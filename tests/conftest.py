"""Test suite setup for the Everyday Agent Skills Pack.

Makes the tools package importable and provides a helper fixture that
runs a skill script the way a real user would: as a subprocess.
Everything here runs fully offline.
"""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
TOOLS = REPO_ROOT / "tools"
SKILLS = REPO_ROOT / "skills"

if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))


@pytest.fixture()
def run_script():
    """Run a script from a skill folder in a subprocess.

    Usage: run_script("plan-my-week", "draft_week_plan.py", path)
    """

    def _run(skill_name: str, script: str, *args: str):
        path = SKILLS / skill_name / "scripts" / script
        assert path.is_file(), f"missing script {script} in {skill_name}"
        return subprocess.run(
            [sys.executable, str(path), *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

    return _run


@pytest.fixture()
def run_validator():
    """Run tools/validate_skill.py in a subprocess."""

    def _run(*args: str):
        return subprocess.run(
            [sys.executable, str(TOOLS / "validate_skill.py"), *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            cwd=REPO_ROOT,
        )

    return _run
