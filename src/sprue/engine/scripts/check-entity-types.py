#!/usr/bin/env python3
"""Validate entity-types.yaml against wiki pages.

Checks:
  1. Every entity page's primary topic appears in entity-types.yaml
  2. Every entry in entity-types.yaml has a corresponding entity page
  3. Relationship types in ## Relationships are in the controlled vocabulary
  4. Wikilink targets in ## Relationships resolve to actual pages

Usage:
  python3 .sprue/scripts/check-entity-types.py           # Full validation
  python3 .sprue/scripts/check-entity-types.py --quiet   # Errors only (for verify.sh)
  python3 .sprue/scripts/check-entity-types.py --json    # Structured records (for resolve-relationships)
"""

import sys, re, yaml
from pathlib import Path
from collections import defaultdict

# T11: Route engine/instance paths through resolvers.
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))  # adds src/
from sprue.engine_root import instance_root

sys.path.insert(0, str(Path(__file__).resolve().parent))  # for lib
from lib import SKIP_DIRS

MANIFEST = instance_root() / "wiki" / ".index" / "manifest.yaml"
ENTITY_TYPES_PATH = instance_root() / "instance" / "entity-types.yaml"
WIKI = instance_root() / "wiki"


def main():
    quiet = "--quiet" in sys.argv
    json_mode = "--json" in sys.argv
    errors = []
    warnings = []
    records = []

    if not MANIFEST.exists():
        print("Error: manifest.yaml not found. Run: python3 .sprue/scripts/build-index.py")
        sys.exit(1)

    if not ENTITY_TYPES_PATH.exists():
        print("Error: entity-types.yaml not found.")
        sys.exit(1)

    manifest = yaml.safe_load(MANIFEST.read_text()) or {}
    manifest.pop("_meta", None)

    et = yaml.safe_load(ENTITY_TYPES_PATH.read_text()) or {}
    registry = et.get("entities", {})
    raw_rel_types = et.get("relationship_types", [])
    # Normalize: support both list-of-dicts (name key) and dict-of-dicts (slug key)
    if isinstance(raw_rel_types, list):
        rel_types = {item["name"]: item for item in raw_rel_types if isinstance(item, dict) and "name" in item}
    else:
        rel_types = raw_rel_types or {}

    # Build display → slug lookup
    rel_display_to_slug = {}
    for slug, cfg in rel_types.items():
        rel_display_to_slug[cfg.get("display", "").lower()] = slug
        rel_display_to_slug[slug] = slug

    # All entity page slugs
    entity_slugs = {slug for slug, meta in manifest.items() if meta.get("type") == "entity"}
    all_slugs = set(manifest.keys())

    # Check 1: Every entity page should be resolvable in the registry
    # Match by: page slug itself, or any of its topic values
    for slug in sorted(entity_slugs):
        topics = manifest[slug].get("topic", [])
        found = slug in registry or any(t in registry for t in topics)
        if not found:
            warnings.append(f"UNREGISTERED: {slug} (topics: {topics}) not in entity-types.yaml")
            records.append({"kind": "UNREGISTERED", "severity": "warning",
                            "entity": slug, "topics": list(topics)})

    # Check 2: Every registry entry should have a corresponding entity page
    for topic_slug, kind in sorted(registry.items()):
        if topic_slug not in all_slugs:
            warnings.append(f"ORPHAN REGISTRY: {topic_slug} → {kind} (no wiki page exists)")
            records.append({"kind": "ORPHAN_REGISTRY", "severity": "warning",
                            "registry_slug": topic_slug, "registry_kind": kind})

    # Check 3 & 4: Validate ## Relationships in entity pages
    for slug in sorted(entity_slugs):
        meta = manifest[slug]
        wiki_dir = meta.get("dir", "")
        if wiki_dir:
            path = WIKI / wiki_dir / f"{slug}.md"
        else:
            path = WIKI / f"{slug}.md"
        if not path.exists():
            continue

        body = path.read_text(encoding="utf-8")
        m = re.search(r'^## Relationships\n(.*?)(?=^## |\Z)', body, re.MULTILINE | re.DOTALL)
        if not m:
            continue

        for line in m.group(1).strip().split('\n'):
            rm = re.match(r'^-\s+\*\*(.+?)\*\*:\s*(.+)', line.strip())
            if not rm:
                continue
            rel_display = rm.group(1).strip()
            targets_raw = rm.group(2).strip()

            # Check 3: relationship type in vocabulary
            if rel_display.lower() not in rel_display_to_slug:
                errors.append(f"UNKNOWN REL TYPE: {slug} uses '{rel_display}' (not in entity-types.yaml)")
                records.append({"kind": "UNKNOWN_REL_TYPE", "severity": "error",
                                "source": slug, "source_path": str(path),
                                "rel_type": rel_display})

            # Check 4: wikilink targets exist
            targets = re.findall(r'\[\[([a-zA-Z0-9_-]+)\]\]', targets_raw)
            for target in targets:
                if target not in all_slugs:
                    warnings.append(f"BROKEN REL LINK: {slug} → [[{target}]] (page not found)")
                    records.append({"kind": "BROKEN_REL_LINK", "severity": "warning",
                                    "source": slug, "source_path": str(path),
                                    "rel_type": rel_display, "target": target})

    # Report
    if json_mode:
        import json
        print(json.dumps({"records": records}, indent=2))
        sys.exit(0)
    if not quiet:
        if not errors and not warnings:
            print("✅ Entity types validation passed")
        else:
            if errors:
                print(f"❌ {len(errors)} errors:")
                for e in errors:
                    print(f"   {e}")
            if warnings:
                print(f"⚠️  {len(warnings)} warnings:")
                for w in warnings:
                    print(f"   {w}")
    else:
        for e in errors:
            print(e)

    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
