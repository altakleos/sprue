"""Tests for `sprue upgrade` — AC6, AC10, AC12."""

import os
import sys

import pytest

from sprue.cli import main


def test_upgrade_same_version_idempotent(tmp_instance, runner):
    """AC12: upgrade when already current exits 0 with 'up to date'."""
    result = runner.invoke(main, ["upgrade", str(tmp_instance)])
    assert result.exit_code == 0
    assert "up to date" in result.output.lower()


def test_upgrade_preserves_instance_content(tmp_instance, runner):
    """AC6: upgrade replaces .sprue/ but leaves instance content intact."""
    markers = {
        "wiki/marker.md": "wiki-content",
        "raw/marker.txt": "raw-content",
        "memory/marker.yaml": "memory-content",
    }
    for rel, content in markers.items():
        p = tmp_instance / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
    # Tamper version to trigger actual upgrade
    (tmp_instance / ".sprue" / ".sprue-version").write_text("0.0.1")
    result = runner.invoke(main, ["upgrade", str(tmp_instance)])
    assert result.exit_code == 0, result.output
    for rel, content in markers.items():
        assert (tmp_instance / rel).read_text() == content, f"{rel} was modified"


def test_upgrade_rejects_non_instance(tmp_path, runner):
    """upgrade on a dir without .sprue/ fails with clear message."""
    result = runner.invoke(main, ["upgrade", str(tmp_path)])
    assert result.exit_code != 0
    assert "not a sprue instance" in result.output.lower()


@pytest.mark.skipif(sys.platform == "win32", reason="symlinks unreliable on Windows")
def test_upgrade_rejects_symlink_sprue_dir(tmp_instance, runner, tmp_path):
    """upgrade refuses when .sprue/ is a symlink."""
    real = tmp_path / "real_sprue"
    real.mkdir()
    dot_sprue = tmp_instance / ".sprue"
    # Replace .sprue/ with a symlink
    import shutil
    shutil.rmtree(dot_sprue)
    os.symlink(real, dot_sprue)
    result = runner.invoke(main, ["upgrade", str(tmp_instance)])
    assert result.exit_code != 0
    assert "symlink" in result.output.lower()


def test_upgrade_schema_mismatch_without_flag(tmp_instance, runner):
    """AC10: schema_version out of range produces clear error."""
    (tmp_instance / "instance" / "config.yaml").write_text("schema_version: 999\n")
    (tmp_instance / ".sprue" / ".sprue-version").write_text("0.0.1")
    result = runner.invoke(main, ["upgrade", str(tmp_instance)])
    assert result.exit_code != 0
    assert "schema" in result.output.lower()


def test_upgrade_schema_mismatch_with_flag(tmp_instance, runner):
    """AC10: --accept-schema-change proceeds despite mismatch."""
    (tmp_instance / "instance" / "config.yaml").write_text("schema_version: 999\n")
    (tmp_instance / ".sprue" / ".sprue-version").write_text("0.0.1")
    result = runner.invoke(main, ["upgrade", str(tmp_instance), "--accept-schema-change"])
    assert result.exit_code == 0, result.output


def test_upgrade_sweeps_stale_artifacts(tmp_instance, runner):
    """M5: stale .sprue.old.* and tmpXXXXXXXX dirs are cleaned on upgrade."""
    # Simulate dangling artifacts from a SIGKILL'd prior run.
    stale_sidelined = tmp_instance / ".sprue.old.12345"
    stale_tempdir = tmp_instance / "tmpABCD1234"
    legit_dir = tmp_instance / "tmp_my_notes"  # Not matching pattern — preserved.
    for d in (stale_sidelined, stale_tempdir, legit_dir):
        d.mkdir()
        (d / "marker.txt").write_text("x")

    # Runs sweep via the "already up to date" path.
    result = runner.invoke(main, ["upgrade", str(tmp_instance)])
    assert result.exit_code == 0, result.output

    assert not stale_sidelined.exists()
    assert not stale_tempdir.exists()
    assert legit_dir.exists(), "non-matching dir should be preserved"
