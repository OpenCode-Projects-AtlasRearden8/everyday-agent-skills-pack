#!/usr/bin/env python3
"""Audit a folder so an agent can propose a declutter plan without harm.

Walks a folder (offline, standard library only), writes nothing, and
reports: file counts by extension, total size, largest files, oldest
files, empty files, and duplicate-name candidates (same name, any
folder). It never deletes, moves, or renames anything.

Usage:
    python folder_audit.py <folder>
    python folder_audit.py <folder> --json
    python folder_audit.py <folder> --max 30     # cap list lengths
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from collections import defaultdict
from pathlib import Path

__all__ = ["AuditError", "audit_folder", "render_audit", "main"]

SKIP_DIRECTORIES = {
    ".git", ".github", ".venv", "venv", "__pycache__", "node_modules",
    ".pytest_cache", ".mypy_cache", ".ruff_cache", "build", "dist",
}
IGNORE_FILES = {".DS_Store", "Thumbs.db"}


class AuditError(Exception):
    """A problem with the target folder the user should hear about."""


def audit_folder(root: Path, max_per_list: int = 15) -> dict:
    """Return an audit dict. Read-only; never modifies the folder."""
    if not root.exists():
        raise AuditError(f"folder does not exist: {root}")
    if not root.is_dir():
        raise AuditError(f"not a folder: {root} (did you mean a file path?)")

    files: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        relative_parts = path.relative_to(root).parts
        if any(part in SKIP_DIRECTORIES or part.startswith(".") for part in relative_parts):
            continue
        if path.name in IGNORE_FILES or path.name.startswith("."):
            continue
        files.append(path)

    documents = sorted(
        files,
        key=lambda path: (path.parent == root, str(path).lower()),
    )

    by_extension = Counter(
        (path.suffix.lower().lstrip(".") or "no-extension") for path in documents
    )
    total_size = sum(path.stat().st_size for path in documents)

    largest = [
        {"path": _display(path, root), "bytes": path.stat().st_size}
        for path in sorted(documents, key=lambda path: -path.stat().st_size)[:max_per_list]
    ]
    oldest = [
        {"path": _display(path, root), "mtime": path.stat().st_mtime}
        for path in sorted(documents, key=lambda path: path.stat().st_mtime)[:max_per_list]
    ]
    empty = [_display(path, root) for path in documents if path.stat().st_size == 0][:max_per_list]

    name_groups: dict[str, list[Path]] = defaultdict(list)
    for path in documents:
        name_groups[path.name.lower()].append(path)
    duplicate_groups = [
        {"name": name, "copies": [_display(p, root) for p in paths[:max_per_list]]}
        for name, paths in sorted(name_groups.items())
        if len(paths) > 1
    ][:max_per_list]

    return {
        "root": str(root),
        "file_count": len(documents),
        "total_bytes": total_size,
        "by_extension": dict(by_extension.most_common()),
        "largest_files": largest,
        "oldest_files": [
            {"path": entry["path"], "modified": _iso_time(entry["mtime"])} for entry in oldest
        ],
        "empty_files": empty,
        "duplicate_name_groups": duplicate_groups,
        "note": "Read-only audit. Nothing was moved, renamed, or deleted.",
    }


def _display(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def _iso_time(mtime: float) -> str:
    import datetime

    return datetime.datetime.fromtimestamp(
        mtime, tz=datetime.timezone.utc
    ).strftime("%Y-%m-%d")


def render_audit(audit: dict, max_per_list: int = 15) -> str:
    lines: list[str] = []
    lines.append(f"Folder audit: {audit['root']}")
    lines.append(f"Files found: {audit['file_count']} ({_human_bytes(audit['total_bytes'])})")
    lines.append("")
    lines.append("## By extension")
    for extension, count in list(audit["by_extension"].items())[:max_per_list]:
        lines.append(f"- {extension}: {count}")
    lines.append("")
    lines.append("## Largest files (archive-candidates are often here)")
    for entry in audit["largest_files"]:
        lines.append(f"- {entry['path']} ({_human_bytes(entry['bytes'])})")
    lines.append("")
    lines.append("## Oldest files (forgotten, probably safe to archive)")
    for entry in audit["oldest_files"]:
        lines.append(f"- {entry['path']} (modified {entry['modified']})")
    lines.append("")
    if audit["empty_files"]:
        lines.append("## Empty files (safe archive candidates)")
        for path in audit["empty_files"]:
            lines.append(f"- {path}")
        lines.append("")
    if audit["duplicate_name_groups"]:
        lines.append("## Same-named files (compare before merging; the audit shows name only)")
        for group in audit["duplicate_name_groups"]:
            lines.append(f"- {group['name']}")
            for copy in group["copies"]:
                lines.append(f"    {copy}")
        lines.append("")
    lines.append(audit["note"])
    return "\n".join(lines).rstrip() + "\n"


def _human_bytes(size: int) -> str:
    value = float(size)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if value < 1024 or unit == "TB":
            precision = 0 if value >= 10.0 or unit == "B" else 1
            return f"{value:.{precision}f} {unit}"
        value /= 1024
    return f"{size} B"  # pragma: no cover - unreachable


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="folder_audit.py",
        description="Read-only folder audit for declutter planning (offline, standard library only).",
    )
    parser.add_argument("root", help="the folder to audit")
    parser.add_argument("--json", action="store_true", help="print the audit as JSON")
    parser.add_argument("--max", type=int, default=15, help="cap how many entries per list (default 15)")
    args = parser.parse_args(argv)

    try:
        audit = audit_folder(Path(args.root), max_per_list=max(1, args.max))
    except AuditError as exc:
        print(f"declutter-a-folder: {exc}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(audit, indent=2))
    else:
        sys.stdout.write(render_audit(audit, max_per_list=max(1, args.max)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
