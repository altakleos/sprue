#!/usr/bin/env python3
"""check-page-uses-assets.py — fail when a page skips its source's captured images.

For each wiki page, resolves its frontmatter `sources` to entries in
`imports.yaml`. When any source has a non-empty `assets` list, the page
body must reference at least one of those captured local_path values.
Otherwise, image capture happened but the compile step skipped image
triage/placement — the page is missing visuals the source provided.

Respects the `CONTENT_PAGES` env var (the verify runner writes the
list of pages to check). Runs in both page-scope and whole-scope modes.

Usage:
  python3 .sprue/scripts/check-page-uses-assets.py          # human
  python3 .sprue/scripts/check-page-uses-assets.py --quiet  # exit code only
  python3 .sprue/scripts/check-page-uses-assets.py --json   # structured
"""
from __future__ import annotations

import argparse
import json as jsonlib
import os
import re
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import parse_frontmatter

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))  # adds src/
from sprue.engine_root import instance_root

ROOT = instance_root()
WIKI = ROOT / "wiki"
IMPORTS = ROOT / "instance" / "state" / "imports.yaml"
_IMG_RE = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")


def _load_imports_index() -> dict[str, list[str]]:
    """Return mapping: raw_path -> list of local_path asset strings."""
    if not IMPORTS.is_file():
        return {}
    doc = yaml.safe_load(IMPORTS.read_text(encoding="utf-8")) or []
    if not isinstance(doc, list):
        return {}
    index: dict[str, list[str]] = {}
    for entry in doc:
        if not isinstance(entry, dict):
            continue
        raw = entry.get("raw")
        assets = entry.get("assets") or []
        if not raw or not isinstance(assets, list):
            continue
        paths = [a.get("local_path") for a in assets if isinstance(a, dict) and a.get("local_path")]
        if paths:
            index[raw] = paths
    return index


def _pages_to_check() -> list[Path]:
    """Read CONTENT_PAGES env var (written by verify.py) or fall back to the wiki tree."""
    env = os.environ.get("CONTENT_PAGES", "")
    if env and Path(env).is_file():
        paths = [line.strip() for line in Path(env).read_text().splitlines() if line.strip()]
        return [ROOT / p for p in paths if p.endswith(".md")]
    if not WIKI.is_dir():
        return []
    return sorted(p for p in WIKI.rglob("*.md") if p.is_file())


def _violations_for(page: Path, imports_idx: dict[str, list[str]]) -> list[dict]:
    """Return violation records for one page."""
    try:
        fm, body = parse_frontmatter(page)
    except Exception:
        return []
    sources = fm.get("sources") or []
    if not isinstance(sources, list):
        return []
    expected_assets: list[str] = []
    for src in sources:
        if not isinstance(src, dict):
            continue
        raw = src.get("raw")
        if raw and raw in imports_idx:
            expected_assets.extend(imports_idx[raw])
    if not expected_assets:
        return []  # source has no captured assets — nothing to require
    # Check whether the body references any captured asset filename.
    asset_filenames = {Path(p).name for p in expected_assets}
    body_refs = _IMG_RE.findall(body)
    referenced = any(Path(ref).name in asset_filenames for ref in body_refs)
    if referenced:
        return []
    slug = str(page.relative_to(WIKI)).removesuffix(".md")
    return [{
        "page": slug,
        "assets_available": len(expected_assets),
        "issue": "source_has_assets_but_page_does_not_reference_any",
    }]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--quiet", action="store_true", help="Exit code only")
    parser.add_argument("--json", action="store_true", help="JSON output")
    args = parser.parse_args()

    imports_idx = _load_imports_index()
    if not imports_idx:
        if args.json:
            print(jsonlib.dumps({"violations": []}))
        elif not args.quiet:
            print("⏭️  No imports with captured assets — nothing to check.")
        return 0

    violations: list[dict] = []
    for page in _pages_to_check():
        violations.extend(_violations_for(page, imports_idx))

    if args.json:
        print(jsonlib.dumps({"violations": violations}, indent=2))
    elif violations:
        for v in violations:
            print(
                f"Page: {v['page']}  ✖ source has {v['assets_available']} captured "
                f"image(s) but page references none. Run compile Step 4 (Triage images) "
                f"and place relevant subject-photo/diagram/chart images in the page."
            )
    elif not args.quiet:
        print("✅ All pages with captured-asset sources reference at least one asset.")

    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main())
