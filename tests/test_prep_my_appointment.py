"""Tests for the prep-my-appointment skill."""

from __future__ import annotations

import json

from validate_skill import validate_skill_directory

from conftest import SKILLS

SCRIPT = "make_visit_brief.py"


def _write(tmp_path, spec) -> str:
    location = tmp_path / "visit.json"
    location.write_text(json.dumps(spec), encoding="utf-8")
    return str(location)


def _full_spec() -> dict:
    return {
        "what": "Yearly blood pressure check",
        "where": "Riverside Family Clinic",
        "when": "Thursday, March 12, 3:00 PM",
        "arrive_early_minutes": 15,
        "cant_miss_bring": ["Photo ID", "Insurance card", "Home readings list"],
        "questions_to_ask": [
            "Is my home reading trend one you would act on?",
            "What side effects of a new medicine should send me back?",
        ],
        "outcomes_wanted": ["A next-check date", "A plain-language note I can read later"],
    }


def test_skill_passes_strict_validation():
    result = validate_skill_directory(SKILLS / "prep-my-appointment", strict=True)
    assert result.ok, "\n".join(f.render() for f in result.findings)
    assert result.findings == []


def test_full_input_brief_with_no_gaps(run_script, tmp_path):
    completed = run_script("prep-my-appointment", SCRIPT, _write(tmp_path, _full_spec()))
    assert completed.returncode == 0, completed.stderr
    text = completed.stdout
    assert "Visit brief: Yearly blood pressure check" in text
    assert "- Where: Riverside Family Clinic" in text
    assert "Plan to arrive 15 minutes early" in text
    assert "- [ ] Photo ID" in text
    assert "1. Is my home reading trend one you would act on?" in text
    assert "read your questions out loud once" in text
    assert "Still need" not in text


def test_incomplete_input_surfaces_gaps_instead_of_inventing(run_script, tmp_path):
    completed = run_script("prep-my-appointment", SCRIPT, _write(tmp_path, {"what": "Dentist"}))
    assert completed.returncode == 0, completed.stderr
    text = completed.stdout
    assert "- Where: (to be written in)" in text
    assert "- When: (to be written in)" in text
    assert "Confirm the where" in text
    assert "Confirm the when" in text
    assert "At least one question you want an answer to" in text


def test_brief_lists_outcomes_and_no_show_line(run_script, tmp_path):
    spec = dict(_full_spec())
    spec["if_no_show_call"] = "the clinic rescheduling line"
    completed = run_script("prep-my-appointment", SCRIPT, _write(tmp_path, spec))
    text = completed.stdout
    assert "- If you cannot make it, call: the clinic rescheduling line" in text
    assert "- [ ] A next-check date" in text


def test_bare_minimum_still_makes_a_brief(run_script, tmp_path):
    completed = run_script("prep-my-appointment", SCRIPT, _write(tmp_path, {"what": "Appointment"}))
    assert completed.returncode == 0
    assert "Visit brief: Appointment" in completed.stdout


def test_bad_inputs_fail_friendly(run_script, tmp_path):
    bad_specs = [
        {"what": 3},
        {"what": "", "where": "Somewhere"},
        {"what": "X", "questions_to_ask": "just one"},
        {"what": "X", "questions_to_ask": ["", "?"]},
        {"what": "A", "questions_to_ask": ["Q", "Q"]},
        {"what": "A", "arrive_early_minutes": -5},
        {"what": "A", "arrive_early_minutes": "fifteen"},
        {"what": "A", "mystery_field": True},
    ]
    for spec in bad_specs:
        completed = run_script("prep-my-appointment", SCRIPT, _write(tmp_path, spec))
        assert completed.returncode == 1, spec
        assert "prep-my-appointment:" in completed.stderr


def test_unreadable_or_broken_json_fails_friendly(run_script, tmp_path):
    location = tmp_path / "visit.json"
    location.write_text("{oops", encoding="utf-8")
    completed = run_script("prep-my-appointment", SCRIPT, str(location))
    assert completed.returncode == 1
    assert "valid JSON" in completed.stderr
    completed = run_script("prep-my-appointment", SCRIPT, str(tmp_path / "no.json"))
    assert completed.returncode == 1
    assert "could not read" in completed.stderr


def test_json_output_is_machine_readable(run_script, tmp_path):
    completed = run_script("prep-my-appointment", SCRIPT, _write(tmp_path, _full_spec()), "--json")
    assert completed.returncode == 0
    brief = json.loads(completed.stdout)
    assert brief["facts"]["where"] == "Riverside Family Clinic"
    assert brief["still_need"] == []
    assert brief["advice"] is False
