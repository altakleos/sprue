#!/usr/bin/env python3
"""check-claims-coverage.py — check per-claim attribution coverage on wiki pages.

Enforces the source-authority spec: verified wiki pages should have inline
[^src-N] markers linking claims to source evidence. When enforce_claims is
false (default), the report is advisory (exit 0). When true, pages below
the coverage threshold cause exit 1.

Usage:
  python3 .sprue/scripts/check-claims-coverage.py            # human report
  python3 .sprue/scripts/check-claims-coverage.py --quiet    # exit code only
  python3 .sprue/scripts/check-claims-coverage.py --json     # structured output
"""
from __future__ import annotations

import argparse
import json as jsonlib
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import load as load_config
from lib import find_wiki_pages, parse_frontmatter

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))  # adds src/
from sprue.engine_root import instance_root

WIKI = instance_root() / "wiki"


def _page_coverage(path: Path, marker_re: re.Pattern) -> dict | None:
    """Return coverage record for a page, or None if not assessable."""
    fm, body = parse_frontmatter(path)
    if not fm:
        return None

    verified = fm.get("claims_verified")
    unverifiable = fm.get("claims_unverifiable")

    if verified is not None and unverifiable is not None:
        total = verified + unverifiable
        coverage = verified / total if total > 0 else 1.0
        return {"slug": path.stem, "coverage": coverage,
                "verified": verified, "total": total}

    # Fallback: count inline markers as a proxy signal.
    markers = marker_re.findall(body)
    if not markers:
        return None  # No verification data — skip.

    return {"slug": path.stem, "coverage": 1.0,
            "verified": len(markers), "total": len(markers)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--quiet", action="store_true", help="Exit code only")
    parser.add_argument("--json", action="store_true", help="JSON output")
    args = parser.parse_args()

    if not WIKI.is_dir():
        if args.json:
            print(jsonlib.dumps({"pages": []}))
        elif not args.quiet:
            print("✅ No wiki/ directory — nothing to check.")
        return 0

    cfg = load_config()
    sa = cfg.get("source_authority", {})
    enforce = sa.get("enforce_claims", False)
    threshold = sa.get("enforce_coverage_threshold", 0.8)
    prefix = sa.get("markers", {}).get("prefix", "src")
    marker_re = re.compile(rf"\[\^{re.escape(prefix)}-\d+\]")

    results = []
    for page in find_wiki_pages(WIKI):
        rec = _page_coverage(page, marker_re)
        if rec:
            rec["pass"] = rec["coverage"] >= threshold
            results.append(rec)

    failures = [r for r in results if not r["pass"]]

    if args.json:
        print(jsonlib.dumps({"pages": results, "enforce": enforce}, indent=2))
    elif not args.quiet:
        for r in results:
            pct = int(r["coverage"] * 100)
            mark = "✔" if r["pass"] else "✖ below threshold"
            print(f"Page: {r['slug']}  coverage: {pct}% "
                  f"({r['verified']}/{r['total']} claims)  {mark}")
        if not results:
            print("✅ No pages with claim verification data.")
        elif not failures:
            print("✅ Claims coverage check passed.")

    if not enforce:
        return 0  # Advisory mode — always pass.
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
