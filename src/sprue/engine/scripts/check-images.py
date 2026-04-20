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
import os
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


_ISSUE_LABELS = {
    "missing_file": "missing file",
    "empty_alt": "empty alt text",
    "kb_root_relative": "KB-root-relative path (must be page-relative, e.g. '../raw/assets/…')",
}


def _pages_to_check() -> list[Path]:
    """Use CONTENT_PAGES env var when set (verify --file scope), else whole wiki."""
    env = os.environ.get("CONTENT_PAGES", "")
    if env and Path(env).is_file():
        paths = [line.strip() for line in Path(env).read_text().splitlines() if line.strip()]
        return [ROOT / p for p in paths if p.endswith(".md")]
    if not WIKI.is_dir():
        return []
    return list(find_wiki_pages(WIKI))


def _violations_for(page: Path) -> list[dict]:
    """Return violation records for image references in *page*.

    Image paths in wiki pages must be relative to the page's directory so
    they render in standard markdown viewers (Obsidian, GitHub, VS Code).
    KB-root-relative paths like ``raw/assets/foo.jpg`` appear valid when
    resolved from ROOT but break in viewers — flag them explicitly.
    """
    text = page.read_text(encoding="utf-8")
    slug = str(page.relative_to(WIKI)).removesuffix(".md")
    violations: list[dict] = []
    for alt, ref in _IMG_RE.findall(text):
        if ref.startswith(_REMOTE_PREFIXES):
            continue
        # Paths MUST resolve relative to the page's directory.
        page_relative = page.parent / ref
        if not page_relative.is_file():
            # Check whether the file exists via KB-root-relative resolution —
            # if yes, this is the common "forgot the ../" mistake, give a
            # targeted hint.
            issue = "kb_root_relative" if (ROOT / ref).is_file() else "missing_file"
            violations.append({"page": slug, "path": ref, "issue": issue})
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
    for page in _pages_to_check():
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
                    print(f"   - {_ISSUE_LABELS.get(v['issue'], v['issue'])}: {v['path']}")
            else:
                print(f"Page: {slug}  ✔ {info['total']} local images all valid")
        if not violations:
            print("✅ Images check passed — all local image references valid.")

    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main())
