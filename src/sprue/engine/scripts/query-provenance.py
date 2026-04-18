#!/usr/bin/env python3
"""Query per-claim provenance chain: claim→source or source→pages.

Usage:
  python3 .sprue/scripts/query-provenance.py --page kafka --claim-id src-1
  python3 .sprue/scripts/query-provenance.py --source-url <url> [--json]
"""
from __future__ import annotations

import argparse, json, sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))  # adds src/
from sprue.engine_root import instance_root

VERIFICATIONS_PATH = instance_root() / "instance" / "state" / "verifications.yaml"
BY_SOURCE_URL_PATH = instance_root() / "wiki" / ".index" / "by-source-url.yaml"


def _load(path: Path):
    if not path.exists():
        return None
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _fail(msg: str, as_json: bool, code: int = 1) -> int:
    if as_json:
        print(json.dumps({"error": msg}))
    else:
        print(msg, file=sys.stderr)
    return code


def query_claim(page: str, claim_id: str) -> dict | None:
    """Look up a single claim from the verification ledger."""
    entries = _load(VERIFICATIONS_PATH)
    if not entries:
        return None
    for entry in reversed(entries):  # newest-first; latest is authoritative
        if entry.get("page") != page:
            continue
        for c in entry.get("claims") or []:
            if c.get("id") != claim_id:
                continue
            return {"page": page, "claim_id": claim_id,
                    "claim_text": c.get("claim", ""),
                    "verdict": c.get("final_verdict") or c.get("writer_verdict", ""),
                    "source_chain": {"tier": c.get("source_tier_used", ""),
                                     "raw_path": c.get("source_ref", ""),
                                     "source_url": c.get("source_url", ""),
                                     "excerpt": c.get("source_excerpt", ""),
                                     "excerpt_hash": c.get("excerpt_hash", "")},
                    "verification": {"verified_at": c.get("verified_at") or entry.get("verified_at", ""),
                                     "mode": entry.get("mode", "")}}
    return None


def _print_claim(r: dict) -> None:
    sc, v = r["source_chain"], r["verification"]
    lines = [f"Page:      {r['page']}", f"Claim:     [{r['claim_id']}] {r['claim_text']}",
             f"Verdict:   {r['verdict']}", f"Tier:      {sc['tier']}"]
    if sc["source_url"]:  lines.append(f"URL:       {sc['source_url']}")
    if sc["raw_path"]:    lines.append(f"Raw:       {sc['raw_path']}")
    if sc["excerpt"]:     lines.append(f"Excerpt:   {sc['excerpt']}")
    if v["verified_at"]:  lines.append(f"Verified:  {v['verified_at']}")
    print("\n".join(lines))


def _print_source(url: str, results: list[dict]) -> None:
    print(f"Source: {url}\nCited by {len(results)} page(s):\n")
    for r in results:
        print(f"  {r['page']}: [{', '.join(r.get('claims', []))}]")


def main() -> int:
    ap = argparse.ArgumentParser(description="Query per-claim provenance chain")
    ap.add_argument("--page", help="Page slug")
    ap.add_argument("--claim-id", help="Claim identifier (e.g. src-1)")
    ap.add_argument("--source-url", help="Source URL for reverse lookup")
    ap.add_argument("--json", action="store_true", help="JSON output")
    args = ap.parse_args()

    if args.source_url and (args.page or args.claim_id):
        return _fail("--source-url cannot be combined with --page/--claim-id", args.json, 2)
    if not args.source_url and not (args.page and args.claim_id):
        return _fail("Provide --page + --claim-id, or --source-url", args.json, 2)

    try:
        if args.source_url:
            index = _load(BY_SOURCE_URL_PATH)
            if index is None:
                return _fail("by-source-url.yaml not found. Run build-index.py first.", args.json)
            results = index.get(args.source_url, [])
            if args.json:
                print(json.dumps(results, indent=2))
            else:
                _print_source(args.source_url, results)
            return 0

        if not VERIFICATIONS_PATH.exists():
            return _fail("verifications.yaml not found. Run verify first.", args.json)

        result = query_claim(args.page, args.claim_id)
        if not result:
            return _fail(f"No claim {args.claim_id} found for page '{args.page}'", args.json)

        if args.json:
            print(json.dumps(result, indent=2))
        else:
            _print_claim(result)
        return 0
    except Exception as e:
        return _fail(str(e), args.json, 2)


if __name__ == "__main__":
    sys.exit(main())
