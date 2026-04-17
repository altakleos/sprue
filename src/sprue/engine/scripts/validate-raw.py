#!/usr/bin/env python3
"""sprue/scripts/validate-raw.py — Validate raw/ invariants.

Checks:
  1. No duplicate source URLs in imports.yaml
  2. No raw .md files with agent-injected YAML frontmatter
     (detected by frontmatter containing 'source:' or 'title:' keys
      that match imports.yaml metadata patterns)

Usage: python3 .sprue/scripts/validate-raw.py
Exit code: 0 = clean, 1 = violations found
"""
import sys, re
from pathlib import Path

# T11: Route engine/instance paths through resolvers.
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))  # adds src/
from sprue.engine_root import instance_root

try:
    import yaml
except ImportError:
    print("⚠️  PyYAML not installed — skipping imports.yaml dedup check")
    yaml = None

errors = []

# --- Check 1: duplicate source URLs in imports.yaml ---
imports_path = instance_root() / "instance" / "state" / "imports.yaml"
if yaml and imports_path.exists():
    try:
        entries = yaml.safe_load(imports_path.read_text()) or []
    except yaml.YAMLError as e:
        errors.append(f"imports.yaml parse error (fix manually): {e}")
        entries = []
    seen = {}
    for e in entries:
        url = e.get("source", "")
        if e.get("superseded_by"):
            continue  # old entry, skip dedup check
        if url in seen:
            errors.append(
                f"duplicate source URL in imports.yaml: {url}\n"
                f"    first: {seen[url]}\n"
                f"    also:  {e.get('raw', '?')}"
            )
        else:
            seen[url] = e.get("raw", "?")

# --- Check 2: agent-injected frontmatter in raw .md files ---
FM_RE = re.compile(r"^---\s*\n(.*?)\n---", re.DOTALL)
RAW_DIR = instance_root() / "raw"
for md in sorted(RAW_DIR.rglob("*.md")) if RAW_DIR.exists() else []:
    text = md.read_text(errors="replace")
    m = FM_RE.match(text)
    if m:
        fm_block = m.group(1)
        if re.search(r"^(source|title|content_type):", fm_block, re.MULTILINE):
            errors.append(f"agent-injected frontmatter: {md.relative_to(instance_root())}")

# --- Report ---
if errors:
    print(f"❌ {len(errors)} raw/ violation(s):\n")
    for e in errors:
        print(f"  • {e}")
    sys.exit(1)
else:
    print("✅ raw/ invariants OK")
    sys.exit(0)
