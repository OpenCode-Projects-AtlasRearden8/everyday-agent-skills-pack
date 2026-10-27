"""Tests for the plan-my-week skill: happy paths, failures, and honesty."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from validate_skill import validate_skill_directory

from conftest import SKILLS

SCRIPT = "draft_week_plan.py"


def write_spec(tmp_path: Path, spec) -> str:
    location = tmp_path / "plan.json"
    location.write_text(json.dumps(spec), encoding="utf-8")
    return str(location)


def _spec() -> dict:
    return {
        "week_of": "2026-03-09",
        "days": [
            {"day": "Monday", "capacity_minutes": 60},
            {"day": "Tuesday", "capacity_minutes": 90},
            {"day": "Wednesday", "capacity_minutes": 60},
        ],
        "tasks": [
            {"name": "Pay water bill", "minutes": 15, "energy": "low", "due": "Monday"},
            {"name": "Call pharmacy refill", "minutes": 20, "energy": "high", "due": "Tuesday"},
            {"name": "Draft renter letter", "minutes": 45, "energy": "medium"},
            {"name": "Grocery order", "minutes": 30, "energy": "low"},
            {"name": "Backup photos", "minutes": 90, "energy": "medium"},
        ],
    }


# --------------------------------------------------------------------------
# The skill folder itself


def test_skill_passes_strict_validation():
    result = validate_skill_directory(SKILLS / "plan-my-week", strict=True)
    assert result.ok, "\n".join(f.render() for f in result.findings)
    assert result.findings == []


# --------------------------------------------------------------------------
# Happy path


def test_plan_assigns_due_tasks_and_respects_capacity(run_script, tmp_path):
    completed = run_script("plan-my-week", SCRIPT, write_spec(tmp_path, _spec()))
    assert completed.returncode == 0, completed.stderr
    assert "Pay water bill" in completed.stdout
    assert "Call pharmacy refill" in completed.stdout
    assert "Start here: Pay water bill" in completed.stdout
    monday = completed.stdout.split("## Wednesday")[0].split("## Tuesday")[0]
    assert "Pay water bill" in monday
    assert "Draft renter letter" in monday


def test_plan_marks_open_days(run_script, tmp_path):
    spec = _spec()
    spec["tasks"] = spec["tasks"][:1]
    completed = run_script("plan-my-week", SCRIPT, write_spec(tmp_path, spec))
    assert completed.returncode == 0
    assert "(open day - protected space)" in completed.stdout


def test_plan_moves_unfittable_tasks_to_visible_overflow(run_script, tmp_path):
    spec = _spec()
    spec["days"] = [{"day": "Monday", "capacity_minutes": 30}]
    spec["tasks"] = [{"name": "Backup photos", "minutes": 90, "energy": "medium"}]
    completed = run_script("plan-my-week", SCRIPT, write_spec(tmp_path, spec))
    assert completed.returncode == 0
    assert "## Overflow - did not fit; pick what slips" in completed.stdout
    assert "Backup photos (90 min" in completed.stdout


def test_plan_flags_packed_past_capacity(run_script, tmp_path):
    spec = _spec()
    spec["days"] = [{"day": "Monday", "capacity_minutes": 10}]
    spec["tasks"] = [{"name": "Pay water bill", "minutes": 15, "energy": "low", "due": "Monday"}]
    completed = run_script("plan-my-week", SCRIPT, write_spec(tmp_path, spec))
    assert completed.returncode == 0
    assert "packed past its capacity" in completed.stdout


def test_json_output_is_machine_readable(run_script, tmp_path):
    completed = run_script("plan-my-week", SCRIPT, write_spec(tmp_path, _spec()), "--json")
    assert completed.returncode == 0
    plan = json.loads(completed.stdout)
    assert plan["overflow"] == [{"name": "Backup photos", "minutes": 90, "energy": "medium"}]
    assert [d for d in plan["days"]] == ["Monday", "Tuesday", "Wednesday"]
    assert plan["used"]["Monday"] == 60
    assert [t["name"] for t in plan["assignments"]["Tuesday"]] == ["Call pharmacy refill", "Grocery order"]
    assert plan["assignments"]["Wednesday"] == []


# --------------------------------------------------------------------------
# Failure paths, shaped honestly


def test_plan_reports_friendly_errors(run_script, tmp_path):
    completed = run_script("plan-my-week", SCRIPT, str(tmp_path / "missing-that-never-existed.json"))
    assert completed.returncode == 1
    assert "plan-my-week:" in completed.stderr
    assert "could not read" in completed.stderr

    checks = [
        ('[1, 2]', "top level must be an object"),
        ('{"tasks": "yes"}', "must be a list"),
        ('not json', "valid JSON"),
    ]
    for index, (raw, expected) in enumerate(checks):
        location = tmp_path / f"spec-{index}.json"
        location.write_text(raw, encoding="utf-8")
        completed = run_script("plan-my-week", SCRIPT, str(location))
        assert completed.returncode == 1, (raw, completed.stderr)
        assert "plan-my-week:" in completed.stderr
        assert expected in completed.stderr, completed.stderr


def test_plan_rejects_bad_task_shapes_and_day_names(run_script, tmp_path):
    bad_specs = [
        {"tasks": [{"minutes": 10}]},
        {"tasks": [{"name": "", "minutes": 10}]},
        {"tasks": [{"name": "X", "minutes": 0}]},
        {"tasks": [{"name": "X", "minutes": -5}]},
        {"tasks": [{"name": "X", "minutes": 10, "energy": "furious"}]},
        {"tasks": [{"name": "X", "minutes": 10, "due": "Someday"}]},
        {"tasks": [], "days": "Monday"},
        {"tasks": [], "days": [{"day": "Funday", "capacity_minutes": 10}]},
        {"tasks": [], "days": [{"day": "Monday", "capacity_minutes": -1}]},
        {"tasks": [], "days": [{"day": "Monday"}, {"day": "Monday"}]},
    ]
    for spec in bad_specs:
        completed = run_script("plan-my-week", SCRIPT, write_spec(tmp_path, spec))
        assert completed.returncode == 1, spec
        assert "plan-my-week:" in completed.stderr, spec


def test_due_day_outside_planned_days_is_listed_not_lost(run_script, tmp_path):
    spec = {
        "days": [{"day": "Monday", "capacity_minutes": 120}],
        "tasks": [{"name": "Return library books", "minutes": 20, "due": "Saturday"}],
    }
    completed = run_script("plan-my-week", SCRIPT, write_spec(tmp_path, spec))
    assert completed.returncode == 0
    assert "## Needs a real day" in completed.stdout
    assert "Return library books (due Saturday" in completed.stdout


def test_empty_task_list_still_produces_a_plan(run_script, tmp_path):
    completed = run_script("plan-my-week", SCRIPT, write_spec(tmp_path, {"tasks": []}))
    assert completed.returncode == 0
    assert "open day - protected space" in completed.stdout


def test_spelling_according_to_failure_prompts_is_covered():
    text = (SKILLS / "plan-my-week" / "references" / "failure-prompts.md").read_text(encoding="utf-8")
    for needed in ("overflow", "due date", "3 AM", "private"):
        assert needed.lower() in text.lower()


def test_script_cli_shows_usage_without_argument():
    completed = subprocess.run(
        [sys.executable, str(SKILLS / "plan-my-week" / "scripts" / SCRIPT)],
        capture_output=True,
        text=True,
    )
    assert completed.returncode != 0
    assert "usage" in completed.stderr.lower()
