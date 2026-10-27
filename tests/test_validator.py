"""Tests for the pack validator: the shipped skills and its own rules."""

from __future__ import annotations

from validate_skill import resolve_skill_paths, validate_skill_directory

from conftest import REPO_ROOT

ALL_SKILLS = [
    "declutter-a-folder",
    "draft-a-kind-letter",
    "learn-one-thing",
    "plan-my-week",
    "prep-my-appointment",
    "untangle-a-bill",
]


def test_whole_collection_resolves_and_validates_strictly():
    pairs, structural = resolve_skill_paths([REPO_ROOT / "skills"])
    assert not structural
    assert [label for label, _ in pairs] == ALL_SKILLS
    for _, path in pairs:
        result = validate_skill_directory(path, strict=True)
        assert result.ok, "\n".join(f.render() for f in result.findings)
        assert result.findings == [], path


def test_cli_on_collection_exits_zero_and_names_every_skill(run_validator):
    completed = run_validator("skills/")
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "6 folder(s) checked - all valid" in completed.stdout
    for name in ALL_SKILLS:
        assert name in completed.stdout


def test_cli_strict_on_collection_exits_zero(run_validator):
    completed = run_validator("--strict", "skills/")
    assert completed.returncode == 0, completed.stdout + completed.stderr


def test_cli_on_each_skill_exits_zero(run_validator):
    for name in ALL_SKILLS:
        completed = run_validator(f"skills/{name}")
        assert completed.returncode == 0, (name, completed.stdout, completed.stderr)


# --------------------------------------------------------------------------
# The validator's own behavior on damaged skills


def make_skill(root, name, description="Does a thing. Use when the thing needs doing.",
               body="One: do it. Two: check it.", extra=""):
    folder = root / name
    folder.mkdir(parents=True)
    lines = [f"name: {name}", f"description: {description}"]
    if extra:
        lines.append(extra)
    (folder / "SKILL.md").write_text(
        "---\n" + "\n".join(lines) + "\n---\n" + body, encoding="utf-8"
    )
    return folder


def test_name_mismatch_fails(tmp_path, run_validator):
    folder = make_skill(tmp_path, "one-thing")
    backend = (folder / "SKILL.md").read_text(encoding="utf-8").replace(
        "name: one-thing", "name: two-thing"
    )
    (folder / "SKILL.md").write_text(backend, encoding="utf-8")
    completed = run_validator(str(folder))
    assert completed.returncode == 1
    assert "name-mismatch" in completed.stdout


def test_secret_scan_finds_seams_across_skill_files(tmp_path, run_validator):
    folder = make_skill(tmp_path, "leaky-skill")
    (folder / "references").mkdir()
    (folder / "references" / "config.md").write_text(
        "token: ghp_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\n", encoding="utf-8"
    )
    completed = run_validator(str(folder))
    assert completed.returncode == 1
    assert "secret-found" in completed.stdout


def test_email_privacy_nudge_warns(tmp_path, run_validator):
    folder = make_skill(tmp_path, "emaily-skill",
                        body="Write to the help address for questions.\n")
    skill_md = folder / "SKILL.md"
    skill_md.write_text(
        skill_md.read_text(encoding="utf-8").rstrip("\n") + "\nsupport@example.com\n",
        encoding="utf-8",
    )
    completed = run_validator(str(folder))
    assert completed.returncode == 0
    assert "privacy-email" in completed.stdout


def test_missing_reference_warns_and_fails_strict(tmp_path, run_validator):
    folder = make_skill(tmp_path, "referencing-skill",
                        body="Open references/details.md before answering.\n")
    relaxed = run_validator(str(folder))
    assert relaxed.returncode == 0
    assert "missing-file" in relaxed.stdout
    strict = run_validator("--strict", str(folder))
    assert strict.returncode == 1


def test_empty_folder_reports_missing_skillmd(tmp_path, run_validator):
    (tmp_path / "hollow").mkdir()
    completed = run_validator(str(tmp_path / "hollow"))
    assert completed.returncode == 1
    assert "no skill folders found" in completed.stdout
