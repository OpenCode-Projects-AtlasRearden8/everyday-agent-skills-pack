"""Tests for the draft-a-kind-letter skill."""

from __future__ import annotations

from validate_skill import validate_skill_directory

from conftest import SKILLS

SCRIPT = "letter_check.py"


def _write(tmp_path, text: str) -> str:
    location = tmp_path / "draft.md"
    location.write_text(text, encoding="utf-8")
    return str(location)


KIND_DRAFT = """Dear Ms. Okorie,

Thank you for taking the time to meet with me on Thursday. I left
excited about the job.

Sincerely,
Dee
"""


def test_skill_passes_strict_validation():
    result = validate_skill_directory(SKILLS / "draft-a-kind-letter", strict=True)
    assert result.ok, "\n".join(f.render() for f in result.findings)
    assert result.findings == []


def test_clean_draft_reads_well_and_exits_zero(run_script, tmp_path):
    completed = run_script("draft-a-kind-letter", SCRIPT, _write(tmp_path, KIND_DRAFT))
    assert completed.returncode == 0, completed.stderr
    assert "reads well" in completed.stdout


def test_all_caps_sentence_found_across_paragraphs(run_script, tmp_path):
    draft = "Dear Sir,\n\nYOU MUST FIX THIS IMMEDIATELY BECAUSE IT IS RUDE.\n\nRegards.\n"
    completed = run_script("draft-a-kind-letter", SCRIPT, _write(tmp_path, draft))
    assert completed.returncode == 1
    returncode_note = completed.stdout
    assert "shouting" in returncode_note
    assert "ERROR" in returncode_note


def test_stiff_phrase_suggested_plain(run_script, tmp_path):
    draft = "Dear Sir,\n\nAs per our conversation, the heater is broken.\n\nRegards.\n"
    completed = run_script("draft-a-kind-letter", SCRIPT, _write(tmp_path, draft))
    assert completed.returncode == 1
    assert "stiff-phrase" in completed.stdout
    assert "consider 'as we discussed'" in completed.stdout


def test_long_sentence_flagged(run_script, tmp_path):
    draft = (
        "Dear Sam,\n\n"
        "I wanted to write briefly today to say that I am sorry about the window and the "
        "noise and the fence rail that came loose during the windstorm last week when the "
        "gusts came through the neighborhood and knocked the trash bins over.\n\nAna\n"
    )
    completed = run_script("draft-a-kind-letter", SCRIPT, _write(tmp_path, draft))
    assert completed.returncode == 1
    assert "long-sentence" in completed.stdout


def test_wall_of_words_detected(run_script, tmp_path):
    wall = "one two three four five " * 30
    draft = f"Note.\n\n{wall.strip()}\n\nEnd.\n"
    completed = run_script("draft-a-kind-letter", SCRIPT, _write(tmp_path, draft))
    assert completed.returncode == 1
    assert "wall-of-words" in completed.stdout


def test_json_report_shape(run_script, tmp_path):
    import json

    draft = "Dear Sir,\n\nPER OUR CONVERSATION YOU MUST FIX THIS IMMEDIATELY THANK YOU VERY MUCH SIR.\n"
    completed = run_script("draft-a-kind-letter", SCRIPT, _write(tmp_path, draft), "--json")
    assert completed.returncode == 1
    report = json.loads(completed.stdout)
    codes = {finding["code"] for finding in report["findings"]}
    assert {"stiff-phrase", "shouting"} <= codes
    assert report["sound"] is False


def test_unreadable_file_reported_cleanly(run_script, tmp_path):
    completed = run_script("draft-a-kind-letter", SCRIPT, str(tmp_path / "ghost.md"))
    assert completed.returncode == 2
    assert "could not read" in completed.stderr
    broken = tmp_path / "x.md"
    broken.write_bytes(b"\xff\xfe\x00")
    completed = run_script("draft-a-kind-letter", SCRIPT, str(broken))
    assert completed.returncode in (0, 1)


def test_examples_and_failure_prompts_cover_the_boundaries():
    examples = (SKILLS / "draft-a-kind-letter" / "references" / "example-output.md").read_text(encoding="utf-8")
    for needed in ("Thank you", "apology", "kind complaint"):
        assert needed.lower() in examples.lower()
    failures = (SKILLS / "draft-a-kind-letter" / "references" / "failure-prompts.md").read_text(encoding="utf-8")
    for needed in ("mean", "lawyer", "grieving"):
        assert needed.lower() in failures.lower()
