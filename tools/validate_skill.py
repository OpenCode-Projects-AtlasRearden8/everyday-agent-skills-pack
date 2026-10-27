#!/usr/bin/env python3
"""Validate agent skill folders offline.

A "skill" is a folder whose name matches the skill, containing a SKILL.md
file with a YAML frontmatter block. This script lints folders you point it
at and reports problems as ERRORs (the skill is broken) or WARNs (worth a
look, not necessarily broken).

Usage:
    python tools/validate_skill.py <folder>            # one skill folder
    python tools/validate_skill.py <folder-a> <b> ...  # several skills
    python tools/validate_skill.py skills/             # a collection folder
    python tools/validate_skill.py --strict skills/    # warnings fail too

Exit code 0 means everything passed; 1 means at least one folder failed
(or --strict turned a warning into a failure).

Only standard-library code is used, so this runs offline with no
third-party packages installed.

The frontmatter parser understands a friendly subset of YAML: comments,
scalars (strings, booleans, numbers, null), quoted strings, block lists,
inline lists, and one level of nested mappings (enough for `metadata:`).
It is intentionally simpler than a full YAML parser; anything it cannot
parse is reported as a yaml-error rather than guessed at.

Finding codes emitted by this module (handy when reading test output):

    check-folder, big-skmd, missing-skmd, missing-frontmatter,
    frontmatter-unclosed, yaml-error, duplicate-key, name-not-slug,
    name-too-long, name-mismatch, name-missing, description-missing,
    description-empty, description-too-long, description-first-person,
    body-empty, body-too-long, unknown-key, allowed-tools-format,
    metadata-not-map, metadata-version, missing-file, secret-found,
    privacy-email
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

__all__ = [
    "Finding",
    "ValidationResult",
    "parse_frontmatter",
    "validate_skill_directory",
    "resolve_skill_paths",
    "run_cli",
    "main",
]

ERROR = "ERROR"
WARN = "WARN"

DEFAULT_MAX_DESCRIPTION = 1024
DEFAULT_MAX_BODY_LINES = 500
DEFAULT_MAX_SKMD_BYTES = 1_000_000

NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
TOOL_NAME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_-]*(\(.*\))?$")
KNOWN_FRONTMATTER_KEYS = {"name", "description", "license", "allowed-tools", "metadata"}
REF_PATH_RE = re.compile(r"\b(?:scripts|references|assets)/[A-Za-z0-9][A-Za-z0-9_./-]*")
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}")

SECRET_PATTERNS = (
    ("aws-access-key", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("github-token", re.compile(r"\b(?:gh[psou]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{22,})\b")),
    ("openai-style-key", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b")),
    ("google-api-key", re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b")),
    ("private-key-block", re.compile(r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----")),
    ("slack-token", re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}\b")),
    ("npm-token", re.compile(r"\bnpm_[A-Za-z0-9]{36}\b")),
    (
        "password-assignment",
        re.compile(
            r"(?i)\b(?:api[_-]?key|secret[_-]?key|password|passwd|auth[_-]?token)\b"
            r"\s*[:=]\s*['\"]?[A-Za-z0-9_\-+/<>$!%*#?]{16,}"
        ),
    ),
    ("bearer-token", re.compile(r"(?i)\bbearer\s+[A-Za-z0-9_\-\.=+/]{30,}")),
)

SCAN_EXTENSIONS = {".md", ".txt", ".py", ".sh", ".yml", ".yaml", ".json", ".toml", ".rst"}


@dataclass(frozen=True)
class Finding:
    """One lint result: its level (ERROR/WARN), a short code, and words."""

    level: str
    code: str
    message: str
    detail: str | None = None

    def render(self, indent: str = "  ") -> str:
        line = f"{indent}{self.level} [{self.code}] {self.message}"
        if self.detail:
            line += f"\n{indent}{indent}{self.detail}"
        return line


@dataclass
class ValidationResult:
    """Everything the validator noticed about one skill folder."""

    path: str
    findings: list[Finding] = field(default_factory=list)

    @property
    def errors(self) -> list[Finding]:
        return [f for f in self.findings if f.level == ERROR]

    @property
    def warnings(self) -> list[Finding]:
        return [f for f in self.findings if f.level == WARN]

    @property
    def ok(self) -> bool:
        return not self.errors

    @property
    def strict_ok(self) -> bool:
        return not self.findings


def warn(result: ValidationResult, code: str, message: str, detail: str | None = None) -> None:
    result.findings.append(Finding(WARN, code, message, detail))


def fail(result: ValidationResult, code: str, message: str, detail: str | None = None) -> None:
    result.findings.append(Finding(ERROR, code, message, detail))


# --------------------------------------------------------------------------
# A friendly YAML subset parser (frontmatter only needs a small heart)
# --------------------------------------------------------------------------

_KEYVAL_RE = re.compile(r"^(?P<key>[^ \t#][^:]*?):(?P<val>.*)$")
_QUOTED_RE = re.compile(r"^(?P<quote>['\"])(?P<body>.*)(?P=quote)$", re.DOTALL)


def _scalar(token: str):
    """Turn a token like `true`, `1.5`, or 'hello' into a Python value."""
    token = token.strip()
    if token == "":
        return ""
    quoted = _QUOTED_RE.match(token)
    if quoted:
        body = quoted.group("body")
        if quoted.group("quote") == "'":
            return body.replace("''", "'")
        return body
    low = token.lower()
    if low in ("true", "yes", "on"):
        return True
    if low in ("false", "no", "off"):
        return False
    if low in ("null", "~"):
        return None
    try:
        return int(token)
    except ValueError:
        pass
    try:
        return float(token)
    except ValueError:
        pass
    return token


def _strip_inline_comment(value: str) -> str:
    """Drop a trailing ' # comment' unless the value starts with a quote."""
    if value.lstrip()[:1] in ('"', "'"):
        return value
    if " #" in value:
        return value.split(" #", 1)[0].rstrip()
    return value


def _split_inline_list(value: str) -> list:
    inner = value.strip()[1:-1]
    if not inner.strip():
        return []
    return [_scalar(part) for part in inner.split(",") if part.strip() != ""]


def _is_noise(line: str) -> bool:
    stripped = line.strip()
    return stripped == "" or stripped.startswith("#")


def _measure(line: str) -> tuple[int, str]:
    indent = len(line) - len(line.lstrip(" "))
    return indent, line.strip()


def _parse_list(lines: list[str], start: int, item_indent: int):
    """Parse '- item' lines starting at `start`; items share one indent."""
    items: list = []
    findings: list[Finding] = []
    i = start
    while i < len(lines):
        if _is_noise(lines[i]):
            i += 1
            continue
        if lines[i][:1] == "\t":
            findings.append(Finding(ERROR, "yaml-error", "tab indentation is not allowed in frontmatter"))
            i += 1
            continue
        indent, content = _measure(lines[i])
        if indent > item_indent:
            findings.append(Finding(ERROR, "yaml-error", f"unexpected indentation in list: {content!r}"))
            i += 1
            continue
        if indent < item_indent or not (content.startswith("- ") or content == "-"):
            break
        value = content[2:].strip() if content.startswith("- ") else ""
        items.append(_scalar(_strip_inline_comment(value)))
        i += 1
    return items, i, findings


def _parse_mapping(lines: list[str], base_indent: int):
    """Parse a mapping block whose keys sit at `base_indent`.

    Handles scalars, quoted strings, inline lists, block lists (one level
    of items), and nested mappings via recursion. Stops at the first line
    that is indented less than `base_indent` (the caller resumes there).
    """
    result: dict = {}
    findings: list[Finding] = []
    i = 0
    while i < len(lines):
        if _is_noise(lines[i]):
            i += 1
            continue
        if lines[i][:1] == "\t":
            findings.append(Finding(ERROR, "yaml-error", "tab indentation is not allowed in frontmatter"))
            i += 1
            continue
        indent, content = _measure(lines[i])
        if indent < base_indent:
            break
        if indent > base_indent:
            findings.append(Finding(ERROR, "yaml-error", f"unexpected indentation: {content!r}"))
            i += 1
            continue

        keyval = _KEYVAL_RE.match(content)
        if keyval is None:
            if content.startswith("- ") or content == "-":
                findings.append(Finding(ERROR, "yaml-error", f"list item without a key above it: {content!r}"))
            else:
                findings.append(Finding(ERROR, "yaml-error", f"could not parse line: {content!r}"))
            i += 1
            continue

        key = keyval.group("key").strip()
        if key in result:
            findings.append(Finding(ERROR, "duplicate-key", f"key {key!r} appears more than once"))
        raw = _strip_inline_comment(keyval.group("val")).strip()

        if raw != "":
            if raw.startswith("[") and raw.endswith("]"):
                result[key] = _split_inline_list(raw)
            else:
                result[key] = _scalar(raw)
            i += 1
            continue

        # `key:` with nothing after it - the value is a list, a nested map,
        # or nothing at all. Peek at the next significant line to decide.
        peek = i + 1
        while peek < len(lines) and _is_noise(lines[peek]):
            peek += 1
        if peek >= len(lines):
            result[key] = None
            i = peek
            continue
        indent_next, content_next = _measure(lines[peek])
        if content_next.startswith("- ") or content_next == "-":
            items, stop, list_findings = _parse_list(lines, peek, indent_next)
            findings.extend(list_findings)
            result[key] = items
            i = stop
            continue
        if indent_next > indent:
            nested, nested_stop, nested_findings = _parse_mapping(lines[peek:], indent_next)
            findings.extend(nested_findings)
            result[key] = nested
            i = peek + nested_stop  # nested parser stopped before this line
            continue
        result[key] = None
        i += 1
    return result, i, findings


def parse_frontmatter(text: str) -> tuple[dict, list[Finding]]:
    """Extract and parse the frontmatter block of a SKILL.md document.

    Returns (data, findings). Structural problems (no block, unclosed
    block, parse errors) come back as ERROR-level findings.
    """
    lines = text.split("\n")
    first = -1
    for index, line in enumerate(lines):
        if line.strip():
            first = index
            break
    if first == -1 or lines[first].strip() != "---":
        return {}, [Finding(ERROR, "missing-frontmatter", "SKILL.md has no frontmatter block (no leading ---)")]
    closing = None
    for index in range(first + 1, len(lines)):
        if lines[index].strip() == "---":
            closing = index
            break
    if closing is None:
        return {}, [Finding(ERROR, "frontmatter-unclosed", "frontmatter is never closed with a second ---")]

    block = lines[first + 1 : closing]
    data, _, findings = _parse_mapping(block, 0)
    return data, findings


def parse_skill_document(text: str) -> tuple[dict, str, list[Finding]]:
    """Split a SKILL.md into (frontmatter data, body text, findings)."""
    data, findings = parse_frontmatter(text)
    if "missing-frontmatter" not in {f.code for f in findings} and "frontmatter-unclosed" not in {
        f.code for f in findings
    }:
        lines = text.split("\n")
        start = 0
        while start < len(lines) and not lines[start].strip():
            start += 1
        end = start + 1
        while end < len(lines) and lines[end].strip() != "---":
            end += 1
        body = "\n".join(lines[end + 1 :])
        return data, body, findings
    return data, text, findings


# --------------------------------------------------------------------------
# The actual lint checks
# --------------------------------------------------------------------------


def validate_skill_directory(path: Path, strict: bool = False) -> ValidationResult:
    """Validate one skill folder. See the module docstring for the rules."""
    result = ValidationResult(path=str(path))

    if not path.is_dir():
        fail(result, "check-folder", f"path is not a folder: {path}")
        return finalize(result, strict)

    skill_md = path / "SKILL.md"
    if not skill_md.is_file():
        fail(result, "missing-skmd", f"no SKILL.md found at the top of {path}")
        return finalize(result, strict)

    text = skill_md.read_text(encoding="utf-8", errors="replace")
    if len(text) > DEFAULT_MAX_SKMD_BYTES:
        warn(result, "big-skmd", f"SKILL.md is very large ({len(text):,} bytes)")

    folder_name = path.name
    if not NAME_RE.match(folder_name):
        fail(
            result,
            "name-not-slug",
            "folder name must be a lowercase hyphenated slug",
            f"folder name: {folder_name!r}",
        )

    data, body, fm_findings = parse_skill_document(text)
    for finding in fm_findings:
        (fail if finding.level == ERROR else warn)(result, finding.code, finding.message, finding.detail)

    # --- name ---------------------------------------------------------------
    if "name" not in data:
        fail(result, "name-missing", "frontmatter is missing the required 'name' field")
    elif not isinstance(data["name"], str):
        fail(result, "name-not-slug", f"'name' must be a string, got {type(data['name']).__name__}")
    else:
        name = data["name"]
        if not NAME_RE.match(name):
            fail(
                result,
                "name-not-slug",
                f"name {name!r} is not a valid slug",
                "allowed: lowercase letters and digits joined by single hyphens, like doc-finder",
            )
        if len(name) > 64:
            fail(result, "name-too-long", f"name is {len(name)} characters (max 64)")
        if NAME_RE.match(name) and name != folder_name:
            fail(
                result,
                "name-mismatch",
                f"frontmatter name {name!r} does not match folder name {folder_name!r}",
            )

    # --- description ----------------------------------------------------------
    if "description" not in data:
        fail(result, "description-missing", "frontmatter is missing the required 'description' field")
    elif data["description"] is None:
        fail(result, "description-empty", "'description' is present but empty (null)")
    elif not isinstance(data["description"], str):
        fail(result, "description-missing", f"'description' must be a string, got {type(data['description']).__name__}")
    else:
        description = data["description"].strip()
        if description == "":
            fail(result, "description-empty", "'description' is present but empty")
        else:
            if len(description) > DEFAULT_MAX_DESCRIPTION:
                fail(
                    result,
                    "description-too-long",
                    f"description is {len(description)} characters (max {DEFAULT_MAX_DESCRIPTION})",
                )
            if re.search(r"\bI\b|\bmy\b|\bmine\b", description):
                warn(
                    result,
                    "description-first-person",
                    "descriptions read best in the third person",
                    "instead of 'I find docs...' write 'Finds docs...'",
                )

    # --- body -------------------------------------------------------------------
    if body.strip() == "":
        fail(result, "body-empty", "SKILL.md has no instructions after the frontmatter")
    else:
        body_lines = [line for line in body.split("\n") if line.strip()]
        if len(body_lines) > DEFAULT_MAX_BODY_LINES:
            warn(
                result,
                "body-too-long",
                f"SKILL.md body is {len(body_lines)} lines (suggested max {DEFAULT_MAX_BODY_LINES})",
                "move long detail into references/ and keep the core instructions lean",
            )

    # --- allowed-tools -------------------------------------------------------------
    if "allowed-tools" in data:
        allowed = data["allowed-tools"]
        entries: list = []
        if isinstance(allowed, str):
            entries = [part.strip() for part in allowed.split(",") if part.strip()]
        elif isinstance(allowed, list):
            entries = allowed
        else:
            fail(
                result,
                "allowed-tools-format",
                "'allowed-tools' must be a comma-separated string or a list",
                f"got {type(allowed).__name__}: {allowed!r}",
            )
        bad = [e for e in entries if not (isinstance(e, str) and TOOL_NAME_RE.match(e.strip()))]
        if bad:
            fail(
                result,
                "allowed-tools-format",
                "some tool names do not look like tool identifiers",
                "offending: " + ", ".join(repr(b) for b in bad),
            )

    # --- metadata --------------------------------------------------------------------
    if "metadata" in data and data["metadata"] is not None:
        if not isinstance(data["metadata"], dict):
            fail(
                result,
                "metadata-not-map",
                "'metadata' must be a mapping with keys like version",
                f"got {type(data['metadata']).__name__}: {data['metadata']!r}",
            )
        else:
            version = data["metadata"].get("version")
            if version is not None and not (isinstance(version, str) and re.match(r"^\d+(\.\d+){0,2}$", version)):
                warn(
                    result,
                    "metadata-version",
                    "metadata.version should look like a version number",
                    f"got {version!r} (example: '1.0.0')",
                )

    # --- unknown keys ------------------------------------------------------------------
    unknown = sorted(set(data.keys()) - KNOWN_FRONTMATTER_KEYS)
    if unknown:
        warn(
            result,
            "unknown-key",
            "unknown frontmatter key(s): " + ", ".join(unknown),
            "known keys: " + ", ".join(sorted(KNOWN_FRONTMATTER_KEYS)),
        )

    # --- files the SKILL.md mentions ------------------------------------------------------
    referenced = sorted(set(REF_PATH_RE.findall(body)))
    missing = [ref for ref in referenced if not ref.endswith(("/", ".")) and not (path / ref).exists()]
    if missing:
        warn(
            result,
            "missing-file",
            "SKILL.md mentions file(s) that do not exist inside the skill folder",
            "\n".join(missing),
        )

    # --- secret scan + privacy sweep ------------------------------------------------------
    for file_path, lineno, line in iter_scannable_lines(path):
        for secret_name, pattern in SECRET_PATTERNS:
            if pattern.search(line):
                fail(
                    result,
                    "secret-found",
                    f"possible secret pattern '{secret_name}'",
                    f"{relative_to_root(file_path, path)}:{lineno}",
                )
        email = EMAIL_RE.search(line)
        if email:
            warn(
                result,
                "privacy-email",
                "possible personal data: looks like an email address",
                f"{relative_to_root(file_path, path)}:{lineno}",
            )

    return finalize(result, strict)


def finalize(result: ValidationResult, strict: bool) -> ValidationResult:
    # Unique findings, in first-seen order.
    seen = set()
    unique = []
    for finding in result.findings:
        key = (finding.level, finding.code, finding.message, finding.detail)
        if key in seen:
            continue
        seen.add(key)
        unique.append(finding)
    if strict and result.warnings:
        unique.extend(Finding(ERROR, f.code, f"strict mode: {f.message}", f.detail) for f in result.warnings)
    result.findings = unique
    return result


def relative_to_root(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:  # already relative or outside the root
        return str(path)


def iter_scannable_lines(root: Path):
    """Yield (path, lineno, line) for text files inside a skill folder."""
    for file_path in sorted(root.rglob("*")):
        if not file_path.is_file():
            continue
        parts = file_path.relative_to(root).parts
        if any(part.startswith(".") or part == "__pycache__" for part in parts[:-1]) or file_path.name.startswith("."):
            continue
        if file_path.suffix not in SCAN_EXTENSIONS:
            continue
        try:
            with file_path.open(encoding="utf-8", errors="replace") as handle:
                for lineno, line in enumerate(handle, start=1):
                    yield file_path, lineno, line.rstrip("\n")
        except OSError:
            continue


# --------------------------------------------------------------------------
# Collections and the command line
# --------------------------------------------------------------------------


def resolve_skill_paths(paths: list[Path]) -> tuple[list[tuple[str, Path]], list[Finding]]:
    """Expand arguments into (label, skill folder) pairs.

    An argument containing a SKILL.md is treated as one skill; any other
    folder is treated as a collection whose immediate subfolders each hold
    a skill. Bad arguments produce ERROR findings instead.
    """
    pairs: list[tuple[str, Path]] = []
    findings: list[Finding] = []
    for arg in paths:
        if not arg.exists():
            findings.append(Finding(ERROR, "check-folder", f"path does not exist: {arg}"))
            continue
        if (arg / "SKILL.md").is_file():
            pairs.append((arg.name, arg))
            continue
        if arg.is_dir():
            children = sorted(p for p in arg.iterdir() if p.is_dir() and (p / "SKILL.md").is_file())
            if children:
                pairs.extend((child.name, child) for child in children)
                continue
            findings.append(Finding(ERROR, "check-folder", f"no skill folders found in {arg}"))
            continue
        findings.append(Finding(ERROR, "check-folder", f"{arg} is not a folder and has no SKILL.md"))
    return pairs, findings


def run_cli(argv: list[str] | None = None, out=None, err=None) -> int:
    """CLI entry point; returns the process exit code (0 pass, 1 fail)."""
    out = out or sys.stdout
    parser = argparse.ArgumentParser(
        prog="validate_skill.py",
        description="Lint agent skill folders (offline, standard library only).",
    )
    parser.add_argument("paths", nargs="+", help="skill folder(s), or a folder containing skill folders")
    parser.add_argument("--strict", action="store_true", help="treat warnings as failures")
    args = parser.parse_args(argv)

    pairs, structural = resolve_skill_paths([Path(p) for p in args.paths])
    results = [validate_skill_directory(path, strict=args.strict) for _, path in pairs]

    invalid = len(structural)
    for finding in structural:
        print(finding.render(), file=out)
    for result in results:
        print(result.path, file=out)
        if not result.findings:
            print("  OK - no problems found", file=out)
        elif result.errors:
            invalid += 1
            for finding in result.findings:
                print(finding.render(), file=out)
        else:
            for finding in result.findings:
                print(finding.render(), file=out)
        print(file=out)

    total = len(structural) + len(results)
    if invalid == 0 and total > 0:
        summary = "all valid"
    elif total == 0:
        summary = "no skills checked"
    else:
        summary = f"{invalid} of {total} invalid"
    print(f"{total} folder(s) checked - {summary}", file=out)
    return 0 if invalid == 0 else 1


def main(argv: list[str] | None = None) -> int:
    return run_cli(argv)


if __name__ == "__main__":
    sys.exit(main())
