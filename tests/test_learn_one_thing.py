"""Tests for the learn-one-thing skill."""

from __future__ import annotations

import json

from validate_skill import validate_skill_directory

from conftest import SKILLS

SCRIPT = "scope_one_thing.py"


def _write(tmp_path, spec) -> str:
    location = tmp_path / "goal.json"
    location.write_text(json.dumps(spec), encoding="utf-8")
    return str(location)


def test_skill_passes_strict_validation():
    result = validate_skill_directory(SKILLS / "learn-one-thing", strict=True)
    assert result.ok, "\n".join(f.render() for f in result.findings)
    assert result.findings == []


def test_bare_subject_rejected_with_slices(run_script, tmp_path):
    completed = run_script("learn-one-thing", SCRIPT, _write(tmp_path, {"goal": "Learn Python"}))
    assert completed.returncode == 0, completed.stderr
    text = completed.stdout
    assert "too broad for one day" in text
    assert "Print today's date with Python in one short file" in text
    assert "done-line" in text


def test_broad_markers_caught(run_script, tmp_path):
    for goal in ("Learn everything about spreadsheets", "Master chess", "Understand AI from scratch to career"):
        completed = run_script("learn-one-thing", SCRIPT, _write(tmp_path, {"goal": goal}))
        assert completed.returncode == 0, goal
        assert "too broad for one day" in completed.stdout, goal


def test_concrete_goal_gets_a_four_step_plan(run_script, tmp_path):
    spec = {"goal": "Python: print the current date to the terminal", "minutes": 20, "who": "beginner"}
    completed = run_script("learn-one-thing", SCRIPT, _write(tmp_path, spec))
    assert completed.returncode == 0, completed.stderr
    text = completed.stdout
    assert "this fits today" in text
    for step in ("Skim", "Do", "Break", "Tell"):
        assert step in text
    assert "Where it fits" in text
    assert step_minutes_sum(text) == 20


def step_minutes_sum(text: str) -> int:
    import re

    return sum(int(match) for match in re.findall(r"\((\d+) min\)", text.split("The plan:")[1].split("Where it fits")[0]))


def test_longer_goal_with_details_is_not_broad(run_script, tmp_path):
    goal = "Read one doc page and change one regex until it matches my receipt dates"
    completed = run_script("learn-one-thing", SCRIPT, _write(tmp_path, {"goal": goal, "minutes": 15}))
    assert completed.returncode == 0
    assert "this fits today" in completed.stdout


def test_too_few_minutes_says_so(run_script, tmp_path):
    spec = {"goal": "change one regex until it matches my receipt dates", "minutes": 5}
    completed = run_script("learn-one-thing", SCRIPT, _write(tmp_path, spec))
    assert completed.returncode == 0
    assert "not enough minutes yet" in completed.stdout


def test_subject_slices_differ_by_subject(run_script, tmp_path):
    outputs = {}
    for subject in ("Learn chess", "Learn Spanish", "Learn cooking"):
        completed = run_script("learn-one-thing", SCRIPT, _write(tmp_path, {"goal": subject}))
        outputs[subject] = completed.stdout
        assert "too broad for one day" in completed.stdout
    assert outputs["Learn chess"] != outputs["Learn Spanish"]
    assert "endgame" in outputs["Learn chess"]


def test_bad_inputs_fail_friendly(run_script, tmp_path):
    bad_specs = [
        {},
        {"goal": ""},
        {"goal": 3},
        {"goal": "Print today's date with Python", "minutes": 0},
        {"goal": "Print today's date with Python", "minutes": -3},
        {"goal": "Print today's date with Python", "minutes": "many"},
        {"goal": "Print today's date with Python", "who": "   "},
        {"goal": "Print today's date with Python", "extra": True},
    ]
    for spec in bad_specs:
        completed = run_script("learn-one-thing", SCRIPT, _write(tmp_path, spec))
        assert completed.returncode == 1, spec
        assert "learn-one-thing:" in completed.stderr


def test_json_result_has_honest_verdicts(run_script, tmp_path):
    completed = run_script("learn-one-thing", SCRIPT, _write(tmp_path, {"goal": "Master Python"}), "--json")
    assert completed.returncode == 0
    result = json.loads(completed.stdout)
    assert result["verdict"] == "too broad for one day"
    assert result["plan"] is None
    assert len(result["slices"]) == 3
    completed = run_script(
        "learn-one-thing", SCRIPT,
        _write(tmp_path, {"goal": "Python: print the current date to the terminal", "minutes": 20}),
        "--json",
    )
    result = json.loads(completed.stdout)
    assert result["verdict"] == "fits today"
    assert len(result["plan"]["steps"]) == 4
