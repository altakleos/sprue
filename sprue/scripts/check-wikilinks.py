#!/usr/bin/env python3
"""Detect broken wikilinks — links to pages that don't exist.

Run: python3 sprue/scripts/check-wikilinks.py
Exit 0 = no broken links, exit 1 = broken links found.
"""

import os, re, sys
from pathlib import Path

WIKI = Path("wiki")
SKIP_DIRS = {".obsidian", ".index", "domains", "sources"}

def find_pages():
    slugs = set()
    for root, dirs, files in os.walk(WIKI):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in files:
            if f.endswith(".md"):
                slugs.add(Path(f).stem)
    return slugs

def find_wikilinks(path):
    text = path.read_text(encoding="utf-8")
    # Match [[target]] and [[target|display]]
    return re.findall(r"\[\[([a-zA-Z0-9_-]+)(?:\|[^\]]+)?\]\]", text)

def main():
    slugs = find_pages()
    broken = []

    for root, dirs, files in os.walk(WIKI):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in files:
            if not f.endswith(".md"):
                continue
            path = Path(root) / f
            for target in find_wikilinks(path):
                if target not in slugs:
                    broken.append((path.stem, target))

    if broken:
        print(f"Broken wikilinks ({len(broken)}):")
        for source, target in sorted(set(broken)):
            print(f"  {source} → [[{target}]] (page not found)")
        sys.exit(1)
    else:
        print("✅ All wikilinks resolve")

if __name__ == "__main__":
    main()
