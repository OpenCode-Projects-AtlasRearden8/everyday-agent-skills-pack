#!/usr/bin/env python3
"""Build a one-page appointment brief from a visit description.

Reads a JSON file (see assets/visit-input.md) and prints a brief with
the visit facts, a bring list, questions to ask, wanted outcomes, and an
honest "still need you to find this" list. Nothing is invented; missing
facts are surfaced, not filled in. Standard library only; works offline.

Usage:
    python make_visit_brief.py visit.json
    python make_visit_brief.py visit.json --json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

__all__ = ["BriefError", "build_brief", "render_brief", "main"]

STRING_LIST_FIELDS = ("questions_to_ask", "cant_miss_bring", "outcomes_wanted")
CORE_FACT_FIELDS = ("what", "where", "when")


class BriefError(Exception):
    """A problem with the input the user should hear about plainly."""


def _as_optional_text(entry: dict, field: str) -> str | None:
    value = entry.get(field)
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise BriefError(f"{field!r} must be a non-empty string if present")
    return value.strip()


def build_brief(spec: dict) -> dict:
    """Return a brief dict: known facts, lists, and gaps to fill."""
    if not isinstance(spec, dict):
        raise BriefError("the JSON top level must be an object")
    unknown = sorted(set(spec) - set(CORE_FACT_FIELDS) - set(STRING_LIST_FIELDS)
                     - {"arrive_early_minutes", "who_comes_along", "if_no_show_call"})
    if unknown:
        raise BriefError("unrecognized field(s): " + ", ".join(unknown) +
                         " (accepted fields are listed in assets/visit-input.md)")

    facts = {field: _as_optional_text(spec, field) for field in CORE_FACT_FIELDS}

    who = _as_optional_text(spec, "who_comes_along")
    call = _as_optional_text(spec, "if_no_show_call")
    early = spec.get("arrive_early_minutes")
    if early is not None:
        if isinstance(early, bool) or not isinstance(early, (int, float)) or early < 0:
            raise BriefError("arrive_early_minutes must be a number of minutes")

    lists: dict[str, list[str]] = {}
    for field in STRING_LIST_FIELDS:
        value = spec.get(field, [])
        if value is None:
            value = []
        if not isinstance(value, list) or any(not isinstance(v, str) or not v.strip() for v in value):
            raise BriefError(f"{field!r} must be a list of non-empty strings")
        cleaned = [v.strip() for v in value]
        if len(set(cleaned)) != len(cleaned):
            raise BriefError(f"{field!r} has duplicate entries")
        lists[field] = cleaned

    missing_core = [name for name, value in facts.items() if value is None]
    return {
        "facts": facts,
        "who_comes_along": who,
        "arrive_early_minutes": early,
        "if_no_show_call": call,
        "questions_to_ask": lists["questions_to_ask"],
        "cant_miss_bring": lists["cant_miss_bring"],
        "outcomes_wanted": lists["outcomes_wanted"],
        "still_need": missing_core,
        "advice": (not lists["questions_to_ask"]),
    }


def render_brief(brief: dict) -> str:
    lines: list[str] = []
    label = brief["facts"].get("what") or "Appointment"
    lines.append(f"Visit brief: {label}")
    lines.append("")

    lines.append("## The visit")
    lines.append(f"- What: {brief['facts']['what'] or '(to be written in)'}")
    lines.append(f"- Where: {brief['facts']['where'] or '(to be written in)'}")
    lines.append(f"- When: {brief['facts']['when'] or '(to be written in)'}")
    if brief["arrive_early_minutes"]:
        lines.append(f"- Plan to arrive {brief['arrive_early_minutes']:g} minutes early")
    if brief["who_comes_along"]:
        lines.append(f"- Coming along: {brief['who_comes_along']}")
    if brief["if_no_show_call"]:
        lines.append(f"- If you cannot make it, call: {brief['if_no_show_call']}")
    lines.append("")

    lines.append("## Bring")
    if brief["cant_miss_bring"]:
        for item in brief["cant_miss_bring"]:
            lines.append(f"- [ ] {item}")
    else:
        lines.append("- [ ] Whatever the visit's own checklist says - confirm by phone if unsure")
    lines.append("")

    lines.append("## Ask")
    if brief["questions_to_ask"]:
        for index, question in enumerate(brief["questions_to_ask"], start=1):
            lines.append(f"{index}. {question}")
    else:
        lines.append("(no questions yet - bring one; a visit without a question wanders)")
    lines.append("")

    lines.append("## Want to leave with")
    if brief["outcomes_wanted"]:
        for outcome in brief["outcomes_wanted"]:
            lines.append(f"- [ ] {outcome}")
    else:
        lines.append("- [ ] One next step you did not have before you walked in")
    lines.append("")

    if brief["still_need"] or brief["advice"]:
        lines.append("## Still need you to find this (nothing here was invented)")
        for gap in brief["still_need"]:
            lines.append(f"- Confirm the {gap} of the visit")
        if brief["advice"]:
            lines.append("- At least one question you want an answer to")
        lines.append("")

    lines.append("## Before you go")
    lines.append("Tonight: pack the bag and put it with your keys. Tomorrow at the door: read your questions out loud once.")
    return "\n".join(lines).rstrip() + "\n"


def _load_spec(path: Path) -> dict:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        reason = str(exc) or exc.__class__.__name__
        raise BriefError(f"could not read {path}: {reason}")
    try:
        spec = json.loads(text)
    except json.JSONDecodeError as exc:
        raise BriefError(f"{path} is not valid JSON: {exc.msg} on line {exc.lineno}")
    return spec


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="make_visit_brief.py",
        description="Build a one-page appointment brief (offline, standard library only).",
    )
    parser.add_argument("input", help="path to a JSON visit input file")
    parser.add_argument("--json", action="store_true", help="print the brief as JSON instead of text")
    args = parser.parse_args(argv)

    try:
        spec = _load_spec(Path(args.input))
        brief = build_brief(spec)
    except BriefError as exc:
        print(f"prep-my-appointment: {exc}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(brief, indent=2))
    else:
        sys.stdout.write(render_brief(brief))
    return 0


if __name__ == "__main__":
    sys.exit(main())
