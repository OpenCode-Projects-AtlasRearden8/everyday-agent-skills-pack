"""Tests for the untangle-a-bill skill."""

from __future__ import annotations

import json

from validate_skill import validate_skill_directory

from conftest import SKILLS

SCRIPT = "check_bill_math.py"


def _write(tmp_path, spec) -> str:
    location = tmp_path / "bill.json"
    location.write_text(json.dumps(spec), encoding="utf-8")
    return str(location)


def _good_bill() -> dict:
    return {
        "bill_from": "Sunbird Electric",
        "bill_for": "March",
        "printed_total": 148.73,
        "previous_total": 91.02,
        "items": [
            {"label": "Energy charge", "amount": 89.14},
            {"label": "Transmission charge", "amount": 21.20},
            {"label": "Taxes", "amount": 12.19},
            {"label": "Regulatory recovery surcharge", "amount": 26.20},
        ],
    }


def test_skill_passes_strict_validation():
    result = validate_skill_directory(SKILLS / "untangle-a-bill", strict=True)
    assert result.ok, "\n".join(f.render() for f in result.findings)
    assert result.findings == []


def test_matching_math_reported_as_matching(run_script, tmp_path):
    completed = run_script("untangle-a-bill", SCRIPT, _write(tmp_path, _good_bill()))
    assert completed.returncode == 0, completed.stderr
    text = completed.stdout
    assert "Bill breakdown - Sunbird Electric, March" in text
    assert "Sum of items: $148.73" in text
    assert "arithmetic is not it" in text
    assert "$57.71 higher" in text
    assert "Largest item: Energy charge" in text


def test_mismatched_total_is_the_headline_finding(run_script, tmp_path):
    spec = _good_bill()
    spec["printed_total"] = 133.00
    completed = run_script("untangle-a-bill", SCRIPT, _write(tmp_path, spec))
    text = completed.stdout
    assert "does not match the item sum" in text
    assert "$15.73" in text
    assert "first question on the call" in text


def test_duplicates_zeros_negatives_and_round_fees_flagged(run_script, tmp_path):
    spec = {
        "printed_total": 96.00,
        "items": [
            {"label": "Service fee", "amount": 50.00},
            {"label": "Service fee", "amount": 20.00},
            {"label": "Credit adjustment", "amount": -24.00},
            {"label": "Mystery item", "amount": 0},
            {"label": "Round processing fee", "amount": 50.01},
        ],
    }
    completed = run_script("untangle-a-bill", SCRIPT, _write(tmp_path, spec))
    assert completed.returncode == 0
    text = completed.stdout
    assert "Service fee appears more than once" in text
    assert "Mystery item is $0.00" in text
    assert "Negative amount: Credit adjustment (-$24.00)" in text
    assert "Round number: Service fee ($50.00) - a common shape for a fee someone added" in text
    assert "does not match the item sum" in text


def test_no_printed_total_says_so_honestly(run_script, tmp_path):
    spec = {"items": [{"label": "Energy", "amount": 89.14}]}
    completed = run_script("untangle-a-bill", SCRIPT, _write(tmp_path, spec))
    text = completed.stdout
    assert "No printed total was given" in text
    assert "sum could not be checked" in text


def test_bill_higher_than_previous_reported_both_ways(run_script, tmp_path):
    spec = {"printed_total": 50, "previous_total": 80,
            "items": [{"label": "Plan", "amount": 50}]}
    completed = run_script("untangle-a-bill", SCRIPT, _write(tmp_path, spec))
    assert "$30.00 lower" in completed.stdout
    spec = {"printed_total": 50,
            "items": [{"label": "Plan", "amount": 50}]}
    completed = run_script("untangle-a-bill", SCRIPT, _write(tmp_path, spec))
    assert "Compared with last time" not in completed.stdout


def test_bad_inputs_fail_friendly(run_script, tmp_path):
    bad_specs = [
        {"items": []},
        {"items": ["not an object"]},
        {"items": [{"amount": 5}]},
        {"items": [{"label": "X"}]},
        {"items": [{"label": "X", "amount": "high"}]},
        {"items": [{"label": "X", "amount": True}]},
        {"items": [{"label": "X", "amount": 1}], "printed_total": "lots"},
        {"items": [{"label": "X", "amount": 1}], "previous_total": None, "junk": 1},
        {},
    ]
    for spec in bad_specs:
        completed = run_script("untangle-a-bill", SCRIPT, _write(tmp_path, spec))
        assert completed.returncode == 1, spec
        assert "untangle-a-bill:" in completed.stderr


def test_json_output_matches_text_facts(run_script, tmp_path):
    completed = run_script("untangle-a-bill", SCRIPT, _write(tmp_path, _good_bill()), "--json")
    assert completed.returncode == 0
    report = json.loads(completed.stdout)
    assert report["math_ok"] is True
    assert report["item_sum"] == 148.73
    assert report["difference_from_previous"] == 57.71
    assert report["biggest_item"]["label"] == "Energy charge"


def test_boundaries_are_written_down():
    skill = (SKILLS / "untangle-a-bill" / "SKILL.md").read_text(encoding="utf-8")
    assert "Never tell someone they were cheated" in skill or "cheated" in skill
    assert "Never guess billing codes" in skill
