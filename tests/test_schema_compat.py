"""Tests for schema version validation logic in check-config.py."""

import importlib.util
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Load check-config.py via importlib (hyphenated filename).
_SCRIPT = Path(__file__).resolve().parents[1] / "src" / "sprue" / "engine" / "scripts" / "check-config.py"
_spec = importlib.util.spec_from_file_location("check_config", _SCRIPT)
_mod = importlib.util.module_from_spec(_spec)

# The module imports from `config` (sibling), so add scripts dir to path.
_scripts_dir = str(_SCRIPT.parent)
if _scripts_dir not in sys.path:
    sys.path.insert(0, _scripts_dir)
_spec.loader.exec_module(_mod)

check_schema_version = _mod.check_schema_version


def _defaults(schema_version, wmin, wmax):
    return {
        "schema_version": schema_version,
        "supported_schema_versions": {"min": wmin, "max": wmax},
    }


def test_valid_schema_passes():
    """No errors when schema_version is within its own window."""
    errors = check_schema_version(_defaults(1, 1, 1))
    assert not errors


def test_inverted_window_flagged():
    """M2: min > max produces schema_window_inverted error."""
    errors = check_schema_version(_defaults(1, 2, 1))
    checks = [e["check"] for e in errors]
    assert "schema_window_inverted" in checks


def test_version_outside_own_window():
    """schema_version outside [min, max] produces error."""
    errors = check_schema_version(_defaults(5, 1, 3))
    checks = [e["check"] for e in errors]
    assert "schema_version_outside_own_window" in checks
