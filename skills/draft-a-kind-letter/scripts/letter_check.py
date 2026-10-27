#!/usr/bin/env python3
"""A small tone-and-readability check for letter drafts.

Reads a text or markdown draft and reports findings that bear on how the
letter will land: overlong sentences, stiff phrases, shouting, and walls
of words. Findings are advice, not law. Standard library only; offline.

Usage:
    python letter_check.py draft.md
    python letter_check.py draft.md --json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

__all__ = ["LetterCheckError", "check_letter", "findings_to_json", "main"]

WARN = "WARN"
ERROR = "ERROR"

SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+", re.MULTILINE)
WORD_RE = re.compile(r"[A-Za-z0-9'-]+")
SHOUT_RE = re.compile(r"^[A-Z0-9,;:.'\"!? -]{15,}$")

STIFF_PHRASES = {
    "pursuant to": "about",
    "per our conversation": "as we discussed",
    "as per": "as",
    "at your earliest convenience": "when you get a chance",
    "i am writing to inform you": "here is what is happening",
    "please be advised": "a heads-up",
    "heretofore": "so far",
    "kindly do the needful": "please take care of this",
    "it is imperative that": "you have to",
    "in the event that": "if",
    "utilize": "use",
    "endeavor": "try",
    "comestible": "food",
}


class LetterCheckError(Exception):
    """A problem with the input the user should hear about plainly."""


def _split_paragraphs(text: str) -> list[str]:
    paragraphs: list[str] = []
    current: list[str] = []
    for line in text.splitlines():
        if line.strip():
            current.append(line)
        elif current:
            paragraphs.append("\n".join(current))
            current = []
    if current:
        paragraphs.append("\n".join(current))
    return paragraphs


def check_letter(text: str) -> list[dict]:
    """Return findings for a letter draft. Empty list reads comfortable."""
    findings: list[dict] = []

    for paragraph in _split_paragraphs(text):
        words_in_paragraph = len(WORD_RE.findall(paragraph))
        if words_in_paragraph > 120:
            findings.append({
                "level": WARN,
                "code": "wall-of-words",
                "message": f"a paragraph of {words_in_paragraph} words with no break; split it in two",
                "excerpt": paragraph[:120],
            })
        sentences = [s.strip() for s in SENTENCE_SPLIT_RE.split(paragraph) if s.strip()]
        for sentence in sentences:
            word_count = len(WORD_RE.findall(sentence))
            if word_count > 25:
                findings.append({
                    "level": WARN,
                    "code": "long-sentence",
                    "message": f"{word_count} words, this one may lose the reader",
                    "excerpt": sentence[:120],
                })
            low = " ".join(sentence.lower().split())
            for phrase, plainer in STIFF_PHRASES.items():
                if low.find(phrase) != -1:
                    findings.append({
                        "level": WARN,
                        "code": "stiff-phrase",
                        "message": f"consider '{plainer}' instead of '{phrase}'",
                        "excerpt": sentence[:120],
                    })
                    break
            if SHOUT_RE.match(sentence.strip()) and word_count >= 5:
                findings.append({
                    "level": ERROR,
                    "code": "shouting",
                    "message": "this sentence is in full capitals and will read like being yelled at",
                    "excerpt": sentence.strip()[:120],
                })
    return findings


def findings_to_json(findings: list[dict]) -> str:
    return json.dumps({"findings": findings, "sound": not findings}, indent=2)


def render_findings(findings: list[dict]) -> str:
    if not findings:
        return "Letter check: reads well. Short sentences, no stiff phrases, no shouting.\n"
    lines = [f"Letter check: {len(findings)} finding(s)."]
    for finding in findings:
        lines.append(f"- {finding['level']} [{finding['code']}] {finding['message']}")
        lines.append(f"    \"{finding['excerpt']}\"")
    lines.append("")
    lines.append("These are suggestions, not law: keep a finding on purpose if the meaning needs it.")
    return "\n".join(lines) + "\n"


def _load_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        reason = str(exc) or exc.__class__.__name__
        raise LetterCheckError(f"could not read {path}: {reason}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="letter_check.py",
        description="Tone-and-readability check for letter drafts (offline, standard library only).",
    )
    parser.add_argument("input", help="path to a text or markdown letter draft")
    parser.add_argument("--json", action="store_true", help="print findings as JSON")
    args = parser.parse_args(argv)

    try:
        findings = check_letter(_load_text(Path(args.input)))
    except LetterCheckError as exc:
        print(f"draft-a-kind-letter: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(findings_to_json(findings))
    else:
        sys.stdout.write(render_findings(findings))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
