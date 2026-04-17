#!/usr/bin/env python3
"""Content verification engine — regex-based claim extraction.

DEPRECATED: This script uses regex-based claim extraction which is noisy
(catches YAML boilerplate, example port numbers) and misses semantic claims
(security assertions, architectural recommendations, performance numbers).

Replaced by: .sprue/protocols/verify.md + .sprue/scripts/prioritize.py
The LLM now performs claim extraction directly during the standalone verify
operation. This script is retained for backward compatibility.

Usage:
  python3 .sprue/scripts/verify-content.py                    # Report all pages by risk tier
  python3 .sprue/scripts/verify-content.py --page kafka       # Single page
  python3 .sprue/scripts/verify-content.py --tier critical     # All critical pages
  python3 .sprue/scripts/verify-content.py --stale 90          # Pages not verified in 90+ days

Output: wiki/.index/verification/ directory with per-page YAML reports.
"""

import re, sys, os, yaml, json
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict

# T11: Route engine/instance paths through resolvers.
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))  # adds src/
from sprue.engine_root import instance_root

WIKI = instance_root() / "wiki"
INDEX_DIR = WIKI / ".index"
VERIFY_DIR = INDEX_DIR / "verification"
SOURCES_FILE = instance_root() / "instance" / "sources.yaml"
MANIFEST_FILE = INDEX_DIR / "manifest.yaml"
SKIP = {"index.md", "overview.md"}
SKIP_DIRS = {".obsidian", ".index", "domains", "sources"}

# Patterns for extracting verifiable claims
CLAIM_PATTERNS = [
    # Version numbers: "PostgreSQL 16", "Kubernetes 1.29", "Python 3.12"
    (r'(?:version\s+)?(\b[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?\s+\d+(?:\.\d+)+)', "version"),
    # Port numbers: "port 5432", ":8080", "listens on 443"
    (r'(?:port\s+|:\s*)(\d{2,5})(?:\s|[,.]|$)', "port"),
    # Defaults: "defaults to X", "default: X", "default is X", "default value of X"
    (r'(?:defaults?\s+(?:to|is|value\s+of|=)\s+)([^\s,.(]+(?:\s+[^\s,.(]+)?)', "default"),
    # Limits: "maximum of X", "limit of X", "up to X", "max X"
    (r'(?:max(?:imum)?\s+(?:of\s+)?|limit\s+(?:of\s+)?|up\s+to\s+)(\d+[\s]?(?:KB|MB|GB|TB|ms|seconds?|minutes?|hours?|bytes?|items?|connections?|requests?)?)', "limit"),
    # Timeout values: "Xms timeout", "timeout of Xs", "X second timeout"
    (r'(\d+)\s*(?:ms|milliseconds?|seconds?|minutes?)\s*(?:timeout|ttl|expir)', "timeout"),
    # CLI flags: --flag-name
    (r'(--[a-z][a-z0-9-]{2,})', "cli_flag"),
    # Config keys: key = value, key: value (in code blocks)
    (r'^(\w[\w.-]+)\s*[=:]\s*(.+)$', "config"),
]


def parse_frontmatter(path):
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    if not m:
        return {}, text
    try:
        fm = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError:
        fm = {}
    return fm, text[m.end():]


def extract_claims(body, slug):
    """Extract verifiable claims from page body."""
    claims = []
    lines = body.split("\n")
    current_section = "intro"
    in_code_block = False

    for i, line in enumerate(lines):
        if line.startswith("```"):
            in_code_block = not in_code_block
            continue

        if line.startswith("## "):
            current_section = line[3:].strip()

        for pattern, claim_type in CLAIM_PATTERNS:
            # Config patterns only in code blocks
            if claim_type == "config" and not in_code_block:
                continue
            # Skip config patterns outside code blocks
            if claim_type != "config" and in_code_block:
                # Still extract versions/limits from code comments
                if not line.strip().startswith(("#", "//", "/*", "--")):
                    continue

            for match in re.finditer(pattern, line, re.IGNORECASE):
                claim_text = match.group(0).strip()
                # Skip very short or noisy matches
                if len(claim_text) < 3:
                    continue
                claims.append({
                    "text": claim_text,
                    "type": claim_type,
                    "line": i + 1,
                    "section": current_section,
                    "context": line.strip()[:120],
                })

    return claims


def find_sources_for_page(techs, slug):
    """Find authoritative sources relevant to a page based on its tech tags."""
    if not SOURCES_FILE.exists():
        return []
    sources = yaml.safe_load(SOURCES_FILE.read_text()) or {}
    relevant = []
    for tag in techs:
        tag_lower = tag.lower()
        if tag_lower in sources:
            relevant.extend(sources[tag_lower])
    # Deduplicate by URL
    seen = set()
    deduped = []
    for s in relevant:
        if s["url"] not in seen:
            seen.add(s["url"])
            deduped.append(s)
    return deduped


def find_pages(filter_page=None, filter_tier=None, stale_days=None):
    """Find wiki pages to verify, filtered by criteria."""
    if not MANIFEST_FILE.exists():
        print("Error: manifest.yaml not found. Run: python3 .sprue/scripts/build-index.py")
        sys.exit(1)

    manifest = yaml.safe_load(MANIFEST_FILE.read_text()) or {}
    manifest.pop("_meta", None)

    pages = []
    for slug, meta in manifest.items():
        if filter_page and slug != filter_page:
            continue
        if filter_tier and meta.get("risk_tier") != filter_tier:
            continue
        if stale_days:
            lv = meta.get("last_verified")
            if lv and lv != "null":
                verified_date = datetime.fromisoformat(str(lv))
                if (datetime.now() - verified_date).days < stale_days:
                    continue

        # Find the actual file using manifest dir field
        wiki_dir = meta.get("dir", "")
        if wiki_dir:
            page_path = WIKI / wiki_dir / f"{slug}.md"
        else:
            page_path = WIKI / f"{slug}.md"
        if not page_path.exists():
            continue
        candidates = [page_path]

        pages.append({
            "slug": slug,
            "path": candidates[0],
            "meta": meta,
        })

    # Sort by risk tier priority
    tier_order = {"critical": 0, "operational": 1, "conceptual": 2, "reference": 3}
    pages.sort(key=lambda p: tier_order.get(p["meta"].get("risk_tier", "reference"), 9))
    return pages


def generate_report(page_info):
    """Generate a verification report for a single page."""
    slug = page_info["slug"]
    meta = page_info["meta"]
    path = page_info["path"]

    fm, body = parse_frontmatter(path)
    claims = extract_claims(body, slug)
    sources = find_sources_for_page(meta.get("topic", []), slug)

    report = {
        "page": slug,
        "risk_tier": meta.get("risk_tier", "unknown"),
        "confidence": meta.get("confidence", "unknown"),
        "last_verified": str(meta.get("last_verified", "null")),
        "generated_at": datetime.now().isoformat()[:19],
        "claims_extracted": len(claims),
        "authoritative_sources": [{"name": s["name"], "url": s["url"]} for s in sources],
        "claims": claims,
    }

    return report


def write_report(report, output_dir=None):
    """Write a verification report to YAML."""
    out_dir = output_dir or VERIFY_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{report['page']}.yaml"

    with open(out_path, "w") as f:
        f.write(f"# Verification report for {report['page']}\n")
        f.write(f"# Generated: {report['generated_at']}\n\n")
        yaml.dump(report, f, default_flow_style=False, allow_unicode=True, width=120)

    return out_path


def main():
    args = sys.argv[1:]
    filter_page = None
    filter_tier = None
    stale_days = None

    i = 0
    while i < len(args):
        if args[i] == "--page" and i + 1 < len(args):
            filter_page = args[i + 1]; i += 2
        elif args[i] == "--tier" and i + 1 < len(args):
            filter_tier = args[i + 1]; i += 2
        elif args[i] == "--stale" and i + 1 < len(args):
            stale_days = int(args[i + 1]); i += 2
        else:
            i += 1

    pages = find_pages(filter_page, filter_tier, stale_days)
    if not pages:
        print("No pages matched the filter criteria.")
        return

    VERIFY_DIR.mkdir(parents=True, exist_ok=True)
    tier_counts = defaultdict(int)
    total_claims = 0

    for page_info in pages:
        report = generate_report(page_info)
        write_report(report)
        tier_counts[report["risk_tier"]] += 1
        total_claims += report["claims_extracted"]

    print(f"✅ Verification reports generated for {len(pages)} pages")
    print(f"   Total claims extracted: {total_claims}")
    for tier in ["critical", "operational", "conceptual", "reference"]:
        if tier_counts[tier]:
            print(f"   {tier}: {tier_counts[tier]} pages")
    print(f"   Output: {VERIFY_DIR}/")


if __name__ == "__main__":
    main()
