"""Tests for check-package-contents.py — AC9."""

import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "src" / "sprue" / "engine" / "scripts" / "check-package-contents.py"


@pytest.mark.slow
def test_built_wheel_passes_validation(tmp_path):
    """AC9: real built wheel contains no forbidden instance paths."""
    subprocess.run(
        [sys.executable, "-m", "build", "--wheel", "--outdir", str(tmp_path)],
        cwd=str(REPO_ROOT),
        check=True,
        capture_output=True,
    )
    wheels = list(tmp_path.glob("*.whl"))
    assert wheels, "no wheel produced"
    result = subprocess.run(
        [sys.executable, str(SCRIPT), str(wheels[0])],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    assert "OK" in result.stdout


def test_validator_flags_forbidden_paths(tmp_path):
    """AC9: validator rejects a wheel containing instance paths."""
    fake_wheel = tmp_path / "fake-0.0.0-py3-none-any.whl"
    with zipfile.ZipFile(fake_wheel, "w") as zf:
        zf.writestr("sprue/engine/ok.py", "# ok")
        zf.writestr("instance/identity.md", "# forbidden")
    result = subprocess.run(
        [sys.executable, str(SCRIPT), str(fake_wheel)],
        capture_output=True, text=True,
    )
    assert result.returncode == 1
    assert "instance" in result.stderr.lower()
