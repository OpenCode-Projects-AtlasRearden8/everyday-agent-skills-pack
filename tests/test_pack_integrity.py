"""Pack-level integrity tests: files, consistency, license, no drift."""

from __future__ import annotations

from pathlib import Path

from conftest import REPO_ROOT, SKILLS

ALL_SKILLS = [
    "plan-my-week",
    "prep-my-appointment",
    "draft-a-kind-letter",
    "untangle-a-bill",
    "learn-one-thing",
    "declutter-a-folder",
]


def test_required_top_level_files_exist():
    for name in (
        "README.md", "LICENSE", "STATUS.md", "pyproject.toml",
        "requirements-dev.txt", ".gitignore",
    ):
        assert (REPO_ROOT / name).is_file(), name


def test_each_skill_has_reference_and_failure_materials():
    for name in ALL_SKILLS:
        folder = SKILLS / name
        assert (folder / "SKILL.md").is_file()
        assert (folder / "references" / "example-output.md").is_file(), name
        assert (folder / "references" / "failure-prompts.md").is_file(), name
        scripts = sorted((folder / "scripts").glob("*.py")) if (folder / "scripts").is_dir() else []
        assert scripts, f"{name} has no script"


def test_every_skill_has_sections_and_boundaries():
    for name in ALL_SKILLS:
        skill_text = (SKILLS / name / "SKILL.md").read_text(encoding="utf-8")
        for heading in ("When to use it", "How to do it", "Boundaries", "Output format"):
            assert heading in skill_text, (name, heading)
        assert "python scripts/" in skill_text, name
        assert "references/example-output.md" in skill_text, name
        assert "references/failure-prompts.md" in skill_text, name


def test_readme_lists_every_skill():
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    for name in ALL_SKILLS:
        assert name in readme, name


def test_readme_credits_asdale_and_marks_distinction():
    readme = " ".join((REPO_ROOT / "README.md").read_text(encoding="utf-8").split())
    assert "Asdale Dynamics, LLC" in readme
    assert "agent-skill-starter" in readme
    assert "The Massive AI Manual" in readme


def test_license_line_is_exact():
    license_text = (REPO_ROOT / "LICENSE").read_text(encoding="utf-8")
    assert "Copyright (c) 2026 Asdale Dynamics, LLC" in license_text
    assert license_text.startswith("MIT License")


def test_no_secrets_in_pack_text_files():
    import re

    from validate_skill import SECRET_PATTERNS

    patterns = [pattern for _, pattern in SECRET_PATTERNS]
    offenders = []
    for path in REPO_ROOT.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix not in (".md", ".txt", ".py", ".json", ".toml", ".yml", ".yaml"):
            continue
        parts = path.relative_to(REPO_ROOT).parts
        if any(part.startswith(".") or part == "__pycache__" for part in parts[:-1]):
            continue
        if parts[0] == "tests":
            continue  # test fixtures intentionally carry fake token shapes
        text = path.read_text(encoding="utf-8", errors="replace")
        for pattern in patterns:
            if pattern.search(text):
                offenders.append(str(path))
    assert not offenders, offenders


def test_scripts_are_standard_library_only():
    import ast

    allowed = {
        "argparse", "json", "sys", "re", "pathlib", "collections",
        "datetime", "dataclasses", "subprocess", "ast",
    }
    for name in ALL_SKILLS:
        for script in (SKILLS / name / "scripts").glob("*.py"):
            tree = ast.parse(script.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        root = alias.name.split(".")[0]
                        assert root in allowed or root.startswith("_"), (script, alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.level or node.module is None:
                        continue
                    assert node.module.split(".")[0] in allowed or node.module == "__future__", (script, node.module)


def test_tooling_is_offline_and_self_contained():
    validator = (REPO_ROOT / "tools" / "validate_skill.py").read_text(encoding="utf-8")
    assert "from __future__" in validator
    requirements = (REPO_ROOT / "requirements-dev.txt").read_text(encoding="utf-8")
    assert "pytest" in requirements
    config = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert "[tool.pytest.ini_options]" in config


def test_docs_exist_and_explain_usage():
    for name in ("using-the-pack.md", "adding-a-skill.md"):
        doc = (REPO_ROOT / "docs" / name).read_text(encoding="utf-8")
        assert len(doc) > 200, name
    using = (REPO_ROOT / "docs" / "using-the-pack.md").read_text(encoding="utf-8")
    assert "python" in using.lower()
    for skill_name in ("untangle-a-bill", "declutter-a-folder"):
        assert skill_name in using
