#!/usr/bin/env python3
"""Draft a gentle weekly plan from tasks and daily capacities.

Reads a JSON file (see assets/input-format.md) and prints a day-by-day
plan draft. Tasks with a due day land on that day; the rest are placed
largest-first into the first day with room. Anything that does not fit
goes to an honest overflow list. Standard library only; works offline.

Usage:
    python draft_week_plan.py plan-input.json
    python draft_week_plan.py plan-input.json --json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

__all__ = ["PlanError", "build_plan", "render_plan", "main"]

DEFAULT_DAYS = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday")
DEFAULT_CAPACITY = 90
ENERGIES = ("low", "medium", "high")
DAY_NAMES = {
    "monday", "tuesday", "wednesday", "thursday", "friday",
    "saturday", "sunday",
}
DAY_ORDER = {name: index for index, name in enumerate(
    ("monday", "tuesday", "wednesday", "thursday", "friday",
     "saturday", "sunday")
)}


class PlanError(Exception):
    """A problem with the input the user should hear about plainly."""


def _normalize_days(spec: dict) -> list[dict]:
    days = spec.get("days")
    if days is None:
        return [{"day": name, "capacity_minutes": DEFAULT_CAPACITY} for name in DEFAULT_DAYS]
    if not isinstance(days, list) or not days:
        raise PlanError("'days' must be a non-empty list of {day, capacity_minutes} entries")
    normalized = []
    for entry in days:
        if not isinstance(entry, dict) or "day" not in entry:
            raise PlanError("each 'days' entry needs a 'day' name")
        raw_name = entry.get("day")
        if not isinstance(raw_name, str) or raw_name.strip().lower() not in DAY_NAMES:
            raise PlanError(f"unknown day name: {raw_name!r} (use full day names like 'Monday')")
        name = raw_name.strip()
        capacity = entry.get("capacity_minutes", DEFAULT_CAPACITY)
        if isinstance(capacity, bool) or not isinstance(capacity, (int, float)) or capacity < 0:
            raise PlanError(f"capacity_minutes for {name} must be a number of minutes, not {capacity!r}")
        normalized.append({"day": name, "capacity_minutes": capacity})
    seen = {d["day"].lower() for d in normalized}
    if len(seen) != len(normalized):
        raise PlanError("'days' has a repeated day name")
    return normalized


def _normalize_tasks(spec: dict) -> list[dict]:
    tasks = spec.get("tasks")
    if tasks is None:
        raise PlanError("input needs a 'tasks' list (an empty list is fine)")
    if not isinstance(tasks, list):
        raise PlanError("'tasks' must be a list")
    normalized = []
    for index, entry in enumerate(tasks, start=1):
        if not isinstance(entry, dict):
            raise PlanError(f"task {index} is not an object: {entry!r}")
        name = entry.get("name")
        if not isinstance(name, str) or not name.strip():
            raise PlanError(f"task {index} is missing a 'name'")
        minutes = entry.get("minutes")
        if isinstance(minutes, bool) or not isinstance(minutes, (int, float)) or minutes <= 0:
            raise PlanError(f"task {name.strip()!r} needs positive 'minutes', got {minutes!r}")
        task = {"name": name.strip(), "minutes": minutes}
        energy = entry.get("energy", "medium")
        if energy not in ENERGIES:
            raise PlanError(f"task {name.strip()!r}: energy must be one of low, medium, high")
        task["energy"] = energy
        due = entry.get("due")
        if due is not None:
            if not isinstance(due, str) or due.strip().lower() not in DAY_NAMES:
                raise PlanError(f"task {name.strip()!r}: 'due' must be a day name like 'Monday'")
            task["due"] = due.strip()
        normalized.append(task)
    return normalized


def build_plan(spec: dict) -> dict:
    """Return a plan: assignments per day (in calendar order) plus overflow.

    Policies, kept simple and honest:
    - A task with a due day always lands on that day, even if it packs the
      day past capacity; the overload is reported, never hidden.
    - A task whose due day is not in 'days' is listed as skipped, not lost.
    - Free tasks are placed largest-first into the first day with room.
    """
    days = sorted(
        _normalize_days(spec), key=lambda d: DAY_ORDER[d["day"].lower()]
    )
    tasks = _normalize_tasks(spec)
    planned_days = {d["day"].lower() for d in days}
    remaining = {d["day"]: d["capacity_minutes"] for d in days}

    due_tasks = []
    free_tasks = []
    skipped = []
    for task in tasks:
        if "due" in task:
            if task["due"].lower() not in planned_days:
                skipped.append({"name": task["name"], "due": task["due"]})
            else:
                due_tasks.append(task)
        else:
            free_tasks.append(task)

    due_tasks.sort(key=lambda t: (-t["minutes"], t["name"].lower()))
    free_tasks.sort(key=lambda t: (-t["minutes"], t["name"].lower()))

    assignments: dict[str, list[dict]] = {d["day"]: [] for d in days}
    used: dict[str, float] = {d["day"]: 0.0 for d in days}

    for task in due_tasks:
        day = next(d["day"] for d in days if d["day"].lower() == task["due"].lower())
        assignments[day].append(dict(task, landed_because="due"))
        used[day] += task["minutes"]
        remaining[day] -= task["minutes"]

    overflow = []
    for task in free_tasks:
        for d in days:
            if task["minutes"] <= remaining[d["day"]]:
                assignments[d["day"]].append(dict(task, landed_because="fits"))
                remaining[d["day"]] -= task["minutes"]
                used[d["day"]] += task["minutes"]
                break
        else:
            overflow.append(task)

    overloaded = [d["day"] for d in days if used[d["day"]] > d["capacity_minutes"] + 1e-9]
    return {
        "week_of": spec.get("week_of") if isinstance(spec.get("week_of"), str) else "",
        "days": [d["day"] for d in days],
        "capacities": {d["day"]: d["capacity_minutes"] for d in days},
        "used": used,
        "assignments": assignments,
        "overflow": overflow,
        "skipped_unknown_due": skipped,
        "overloaded_days": overloaded,
    }


def render_plan(plan: dict) -> str:
    """Format a plan dict as the friendly text output."""
    lines = []
    header = "Week plan (draft)"
    if plan.get("week_of"):
        header += f" - week of {plan['week_of']}"
    lines.append(header)
    lines.append("")
    for day in plan["days"]:
        capacity = plan["capacities"][day]
        tasks = plan["assignments"][day]
        lines.append(f"## {day} ({capacity:g} min planned)")
        if not tasks:
            lines.append("- (open day - protected space)")
        for task in tasks:
            note = f"{task['minutes']:g} min, {task['energy']} energy"
            if task.get("landed_because") == "due":
                note += ", due this day"
            lines.append(f"- [ ] {task['name']} ({note})")
        smallest = min(tasks, key=lambda t: t["minutes"]) if tasks else None
        if smallest:
            lines.append(f"  -> Start here: {smallest['name']}")
        lines.append("")
    if plan["overflow"]:
        lines.append("## Overflow - did not fit; pick what slips")
        for task in plan["overflow"]:
            lines.append(f"- {task['name']} ({task['minutes']:g} min, {task['energy']} energy)")
        lines.append("")
    if plan["skipped_unknown_due"]:
        lines.append("## Needs a real day")
        for item in plan["skipped_unknown_due"]:
            lines.append(f"- {item['name']} (due {item['due']} - not a planned day; set a date or reschedule)")
        lines.append("")
    for day in plan["overloaded_days"]:
        lines.append(f"! Notice: {day} is packed past its capacity. Move something or raise its capacity honestly.")
    return "\n".join(lines).rstrip() + "\n"


def _load_spec(path: Path) -> dict:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise PlanError(f"could not read {path}: {_take_reason(exc)}")
    try:
        spec = json.loads(text)
    except json.JSONDecodeError as exc:
        raise PlanError(f"{path} is not valid JSON: {exc.msg} on line {exc.lineno}")
    if not isinstance(spec, dict):
        raise PlanError("the JSON top level must be an object like {'tasks': []}")
    return spec


def _take_reason(exc: OSError) -> str:
    text = str(exc)
    return text if text else exc.__class__.__name__


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="draft_week_plan.py",
        description="Draft a gentle weekly plan (offline, standard library only).",
    )
    parser.add_argument("input", help="path to a JSON plan input file")
    parser.add_argument("--json", action="store_true", help="print the plan as JSON instead of text")
    args = parser.parse_args(argv)

    try:
        spec = _load_spec(Path(args.input))
        plan = build_plan(spec)
    except PlanError as exc:
        print(f"plan-my-week: {exc}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(plan, indent=2))
    else:
        sys.stdout.write(render_plan(plan))
    return 0


if __name__ == "__main__":
    sys.exit(main())
