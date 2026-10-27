#!/usr/bin/env python3
"""Shrink a learning goal into one small, finishable thing for today.

Reads a JSON file (see assets/goal-input.md) and prints either a plan -
goal, done-line, four steps with minutes - or, if the goal's scope is a
whole subject rather than a thing, narrower draft slices instead. The
script is deliberately conservative and never promises mastery.
Standard library only; works offline.

Usage:
    python scope_one_thing.py goal.json
    python scope_one_thing.py goal.json --json
"""

from __future__ import annotations

import argparse
import json
import sys
import re
from pathlib import Path

__all__ = ["ScopeError", "scope_one_thing", "render_scope", "main"]

DEFAULT_MINUTES = 20
MIN_PLAN_MINUTES = 9

BROAD_MARKERS = (
    "everything", "all about", "the whole", "completely",
    "master", "career", "from scratch to", "certification", "certified",
    "fully",
)

SUBJECT_KEYWORDS = {
    "python": "python",
    "javascript": "javascript",
    "java": "java",
    "sql": "sql",
    "linux": "linux",
    "git": "git",
    "excel": "spreadsheets",
    "spreadsheet": "spreadsheets",
    "statistics": "statistics",
    "chess": "chess",
    "cooking": "cooking",
    "baking": "cooking",
    "spanish": "language",
    "french": "language",
}

SUBJECT_SLICES = {
    "python": [
        "Print today's date with Python in one short file",
        "Read a small file with Python and count its lines",
        "Fix one bug in a ten-line Python script",
    ],
    "javascript": [
        "Change the text of a button with JavaScript in a small page",
        "Add one event that logs a click with JavaScript",
        "Use Array.map() on three items and log the result",
    ],
    "sql": [
        "Run one SELECT with a WHERE clause on a small table",
        "Sort a small query result with ORDER BY",
        "Join two small tables once and print three rows",
    ],
    "linux": [
        "Navigate a directory tree using only clear and ls",
        "Use grep to find one word in one file",
        "Chain two commands with a pipe",
    ],
    "git": [
        "Make and undo one commit in a practice repository",
        "Revert one change with git checkout",
        "Write a useful commit message for a small change",
    ],
    "spreadsheets": [
        "Add a SUM that totals one small expense column",
        "Use one IF formula on a small list",
        "Add a filter and find the three biggest rows",
    ],
    "statistics": [
        "Compute a mean and a median for seven numbers by hand",
        "Explain to a friend why a median resists outliers",
        "Read one small chart and name the axes out loud",
    ],
    "chess": [
        "Draw one king-and-pawn endgame against a basic bot",
        "Win one must-win endgame with a queen versus a pawn",
        "Name the three stalemate patterns from one lesson",
    ],
    "cooking": [
        "Cook one dish you have done before, faster this time",
        "Season one soup twice and compare the two",
        "Prep for one meal ahead, entirely, start to finish",
    ],
    "language": [
        "Learn ten words for a room you use daily and say them",
        "Read one sentence of a small news item and translate it",
        "Speak two sentences of a full self-introduction out loud",
    ],
}

GENERIC_SLICES = [
    "Find one small open question about {subject} and answer it",
    "Do one tiny thing with {subject} start to finish",
    "Explain {subject}'s one most important idea to a friend in one minute",
]

BROAD_REASONS = ("subject alone", "field-sized phrasing")


class ScopeError(Exception):
    """A problem with the input the user should hear about plainly."""


def _optional_text(spec: dict, field: str) -> str | None:
    value = spec.get(field)
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ScopeError(f"{field!r} must be a non-empty string if present")
    return value.strip()


def _subject_of(goal: str) -> str | None:
    low = goal.lower()
    for keyword, slice_key in SUBJECT_KEYWORDS.items():
        if re.search(rf"\b{re.escape(keyword)}\b", low):
            return slice_key
    return None


def is_too_broad(goal: str) -> tuple[bool, str | None]:
    """Return (too_broad, reason) for a one-goal string."""
    low = goal.lower()
    for marker in BROAD_MARKERS:
        if marker in low:
            return True, f"contains '{marker}', which points at a field, not a thing"
    words = len(low.split())
    if words <= 4 and _subject_of(goal):
        return True, "a bare subject with no concrete thing in it"
    return False, None


def build_slices(goal: str) -> list[str]:
    subject = _subject_of(goal)
    if subject is None:
        return [template.format(subject=subject_text(goal)) for template in GENERIC_SLICES]
    return SUBJECT_SLICES[subject]


def subject_text(goal: str) -> str:
    return goal.strip(" .!")[:60].lower()


def make_plan(goal: str, minutes: int, who: str) -> dict:
    """Return a four-step plan draft for a goal that fits the minutes."""
    skim_minutes = 4 if minutes >= 20 else 2
    tell_minutes = 2 if minutes >= 20 else 1
    do_minutes = max(minutes - skim_minutes - tell_minutes - 2, 1)
    return {
        "goal": goal,
        "minutes": minutes,
        "who": who,
        "steps": [
            {"step": "Skim", "minutes": skim_minutes,
             "do": "Look for the shape of the thing: where does it start, where does it end?"},
            {"step": "Do", "minutes": do_minutes,
             "do": f"Actually do the thing: {goal}"},
            {"step": "Break", "minutes": 2,
             "do": "Name the moment this plan will realistically die and what to do then"},
            {"step": "Tell", "minutes": tell_minutes,
             "do": "Say back out loud what was learned in one sentence"},
        ],
    }


def scope_one_thing(spec: dict) -> dict:
    """Return {verdict, ...} either with a plan or with draft slices."""
    if not isinstance(spec, dict):
        raise ScopeError("the JSON top level must be an object")
    unknown = sorted(set(spec) - {"goal", "minutes", "who"})
    if unknown:
        raise ScopeError("unrecognized field(s): " + ", ".join(unknown) +
                         " (accepted fields are listed in assets/goal-input.md)")
    goal = _optional_text(spec, "goal")
    if goal is None:
        raise ScopeError("input needs a 'goal'")
    minutes = spec.get("minutes", DEFAULT_MINUTES)
    if isinstance(minutes, bool) or not isinstance(minutes, (int, float)) or minutes <= 0:
        raise ScopeError(f"'minutes' must be a positive number, got {minutes!r}")
    minutes = float(minutes)
    who = spec.get("who", "beginner")
    if not isinstance(who, str) or not who.strip():
        raise ScopeError("'who' must be a non-empty string like 'beginner'")
    who = who.strip()

    broad, reason = is_too_broad(goal)
    if broad:
        return {"verdict": "too broad for one day", "reason": reason,
                "goal": goal, "minutes": minutes, "who": who,
                "slices": build_slices(goal), "plan": None}
    if minutes < MIN_PLAN_MINUTES:
        return {"verdict": "not enough minutes yet",
                "reason": f"{minutes:g} minutes is too little for do + skim + tell; come back with ten or more",
                "goal": goal, "minutes": minutes, "who": who,
                "slices": [], "plan": None}
    return {"verdict": "fits today", "reason": None,
            "goal": goal, "minutes": minutes, "who": who,
            "slices": [], "plan": make_plan(goal, minutes, who)}


def render_scope(scope: dict) -> str:
    lines: list[str] = []
    lines.append(f"Goal: {scope['goal']} ({scope['minutes']:g} min, {scope['who']})")
    lines.append("")
    if scope["verdict"] == "too broad for one day":
        lines.append("Verdict: too broad for one day.")
        if scope["reason"]:
            lines.append(f"Reason: {scope['reason']}.")
        lines.append("")
        lines.append("Draft slices - pick one, keep it, edit it to be yours:")
        for index, slice in enumerate(scope["slices"], start=1):
            lines.append(f"{index}. {slice}")
        lines.append("")
        lines.append("Any slice still feels big means it is big; cut it again until the done-line is real.")
    elif scope["verdict"] == "not enough minutes yet":
        lines.append(f"Verdict: not enough minutes yet - {scope['reason']}.")
        lines.append("Either add minutes or keep the goal for a day with real space.")
    else:
        plan = scope["plan"]
        lines.append("Verdict: this fits today.")
        lines.append("")
        done_line = f"- {plan['goal']}"
        lines.append("The one thing:")
        lines.append(done_line)
        lines.append("")
        lines.append("The plan:")
        for index, step in enumerate(plan["steps"], start=1):
            title = f"{index}. {step['step']} ({step['minutes']:g} min)"
            lines.append(title)
            lines.append(f"   {step['do']}")
        lines.append("")
        lines.append("Where it fits: attach this to something that already happens - after lunch, right after opening the laptop, while the kettle is on.")
    return "\n".join(lines).rstrip() + "\n"


def _load_spec(path: Path) -> dict:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        reason = str(exc) or exc.__class__.__name__
        raise ScopeError(f"could not read {path}: {reason}")
    try:
        spec = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ScopeError(f"{path} is not valid JSON: {exc.msg} on line {exc.lineno}")
    return spec


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="scope_one_thing.py",
        description="Shrink one learning goal into a plan for today (offline, standard library only).",
    )
    parser.add_argument("input", help="path to a JSON goal input file")
    parser.add_argument("--json", action="store_true", help="print the scope result as JSON")
    args = parser.parse_args(argv)

    try:
        scope = scope_one_thing(_load_spec(Path(args.input)))
    except ScopeError as exc:
        print(f"learn-one-thing: {exc}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(scope, indent=2))
    else:
        sys.stdout.write(render_scope(scope))
    return 0


if __name__ == "__main__":
    sys.exit(main())
