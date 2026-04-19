#!/usr/bin/env python3
"""check-images.py — validate local image references in wiki pages.

Checks every ![alt](path) reference in wiki pages:
  - Path must resolve to an existing file in the instance
  - Alt text must be non-empty (accessibility requirement)

External URLs (http://, https://, data:) are skipped — those are kept
for failed-download cases and are not local references.

Usage:
  python3 .sprue/scripts/check-images.py            # human report
  python3 .sprue/scripts/check-images.py --quiet     # exit code only
  python3 .sprue/scripts/check-images.py --json      # structured output
"""
from __future__ import annotations

import argparse
import json as jsonlib
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import SKIP_FILES, find_wiki_pages

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))  # adds src/
from sprue.engine_root import instance_root

WIKI = instance_root() / "wiki"
ROOT = instance_root()
_IMG_RE = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")
_REMOTE_PREFIXES = ("http://", "https://", "data:")


def _violations_for(page: Path) -> list[dict]:
    """Return violation records for image references in *page*."""
    text = page.read_text(encoding="utf-8")
    slug = str(page.relative_to(WIKI)).removesuffix(".md")
    violations: list[dict] = []
    for alt, ref in _IMG_RE.findall(text):
        if ref.startswith(_REMOTE_PREFIXES):
            continue
        # Try resolving relative to instance root, then relative to page dir.
        resolved = ROOT / ref
        if not resolved.is_file():
            resolved = page.parent / ref
        if not resolved.is_file():
            violations.append({"page": slug, "path": ref, "issue": "missing_file"})
        elif not alt.strip():
            violations.append({"page": slug, "path": ref, "issue": "empty_alt"})
    return violations


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--quiet", action="store_true", help="Exit code only")
    parser.add_argument("--json", action="store_true", help="JSON output")
    args = parser.parse_args()

    if not WIKI.is_dir():
        if args.json:
            print(jsonlib.dumps({"violations": []}))
        elif not args.quiet:
            print("✅ No wiki/ directory — nothing to check.")
        return 0

    violations: list[dict] = []
    page_stats: dict[str, dict] = {}
    for page in find_wiki_pages(WIKI):
        slug = str(page.relative_to(WIKI)).removesuffix(".md")
        page_v = _violations_for(page)
        text = page.read_text(encoding="utf-8")
        local = [m for m in _IMG_RE.findall(text) if not m[1].startswith(_REMOTE_PREFIXES)]
        page_stats[slug] = {"total": len(local), "violations": page_v}
        violations.extend(page_v)

    if args.json:
        print(jsonlib.dumps({"violations": violations}, indent=2))
    elif not args.quiet:
        for slug, info in page_stats.items():
            if not info["total"]:
                continue
            if info["violations"]:
                print(f"Page: {slug}  ✖ {len(info['violations'])} violations:")
                for v in info["violations"]:
                    print(f"   - {v['issue'].replace('_', ' ')}: {v['path']}")
            else:
                print(f"Page: {slug}  ✔ {info['total']} local images all valid")
        if not violations:
            print("✅ Images check passed — all local image references valid.")

    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main())
