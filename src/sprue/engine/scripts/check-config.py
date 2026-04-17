#!/usr/bin/env python3
"""Static cross-consistency checks across configuration files.

Validates invariants between configs that no other script enforces. Does NOT
read wiki content — see check-frontmatter.py / check-tags.py / check-entity-types.py
for page-level checks.

Checks:
  1. .sprue/defaults.yaml exists and is valid YAML. (error)
  2. Every top-level key in instance/config.yaml exists in
     .sprue/defaults.yaml (catches typos). (error)
  3. Merged config has all required top-level sections. (error)
  4. page_types entries each have 'sections' and 'size_profile'. (error)
  5. facets entries each have 'description' and 'max_per_page'. (error)
  6. Every `size_profile` referenced in page_types is defined in config.yaml:size_profiles. (error)
  7. Every key in config.yaml:page_types (if any) exists in defaults.yaml → page_types:. (error)
  8. Every entry in facets has a mapping with `max_per_page`. (error)
  9. entity-types.yaml:relationship_types has unique `display` names; every entry
     has both `display` and `description`. (error)
 10. Every compile strategy in pipeline.yaml (top-level + each profile) is either
     a built-in (wiki_page) or has a matching .sprue/prompts/<strategy>.md file. (error)
 11. config.yaml's decay_tier and risk_tier enums match the canonical sets
     documented in .sprue/engine.md Frontmatter Schema. (warning)
 12. entity-types.yaml topic slugs follow the project's slug convention
     (lowercase, dash-separated, no spaces). (warning)

Usage:
  python3 .sprue/scripts/check-config.py           # full report
  python3 .sprue/scripts/check-config.py --quiet   # errors only (for verify.sh)
  python3 .sprue/scripts/check-config.py --json    # structured records (for tooling)

Exit: 0 if no errors (warnings allowed); 1 if any error.
"""

import json as jsonlib
import re
import sys
from pathlib import Path

# T11: Route engine/instance paths through resolvers.
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))  # adds src/
from sprue.engine_root import engine_root, instance_root

import yaml

from config import load as load_config

OPS = engine_root()
PROMPTS = OPS / "prompts"

DEFAULTS_YAML = OPS / "defaults.yaml"
CONFIG_YAML = instance_root() / "instance" / "config.yaml"
ENTITY_TYPES_YAML = instance_root() / "instance" / "entity-types.yaml"
PIPELINE_YAML = OPS / "schemas" / "pipeline.yaml"

# Canonical enums per .sprue/engine.md Frontmatter Schema (lines 96-117).
# Update this set in lockstep with engine.md if the schema ever changes.
CANONICAL_DECAY_TIERS = {"fast", "medium", "stable", "glacial"}
CANONICAL_RISK_TIERS = {"critical", "operational", "conceptual", "reference"}

# Built-in compile strategies that don't require an explicit prompt file
# (delegate to .sprue/engine.md contracts).
BUILTIN_STRATEGIES = {"wiki_page"}

SLUG_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]*$")


def load_yaml(path: Path) -> object:
    if not path.exists():
        return None
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def check_size_profiles(config, types_doc):
    errors = []
    profiles = (config or {}).get("size_profiles") or {}
    profile_keys = set(profiles.keys())
    for type_name, type_def in (types_doc or {}).items():
        if not isinstance(type_def, dict):
            continue
        size_profile = type_def.get("size_profile")
        if size_profile is None:
            continue
        if size_profile not in profile_keys:
            errors.append(
                {
                    "check": "size_profile_reference",
                    "severity": "error",
                    "file": str(DEFAULTS_YAML),
                    "message": (
                        f"type '{type_name}' references size_profile '{size_profile}' "
                        f"which is not defined in {CONFIG_YAML}:size_profiles "
                        f"(defined: {sorted(profile_keys)})"
                    ),
                    "related_files": [str(CONFIG_YAML)],
                }
            )
    return errors


def check_page_types_overrides(config, types_doc):
    errors = []
    overrides = (config or {}).get("page_types") or {}
    type_names = set((types_doc or {}).keys())
    for override_key in overrides.keys():
        if override_key not in type_names:
            errors.append(
                {
                    "check": "page_types_override",
                    "severity": "error",
                    "file": str(CONFIG_YAML),
                    "message": (
                        f"page_types override '{override_key}' is not a known type in "
                        f"{DEFAULTS_YAML} (known: {sorted(type_names)}) — override is dead code"
                    ),
                    "related_files": [str(DEFAULTS_YAML)],
                }
            )
    return errors


def check_facets_well_formed(facets_doc):
    errors = []
    for facet_name, facet_def in (facets_doc or {}).items():
        if not isinstance(facet_def, dict):
            errors.append(
                {
                    "check": "facet_structure",
                    "severity": "error",
                    "file": str(DEFAULTS_YAML),
                    "message": (
                        f"facet '{facet_name}' is not a mapping (type {type(facet_def).__name__}) "
                        f"— build-index.py silently filters such entries; declare it as a "
                        f"mapping with max_per_page or remove it"
                    ),
                }
            )
            continue
        if "max_per_page" not in facet_def:
            errors.append(
                {
                    "check": "facet_structure",
                    "severity": "error",
                    "file": str(DEFAULTS_YAML),
                    "message": (
                        f"facet '{facet_name}' is missing required field 'max_per_page' "
                        f"— build-index.py silently filters such entries"
                    ),
                }
            )
    return errors


def check_relationship_types(entity_types_doc):
    errors = []
    raw_rel_types = (entity_types_doc or {}).get("relationship_types") or []
    # Normalize: support both list-of-dicts (name key) and dict-of-dicts (slug key)
    if isinstance(raw_rel_types, list):
        rel_types = {item["name"]: item for item in raw_rel_types if isinstance(item, dict) and "name" in item}
    else:
        rel_types = raw_rel_types or {}
    seen_displays = {}
    for slug, cfg in rel_types.items():
        if not isinstance(cfg, dict):
            errors.append(
                {
                    "check": "relationship_types",
                    "severity": "error",
                    "file": str(ENTITY_TYPES_YAML),
                    "message": (
                        f"relationship_type '{slug}' is not a mapping "
                        f"(type {type(cfg).__name__})"
                    ),
                }
            )
            continue
        display = cfg.get("display")
        description = cfg.get("description")
        if not isinstance(display, str) or not display.strip():
            errors.append(
                {
                    "check": "relationship_types",
                    "severity": "error",
                    "file": str(ENTITY_TYPES_YAML),
                    "message": f"relationship_type '{slug}' missing or empty 'display' field",
                }
            )
            continue
        if not isinstance(description, str) or not description.strip():
            errors.append(
                {
                    "check": "relationship_types",
                    "severity": "error",
                    "file": str(ENTITY_TYPES_YAML),
                    "message": f"relationship_type '{slug}' missing or empty 'description' field",
                }
            )
        norm = display.lower()
        if norm in seen_displays:
            errors.append(
                {
                    "check": "relationship_types",
                    "severity": "error",
                    "file": str(ENTITY_TYPES_YAML),
                    "message": (
                        f"duplicate relationship display '{display}' in '{slug}' — "
                        f"first defined in '{seen_displays[norm]}'"
                    ),
                }
            )
        else:
            seen_displays[norm] = slug
    return errors


def known_strategies():
    """Built-in strategies plus any matching .sprue/prompts/<name>.md (excluding verify-*)."""
    strategies = set(BUILTIN_STRATEGIES)
    if PROMPTS.is_dir():
        for p in PROMPTS.glob("*.md"):
            stem = p.stem
            if stem == "README" or stem.startswith("verify-"):
                continue
            strategies.add(stem)
    return strategies


def check_pipeline_strategies(pipeline_doc):
    errors = []
    strategies = known_strategies()
    refs = []  # list of (location, strategy)

    top_strategy = ((pipeline_doc or {}).get("compile") or {}).get("strategy")
    if top_strategy is not None:
        refs.append(("compile.strategy", top_strategy))

    for profile_name, profile_def in ((pipeline_doc or {}).get("profiles") or {}).items():
        if not isinstance(profile_def, dict):
            continue
        s = (profile_def.get("compile") or {}).get("strategy")
        if s is not None:
            refs.append((f"profiles.{profile_name}.compile.strategy", s))

    for location, strategy in refs:
        if strategy == "custom":
            # Sentinel — caller supplies a custom prompt path; can't statically validate
            continue
        if strategy not in strategies:
            errors.append(
                {
                    "check": "pipeline_strategy",
                    "severity": "error",
                    "file": str(PIPELINE_YAML),
                    "message": (
                        f"{location} = '{strategy}' is not a known strategy. "
                        f"Built-ins: {sorted(BUILTIN_STRATEGIES)}; "
                        f"prompts: {sorted(strategies - BUILTIN_STRATEGIES)}"
                    ),
                    "related_files": [str(PROMPTS)],
                }
            )
    return errors


def check_canonical_enums(config):
    warnings = []
    half_life = set((config or {}).get("half_life_tiers", {}).keys())
    risk = set((config or {}).get("risk_tier_multipliers", {}).keys())

    if half_life and half_life != CANONICAL_DECAY_TIERS:
        warnings.append(
            {
                "check": "canonical_enums",
                "severity": "warning",
                "file": str(CONFIG_YAML),
                "message": (
                    f"half_life_tiers keys {sorted(half_life)} differ from canonical "
                    f"decay_tier enum {sorted(CANONICAL_DECAY_TIERS)} (engine.md "
                    f"Frontmatter Schema). If the schema changed, update both."
                ),
                "related_files": ["sprue/engine.md"],
            }
        )

    if risk and risk != CANONICAL_RISK_TIERS:
        warnings.append(
            {
                "check": "canonical_enums",
                "severity": "warning",
                "file": str(CONFIG_YAML),
                "message": (
                    f"risk_tier_multipliers keys {sorted(risk)} differ from canonical "
                    f"risk_tier enum {sorted(CANONICAL_RISK_TIERS)} (engine.md "
                    f"Frontmatter Schema). If the schema changed, update both."
                ),
                "related_files": ["sprue/engine.md"],
            }
        )
    return warnings


def check_entity_slug_convention(entity_types_doc):
    warnings = []
    entities = (entity_types_doc or {}).get("entities") or {}
    for slug in entities.keys():
        if not isinstance(slug, str) or not SLUG_PATTERN.match(slug):
            warnings.append(
                {
                    "check": "entity_slug_convention",
                    "severity": "warning",
                    "file": str(ENTITY_TYPES_YAML),
                    "message": (
                        f"entity slug {slug!r} does not match convention "
                        f"^[a-z0-9][a-z0-9-]*$ (lowercase, dash-separated, no spaces)"
                    ),
                }
            )
    return warnings


# Schema compatibility window is declared in defaults.yaml under
# `supported_schema_versions: {min, max}`. See T25 / spec invariant
# 'schema compatibility window'.

REQUIRED_SECTIONS = {
    "facets", "page_types", "size_profiles", "half_life_tiers",
    "risk_tier_multipliers", "placement", "maintenance", "expand",
    "verify", "enhance",
}


def check_defaults_valid():
    """Check 1: .sprue/defaults.yaml exists and is valid YAML."""
    errors = []
    if not DEFAULTS_YAML.exists():
        errors.append(
            {
                "check": "defaults_exist",
                "severity": "error",
                "file": str(DEFAULTS_YAML),
                "message": "sprue/defaults.yaml does not exist",
            }
        )
        return errors
    try:
        doc = yaml.safe_load(DEFAULTS_YAML.read_text(encoding="utf-8"))
        if not isinstance(doc, dict):
            errors.append(
                {
                    "check": "defaults_valid",
                    "severity": "error",
                    "file": str(DEFAULTS_YAML),
                    "message": f"sprue/defaults.yaml root is not a mapping (type {type(doc).__name__})",
                }
            )
    except yaml.YAMLError as exc:
        errors.append(
            {
                "check": "defaults_valid",
                "severity": "error",
                "file": str(DEFAULTS_YAML),
                "message": f"sprue/defaults.yaml is not valid YAML: {exc}",
            }
        )
    return errors


def check_schema_version(defaults):
    """Check 1b: schema version range is valid and instance is within range."""
    errors = []
    if not isinstance(defaults, dict):
        return errors
    version = defaults.get("schema_version")
    if not isinstance(version, int):
        errors.append(
            {
                "check": "schema_version_missing",
                "severity": "error",
                "file": str(DEFAULTS_YAML),
                "message": "sprue/defaults.yaml is missing or has non-integer schema_version",
            }
        )
        return errors

    window = defaults.get("supported_schema_versions")
    if not isinstance(window, dict):
        errors.append(
            {
                "check": "schema_window_missing",
                "severity": "error",
                "file": str(DEFAULTS_YAML),
                "message": "sprue/defaults.yaml is missing supported_schema_versions mapping",
            }
        )
        return errors

    wmin = window.get("min")
    wmax = window.get("max")
    if not isinstance(wmin, int) or not isinstance(wmax, int):
        errors.append(
            {
                "check": "schema_window_invalid",
                "severity": "error",
                "file": str(DEFAULTS_YAML),
                "message": "supported_schema_versions.min and .max must be integers",
            }
        )
        return errors

    if wmin > wmax:
        errors.append(
            {
                "check": "schema_window_inverted",
                "severity": "error",
                "file": str(DEFAULTS_YAML),
                "message": (
                    f"supported_schema_versions.min ({wmin}) is greater than "
                    f".max ({wmax}) — window is empty"
                ),
            }
        )
        return errors

    if not (wmin <= version <= wmax):
        errors.append(
            {
                "check": "schema_version_outside_own_window",
                "severity": "error",
                "file": str(DEFAULTS_YAML),
                "message": (
                    f"engine schema_version {version} is outside its own "
                    f"supported range [{wmin}, {wmax}]"
                ),
            }
        )

    # Load instance config and check its schema_version if set
    try:
        instance_cfg = load_yaml(CONFIG_YAML)
    except Exception:
        return errors  # no instance config — that's fine

    if not isinstance(instance_cfg, dict):
        return errors

    inst_ver = instance_cfg.get("schema_version")
    if inst_ver is not None:
        if not isinstance(inst_ver, int):
            errors.append(
                {
                    "check": "instance_schema_invalid",
                    "severity": "error",
                    "file": str(CONFIG_YAML),
                    "message": f"instance schema_version must be an integer, got {type(inst_ver).__name__}",
                }
            )
        elif not (wmin <= inst_ver <= wmax):
            errors.append(
                {
                    "check": "instance_schema_out_of_range",
                    "severity": "error",
                    "file": str(CONFIG_YAML),
                    "message": (
                        f"instance schema_version {inst_ver} is outside supported "
                        f"range [{wmin}, {wmax}] — run `sprue upgrade --accept-schema-change`"
                    ),
                }
            )
    return errors


def check_instance_keys_known(defaults, instance):
    """Check 2: every top-level key in instance/config.yaml exists in defaults (catches typos)."""
    errors = []
    if not instance:
        return errors
    default_keys = set((defaults or {}).keys())
    for key in instance.keys():
        if key not in default_keys:
            errors.append(
                {
                    "check": "instance_key_unknown",
                    "severity": "error",
                    "file": str(CONFIG_YAML),
                    "message": (
                        f"top-level key '{key}' in instance/config.yaml is not defined in "
                        f"sprue/defaults.yaml (known: {sorted(default_keys)}) — possible typo"
                    ),
                    "related_files": [str(DEFAULTS_YAML)],
                }
            )
    return errors


def check_required_sections(merged):
    """Check 3: merged config has all required top-level sections."""
    errors = []
    merged_keys = set((merged or {}).keys())
    for section in sorted(REQUIRED_SECTIONS):
        if section not in merged_keys:
            errors.append(
                {
                    "check": "required_section",
                    "severity": "error",
                    "file": str(DEFAULTS_YAML),
                    "message": f"required top-level section '{section}' missing from merged config",
                    "related_files": [str(CONFIG_YAML)],
                }
            )
    return errors


def check_page_types_structure(merged):
    """Check 4: page_types entries each have 'sections' and 'size_profile'."""
    errors = []
    page_types = (merged or {}).get("page_types") or {}
    for name, defn in page_types.items():
        if not isinstance(defn, dict):
            errors.append(
                {
                    "check": "page_type_structure",
                    "severity": "error",
                    "file": str(DEFAULTS_YAML),
                    "message": f"page_type '{name}' is not a mapping (type {type(defn).__name__})",
                }
            )
            continue
        for required_key in ("sections", "size_profile"):
            if required_key not in defn:
                errors.append(
                    {
                        "check": "page_type_structure",
                        "severity": "error",
                        "file": str(DEFAULTS_YAML),
                        "message": f"page_type '{name}' missing required key '{required_key}'",
                    }
                )
    return errors


def check_facets_structure(merged):
    """Check 5: facets entries each have 'description' and 'max_per_page'."""
    errors = []
    facets = (merged or {}).get("facets") or {}
    for name, defn in facets.items():
        if not isinstance(defn, dict):
            errors.append(
                {
                    "check": "facet_config_structure",
                    "severity": "error",
                    "file": str(DEFAULTS_YAML),
                    "message": f"facet '{name}' is not a mapping (type {type(defn).__name__})",
                }
            )
            continue
        for required_key in ("description", "max_per_page"):
            if required_key not in defn:
                errors.append(
                    {
                        "check": "facet_config_structure",
                        "severity": "error",
                        "file": str(DEFAULTS_YAML),
                        "message": f"facet '{name}' missing required key '{required_key}'",
                    }
                )
    return errors


def main() -> int:
    quiet = "--quiet" in sys.argv
    json_mode = "--json" in sys.argv

    config = load_yaml(CONFIG_YAML)
    entity_types_doc = load_yaml(ENTITY_TYPES_YAML)
    pipeline_doc = load_yaml(PIPELINE_YAML)

    # Raw YAML for instance-key validation; merged config for structural checks
    defaults_raw = load_yaml(DEFAULTS_YAML)
    instance_raw = load_yaml(CONFIG_YAML)
    merged = load_config()

    # page_types and facets now live in the merged config (sprue/defaults.yaml + instance overrides)
    types_doc = merged.get("page_types", {})
    facets_doc = merged.get("facets", {})

    errors = []
    warnings = []

    # New: config-layer validation
    errors += check_defaults_valid()
    errors += check_schema_version(defaults_raw)
    errors += check_instance_keys_known(defaults_raw, instance_raw)
    errors += check_required_sections(merged)
    errors += check_page_types_structure(merged)
    errors += check_facets_structure(merged)

    # Existing cross-consistency checks

    errors += check_size_profiles(merged, types_doc)
    errors += check_page_types_overrides(merged, types_doc)
    errors += check_facets_well_formed(facets_doc)
    errors += check_relationship_types(entity_types_doc)
    errors += check_pipeline_strategies(pipeline_doc)

    warnings += check_canonical_enums(config)
    warnings += check_entity_slug_convention(entity_types_doc)

    if json_mode:
        print(jsonlib.dumps({"errors": errors, "warnings": warnings}, indent=2))
        return 1 if errors else 0

    if quiet:
        for e in errors:
            print(f"[{e['check']}] {e['file']}: {e['message']}")
        return 1 if errors else 0

    if not errors and not warnings:
        print("✅ Config cross-consistency checks passed")
    if errors:
        print(f"❌ {len(errors)} errors:")
        for e in errors:
            print(f"   [{e['check']}] {e['file']}: {e['message']}")
    if warnings:
        print(f"⚠️  {len(warnings)} warnings:", file=sys.stderr)
        for w in warnings:
            print(f"   [{w['check']}] {w['file']}: {w['message']}", file=sys.stderr)

    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
