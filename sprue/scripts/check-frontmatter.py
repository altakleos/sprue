#!/usr/bin/env python3
"""Verify every wiki page has complete frontmatter.

Required fields = system fields + all facets from sprue/defaults.yaml → facets:.
Facet names are read dynamically — adding a facet to defaults.yaml
automatically adds it to the verification check.
Valid page types are read from sprue/defaults.yaml → page_types:.
"""

import os, re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import load as load_config

_cfg = load_config()
facet_names = list(_cfg["facets"].keys())

VALID_TYPES = set(_cfg["page_types"].keys())

REQUIRED = ["type"] + facet_names + ["decay_tier", "confidence", "provenance", "author", "last_verified", "risk_tier", "summary"]

WIKI = Path("wiki")
SKIP_DIRS = {".obsidian", ".index", "domains"}
SKIP_FILES = {"index.md", "overview.md"}

errors = []
for root, dirs, files in os.walk(WIKI):
    dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
    for f in sorted(files):
        if not f.endswith(".md") or f in SKIP_FILES:
            continue
        path = Path(root) / f
        text = path.read_text(encoding="utf-8")
        m = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
        if not m:
            continue
        fm_text = m.group(1)
        for field in REQUIRED:
            if not re.search(rf"^{field}:", fm_text, re.MULTILINE):
                errors.append(f"MISSING {field}: {path}")
        # Validate type value against sprue/defaults.yaml → page_types:
        tm = re.search(r"^type:\s*(.+)$", fm_text, re.MULTILINE)
        if tm:
            type_val = tm.group(1).strip()
            if type_val not in VALID_TYPES:
                errors.append(f"INVALID TYPE '{type_val}': {path} (allowed: {', '.join(sorted(VALID_TYPES))})")

for e in errors:
    print(e)
