"""Canonical config loader. All scripts import this."""
import sys
from pathlib import Path

# T9: Use package resolvers for engine/instance paths.
# Fallback sys.path insert needed because scripts/ is not a package and
# scripts are invoked standalone (e.g., python3 .sprue/scripts/config.py).
# T11 will migrate all invocations to go through the package.
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))  # adds src/
from sprue.engine_root import engine_root, instance_root

import yaml

def deep_merge(base: dict, override: dict) -> dict:
    """Recursive merge. Override wins for scalars. Lists replaced wholesale."""
    merged = base.copy()
    for key, val in override.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(val, dict):
            merged[key] = deep_merge(merged[key], val)
        else:
            merged[key] = val
    return merged

def load() -> dict:
    """Return effective config: platform defaults + instance overrides."""
    defaults_path = engine_root() / "defaults.yaml"
    instance_path = instance_root() / "instance" / "config.yaml"
    defaults = yaml.safe_load(defaults_path.read_text()) or {}
    instance = yaml.safe_load(instance_path.read_text()) or {} if instance_path.exists() else {}
    return deep_merge(defaults, instance)
