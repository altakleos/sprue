#!/usr/bin/env python3
"""Validate faceted frontmatter against emergent vocabulary guardrails.

Checks:
  - per-facet cardinality (max_per_page)
  - per-facet vocabulary size (hard_max ceiling) for facets that define it
  - detect undeclared singular/plural and hyphenation variant pairs
  - editorial overrides from config.yaml (flag if left-side used instead of right-side)
  - below-threshold detection for facets with creation_threshold:
    a value used by < creation_threshold pages is flagged for review
    (consolidate into a populous neighbor, or grow it past the threshold)

The manifest IS the vocabulary. No predefined allow-lists.
Synonym maps removed — the LLM normalizes during compile, this script catches drift.
Exit 0 = pass, exit 1 = errors found.
"""

import os, re, sys, yaml
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import load as load_config
from lib import SKIP_DIRS, SKIP_FILES as SKIP  # backwards compat

# T11: Route engine/instance paths through resolvers.
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))  # adds src/
from sprue.engine_root import instance_root

_cfg = load_config()
FACETS = _cfg["facets"]
OVERRIDES = _cfg.get("overrides", {})

WIKI = instance_root() / "wiki"

errors = []
warnings = []

# Accumulate all values per facet: facet_name → {value → count}
all_values = {name: defaultdict(int) for name in FACETS}


def parse_frontmatter(path):
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    if not m:
        return None
    try:
        return yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError:
        return None


def as_list(val):
    if not val:
        return []
    return val if isinstance(val, list) else [val]


def check_overrides(values, slug, field):
    """Flag values that should have been overridden per config.yaml."""
    for v in values:
        if v in OVERRIDES:
            errors.append(
                f"OVERRIDE VIOLATION '{v}' -> '{OVERRIDES[v]}': {slug} ({field})"
            )


def check_page(path):
    fm = parse_frontmatter(path)
    if fm is None:
        return
    slug = path.stem

    if "tags" in fm:
        errors.append(f"OLD TAGS: {slug} still has 'tags' field")
        return

    for facet_name, facet_cfg in FACETS.items():
        values = as_list(fm.get(facet_name, []))
        max_pp = facet_cfg.get("max_per_page", 999)
        if len(values) > max_pp:
            errors.append(
                f"TOO MANY {facet_name.upper()} ({len(values)}/{max_pp}): {slug}"
            )
        check_overrides(values, slug, facet_name)
        for v in values:
            all_values[facet_name][v] += 1


def check_ceilings():
    for facet_name, facet_cfg in FACETS.items():
        hard_max = facet_cfg.get("hard_max")
        if hard_max is None:
            continue
        count = len(all_values[facet_name])
        label = facet_name.upper()
        if count > hard_max:
            errors.append(
                f"{label} CEILING BREACHED: {count} unique {facet_name} "
                f"(max {hard_max}). Merge the smallest."
            )
        elif count > hard_max - 3:
            warnings.append(f"{label} CEILING NEAR: {count}/{hard_max} {facet_name}")


def check_below_threshold():
    """Flag facet values used by fewer pages than defaults.yaml creation_threshold.

    defaults.yaml documents the semantics: a new value should "stick" only when
    creation_threshold pages share it. Underused values (including singletons)
    are editorial signals — either consolidate into a populous neighbor, or
    grow the value past the threshold.
    """
    for facet_name, facet_cfg in FACETS.items():
        threshold = facet_cfg.get("creation_threshold")
        if threshold is None:
            continue
        # Sort by count ascending so the most underused appear first
        for val, count in sorted(all_values[facet_name].items(), key=lambda x: (x[1], x[0])):
            if count < threshold:
                warnings.append(
                    f"BELOW THRESHOLD {facet_name.upper()} '{val}' "
                    f"({count} pages, threshold {threshold})"
                )


def detect_variants():
    """Detect likely synonym pairs across all facets."""
    combined = set()
    for vals in all_values.values():
        combined |= set(vals)
    for t in sorted(combined):
        # Plural pairs
        if t + "s" in combined:
            warnings.append(f"UNDECLARED PLURAL PAIR: '{t}' / '{t}s'")
        # Hyphenation variants
        bare = t.replace("-", "")
        for other in sorted(combined):
            if other != t and other.replace("-", "") == bare and t < other:
                warnings.append(f"UNDECLARED HYPHENATION PAIR: '{t}' / '{other}'")


def find_pages():
    pages = []
    for root, dirs, files in os.walk(WIKI):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in files:
            if f.endswith(".md") and f not in SKIP:
                pages.append(Path(root) / f)
    return sorted(pages)


if __name__ == "__main__":
    quiet = "--quiet" in sys.argv
    for page in find_pages():
        check_page(page)
    check_ceilings()
    check_below_threshold()
    if not quiet:
        detect_variants()

    if not quiet and warnings:
        print(f"Warnings ({len(warnings)}):", file=sys.stderr)
        for w in warnings:
            print(f"  {w}", file=sys.stderr)

    if errors:
        print(f"\nErrors ({len(errors)}):")
        for e in errors:
            print(f"  {e}")
        sys.exit(1)
