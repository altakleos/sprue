#!/usr/bin/env python3
"""check-asset-capture.py — flag raw markdown with uncaptured remote images.

When images.enabled and images.capture.enabled are both true, every raw
markdown file with remote image refs should have an `assets` field in its
imports.yaml entry. Missing assets = Step 4a was skipped during import.
"""
from __future__ import annotations

import argparse
import json as jsonlib
import re
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import load as load_config
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from sprue.engine_root import instance_root

ROOT = instance_root()
IMPORTS_FILE = ROOT / "instance" / "state" / "imports.yaml"
_IMG_RE = re.compile(r"!\[[^\]]*\]\((https?://[^)]+|data:image/[^)]+)\)")
_MD_TYPES = {"article", "tutorial", "readme", "paper", "thread"}

def _load_imports() -> list[dict]:
    if not IMPORTS_FILE.is_file():
        return []
    doc = yaml.safe_load(IMPORTS_FILE.read_text(encoding="utf-8"))
    return doc if isinstance(doc, list) else []

def _count_remote_refs(path: Path) -> int:
    try:
        return len(_IMG_RE.findall(path.read_text(encoding="utf-8")))
    except (OSError, UnicodeDecodeError):
        return 0

def _violations() -> list[dict]:
    violations = []
    for entry in _load_imports():
        if entry.get("content_type", "") not in _MD_TYPES:
            continue
        raw_path = entry.get("raw", "")
        if not raw_path:
            continue
        full = ROOT / raw_path
        if not full.is_file():
            continue
        count = _count_remote_refs(full)
        if count == 0:
            continue
        assets = entry.get("assets")
        if isinstance(assets, list) and len(assets) > 0:
            continue
        violations.append({
            "source": entry.get("source", raw_path),
            "raw": raw_path,
            "remote_refs": count,
        })
    return violations

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--quiet", action="store_true", help="Exit code only")
    parser.add_argument("--json", action="store_true", help="JSON output")
    args = parser.parse_args()

    cfg = load_config()
    img = cfg.get("images", {})
    if not img.get("enabled", False):
        if not args.quiet and not args.json:
            print("⏭️  Asset capture check skipped (images.enabled: false)")
        return 0
    if not img.get("capture", {}).get("enabled", False):
        if not args.quiet and not args.json:
            print("⏭️  Asset capture check skipped (images.capture.enabled: false)")
        return 0

    vs = _violations()
    if args.json:
        print(jsonlib.dumps({"violations": vs}, indent=2))
    elif vs:
        for v in vs:
            print(
                f"Source: {v['source']}  ✖ raw has {v['remote_refs']} remote image "
                f"refs but no captured assets\n  Raw: {v['raw']}",
                file=sys.stderr,
            )
    elif not args.quiet:
        print("✅ Asset capture check passed — all raw files with remote images have assets.")
    return 1 if vs else 0

if __name__ == "__main__":
    sys.exit(main())
