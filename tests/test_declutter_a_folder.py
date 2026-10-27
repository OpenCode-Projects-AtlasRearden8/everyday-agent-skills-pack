"""Tests for the declutter-a-folder skill."""

from __future__ import annotations

from pathlib import Path

from validate_skill import validate_skill_directory

from conftest import SKILLS

SCRIPT = "folder_audit.py"


def make_messy_folder(tmp_path: Path) -> Path:
    root = tmp_path / "Downloads"
    (root / "old").mkdir(parents=True)
    (root / ".hidden").mkdir()
    (root / "receipt-scans-2019.pdf").write_text("receipt", encoding="utf-8")
    (root / "resume.docx").write_text("resume", encoding="utf-8")
    (root / "old" / "resume.docx").write_text("resume-older", encoding="utf-8")
    (root / "big.bin").write_bytes(b"x" * 50_000)
    (root / "empty.txt").write_text("", encoding="utf-8")
    (root / ".hidden" / "secret.txt").write_text("s", encoding="utf-8")
    (root / ".DS_Store").write_text("junk", encoding="utf-8")
    return root


def test_skill_passes_strict_validation():
    result = validate_skill_directory(SKILLS / "declutter-a-folder", strict=True)
    assert result.ok, "\n".join(f.render() for f in result.findings)
    assert result.findings == []


def test_audit_inventories_but_skips_hidden(run_script, tmp_path):
    root = make_messy_folder(tmp_path)
    completed = run_script("declutter-a-folder", SCRIPT, str(root))
    assert completed.returncode == 0, completed.stderr
    text = completed.stdout
    assert "Files found: 5" in text
    assert "49 KB" in text
    assert "- docx: 2" in text
    assert "- pdf: 1" in text
    assert "big.bin (49 KB)" in text
    assert "empty.txt" in text
    for leaked in ("secret", ".hidden", ".DS_Store"):
        assert leaked not in text
    assert "Nothing was moved, renamed, or deleted." in text


def test_duplicates_found_by_name(run_script, tmp_path):
    root = make_messy_folder(tmp_path)
    completed = run_script("declutter-a-folder", SCRIPT, str(root))
    text = completed.stdout
    assert "## Same-named files" in text
    assert "resume.docx" in text
    assert "old/resume.docx" in text


def test_missing_and_non_folders_fail_friendly(run_script, tmp_path):
    completed = run_script("declutter-a-folder", SCRIPT, str(tmp_path / "ghost"))
    assert completed.returncode == 1
    assert "does not exist" in completed.stderr
    file_path = tmp_path / "afile.txt"
    file_path.write_text("hi", encoding="utf-8")
    completed = run_script("declutter-a-folder", SCRIPT, str(file_path))
    assert completed.returncode == 1
    assert "not a folder" in completed.stderr


def test_max_option_caps_lists(run_script, tmp_path):
    root = make_messy_folder(tmp_path)
    completed = run_script("declutter-a-folder", SCRIPT, str(root), "--max", "2")
    assert completed.returncode == 0
    text = completed.stdout
    by_extension = text.split("## Oldest")[0].split("## Largest")[0]
    counted = [line for line in by_extension.splitlines() if line.startswith("- ")]
    assert len(counted) == 2  # four extensions, capped at two


def test_json_audit_shape(run_script, tmp_path):
    root = make_messy_folder(tmp_path)
    completed = run_script("declutter-a-folder", SCRIPT, str(root), "--json")
    assert completed.returncode == 0
    import json

    audit = json.loads(completed.stdout)
    assert audit["file_count"] == 5
    assert audit["total_bytes"] == 50_000 + len("receipt") + len("resume") + len("resume-older")
    assert audit["by_extension"].get("docx") == 2
    assert any(group["name"] == "resume.docx" for group in audit["duplicate_name_groups"])
    assert "empty.txt" in " ".join(audit["empty_files"])
    assert "Nothing was moved" in audit["note"]


def test_audit_writes_nothing(run_script, tmp_path):
    root = make_messy_folder(tmp_path)
    before = sorted((p, p.stat().st_mtime_ns) for p in root.rglob("*") if p.is_file())
    completed = run_script("declutter-a-folder", SCRIPT, str(root))
    assert completed.returncode == 0
    after = sorted((p, p.stat().st_mtime_ns) for p in root.rglob("*") if p.is_file())
    assert before == after
    assert not (root / "_archive").exists()


def test_boundaries_written_in_skill():
    skill = (SKILLS / "declutter-a-folder" / "SKILL.md").read_text(encoding="utf-8")
    assert "never deletes, moves, or renames" in skill
    assert "read-only" in skill.lower() or "read and report" in skill.lower()
