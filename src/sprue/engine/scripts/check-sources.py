#!/usr/bin/env python3
"""check-sources.py — assert LLM-authored sourced pages declare their sources.

Enforces ADR-0028 provenance invariant: every `author: llm` page with
`provenance: sourced` must declare a non-empty `sources` list in frontmatter.
Without this check, the `sources` field rots into aspiration (see ADR-0027).

Synthesized pages (`provenance: synthesized`) are expected to have no
sources and are skipped.

Usage:
  python3 .sprue/scripts/check-sources.py            # full-wiki report
  python3 .sprue/scripts/check-sources.py --quiet    # errors only (for verify)
  python3 .sprue/scripts/check-sources.py --json     # structured records
"""
from __future__ import annotations

import argparse
import json as jsonlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import SKIP_DIRS, SKIP_FILES, find_wiki_pages, parse_frontmatter

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))  # adds src/
from sprue.engine_root import instance_root

WIKI = instance_root() / "wiki"


def _violations_for(path: Path) -> list[dict]:
    """Return a list of violation records for this page (empty if OK)."""
    fm, _ = parse_frontmatter(path)
    if not fm:
        return []  # check-frontmatter handles missing-frontmatter errors.

    if fm.get("author") != "llm":
        return []  # Human-authored pages are out of scope for this rule.

    if fm.get("provenance") != "sourced":
        return []  # Only 'sourced' pages must declare sources.

    sources = fm.get("sources")
    if isinstance(sources, list) and len(sources) > 0:
        return []  # Has at least one source entry — OK.

    return [
        {
            "check": "sources_missing",
            "severity": "error",
            "file": str(path.relative_to(instance_root())),
            "message": (
                "LLM-authored page with provenance:sourced must declare at "
                "least one entry in `sources:` frontmatter (see ADR-0028)."
            ),
        }
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--quiet", action="store_true", help="Errors only")
    parser.add_argument("--json", action="store_true", help="JSON output")
    args = parser.parse_args()

    if not WIKI.is_dir():
        if args.json:
            print(jsonlib.dumps({"violations": []}))
        elif not args.quiet:
            print("✅ No wiki/ directory — nothing to check.")
        return 0

    violations: list[dict] = []
    for page in find_wiki_pages(WIKI):
        violations.extend(_violations_for(page))

    if args.json:
        print(jsonlib.dumps({"violations": violations}, indent=2))
    elif violations:
        for v in violations:
            print(f"  [{v['check']}] {v['file']}: {v['message']}", file=sys.stderr)
    elif not args.quiet:
        print("✅ Sources check passed — all sourced LLM pages declare sources.")

    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main())
