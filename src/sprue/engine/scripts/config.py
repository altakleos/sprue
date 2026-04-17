"""Canonical config loader. All scripts import this."""
import yaml
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULTS = ROOT / "sprue" / "defaults.yaml"
INSTANCE = ROOT / "instance" / "config.yaml"

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
    defaults = yaml.safe_load(DEFAULTS.read_text()) or {}
    instance = yaml.safe_load(INSTANCE.read_text()) or {} if INSTANCE.exists() else {}
    return deep_merge(defaults, instance)
