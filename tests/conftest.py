"""Shared fixtures for Sprue test suite."""

import pytest
from click.testing import CliRunner

from sprue.cli import main
from sprue.engine_root import _clear_cache


@pytest.fixture(autouse=True)
def _reset_resolvers():
    """Clear engine_root/instance_root caches before each test."""
    _clear_cache()
    yield
    _clear_cache()


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def tmp_instance(tmp_path, runner):
    """Return path to a freshly init'd Sprue instance."""
    target = tmp_path / "kb"
    result = runner.invoke(main, ["init", str(target), "--identity", "Test KB."])
    assert result.exit_code == 0, result.output
    return target
