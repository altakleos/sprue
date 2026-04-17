"""Tests for `sprue init` — AC2, AC4, AC5, AC11, AC18, AC20."""

import sprue
from sprue.cli import main


def test_init_creates_structure(tmp_instance):
    """AC2: init produces the full directory tree."""
    for name in (".sprue", "instance", "raw", "wiki", "notebook", "inbox", "memory", "state"):
        assert (tmp_instance / name).is_dir(), f"missing dir: {name}"
    for name in ("AGENTS.md", "README.md", ".gitignore"):
        assert (tmp_instance / name).is_file(), f"missing file: {name}"


def test_init_renders_identity_in_agents_md(tmp_instance):
    """Identity string appears in AGENTS.md."""
    assert "Test KB." in (tmp_instance / "AGENTS.md").read_text()


def test_init_renders_identity_in_identity_md(tmp_instance):
    """Identity string appears in instance/identity.md."""
    assert "Test KB." in (tmp_instance / "instance" / "identity.md").read_text()


def test_init_writes_version_file(tmp_instance):
    """.sprue/.sprue-version matches package version."""
    assert (tmp_instance / ".sprue" / ".sprue-version").read_text().strip() == sprue.__version__


def test_init_idempotency_without_force(tmp_instance, runner):
    """AC4: second init to same path fails with 'already exists'."""
    result = runner.invoke(main, ["init", str(tmp_instance), "--identity", "X."])
    assert result.exit_code != 0
    assert "already exists" in result.output.lower() or "already exists" in (result.stderr if hasattr(result, 'stderr') else "")


def test_init_force_preserves_user_content(tmp_instance, runner):
    """AC5: --force overwrites .sprue/ but preserves user content."""
    marker = tmp_instance / "wiki" / "marker.md"
    marker.write_text("keep me")
    result = runner.invoke(main, ["init", str(tmp_instance), "--identity", "Reinit.", "--force"])
    assert result.exit_code == 0, result.output
    assert marker.read_text() == "keep me"


def test_init_boot_chain_files_present(tmp_instance):
    """AC11: LLM boot-chain files all present after init."""
    dot_sprue = tmp_instance / ".sprue"
    for path in (
        dot_sprue / "engine.md",
        dot_sprue / "protocols" / "compile.md",
        dot_sprue / "protocols" / "verify.md",
        dot_sprue / "defaults.yaml",
        dot_sprue / "scripts" / "verify.py",
        tmp_instance / "instance" / "identity.md",
        tmp_instance / "AGENTS.md",
    ):
        assert path.is_file(), f"boot-chain file missing: {path}"


def test_init_sprue_dir_no_binary_artifacts(tmp_instance):
    """AC18: .sprue/ contains no compiled Python artifacts."""
    dot_sprue = tmp_instance / ".sprue"
    for p in dot_sprue.rglob("*"):
        assert p.suffix not in (".pyc", ".so", ".pyd"), f"binary artifact: {p}"
        assert p.name != "__pycache__", f"__pycache__ dir: {p}"


def test_init_non_tty_requires_identity_flag(tmp_path, runner):
    """AC20: without --identity in non-TTY mode, exits non-zero."""
    result = runner.invoke(main, ["init", str(tmp_path / "kb")])
    assert result.exit_code != 0
    assert "identity" in result.output.lower()
