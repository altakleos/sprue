#!/usr/bin/env python3
"""Prepare verification context for LLM-driven content fixes.

Reads verification reports, fetches authoritative source content via Jina Reader,
and assembles structured context that an LLM agent uses to verify and fix claims.

Usage:
  python3 sprue/scripts/fix-content.py --page postgresql     # Single page
  python3 sprue/scripts/fix-content.py --tier critical        # All critical pages
  python3 sprue/scripts/fix-content.py --top 10               # Top 10 pages by claim density

Output: wiki/.index/fix-context/ directory with per-page context files.
Each file contains the page content, extracted claims, and fetched source excerpts
ready for an LLM agent to review and apply fixes.
"""

import sys, os, re, yaml, json, subprocess
from pathlib import Path
from datetime import datetime
from collections import defaultdict

WIKI = Path("wiki")
INDEX_DIR = WIKI / ".index"
VERIFY_DIR = INDEX_DIR / "verification"
FIX_DIR = INDEX_DIR / "fix-context"
SOURCES_FILE = Path("instance/sources.yaml")
FIX_LOG = INDEX_DIR / "fix-log.jsonl"
CORRECTIONS_FILE = Path("memory/corrections.md")


def fetch_url(url, search_terms=None):
    """Fetch URL content via Jina Reader. Returns markdown text or None."""
    jina_url = f"https://r.jina.ai/{url}"
    try:
        cmd = ["curl", "-sL", "--max-time", "15", jina_url]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
        if result.returncode == 0 and len(result.stdout) > 100:
            text = result.stdout
            # Truncate to ~4000 chars to keep context manageable
            if len(text) > 4000:
                if search_terms:
                    # Try to find relevant section
                    for term in search_terms:
                        idx = text.lower().find(term.lower())
                        if idx > 0:
                            start = max(0, idx - 500)
                            text = text[start:start + 4000]
                            break
                    else:
                        text = text[:4000]
                else:
                    text = text[:4000]
            return text
    except Exception:
        pass
    return None


def load_verification_report(slug):
    """Load a verification report for a page."""
    report_path = VERIFY_DIR / f"{slug}.yaml"
    if not report_path.exists():
        return None
    return yaml.safe_load(report_path.read_text())


def load_page_content(slug):
    """Find and read a wiki page by slug."""
    candidates = list(WIKI.glob(f"**/{slug}.md"))
    if not candidates:
        return None, None
    path = candidates[0]
    return path, path.read_text(encoding="utf-8")


def load_active_corrections(slug):
    """Load active factual corrections relevant to a page."""
    if not CORRECTIONS_FILE.exists():
        return []
    text = CORRECTIONS_FILE.read_text()
    retired_start = text.find("<!-- retired")
    if retired_start != -1:
        text = text[:retired_start]

    corrections = []
    for m in re.finditer(r'-\s+\*\*(.+?)\s*/\s*(.+?)\*\*:\s*(.+?)(?=\n-\s+\*\*|\n<!--|\Z)', text, re.DOTALL):
        page_field = m.group(1).strip()
        if slug in page_field.lower() or page_field.lower() in slug:
            corrections.append(m.group(0).strip())
    return corrections


def build_fix_context(slug, report, page_content, fetched_sources, corrections):
    """Assemble the full context document for LLM-driven fixing."""
    ctx = []
    ctx.append(f"# Verification Context: {slug}")
    ctx.append(f"Generated: {datetime.now().isoformat()[:19]}")
    ctx.append(f"Risk tier: {report.get('risk_tier', 'unknown')}")
    ctx.append(f"Current confidence: {report.get('confidence', 'unknown')}")
    ctx.append(f"Claims extracted: {report.get('claims_extracted', 0)}")
    ctx.append("")

    if corrections:
        ctx.append("## Active Corrections (MUST be respected)")
        for c in corrections:
            ctx.append(c)
        ctx.append("")

    ctx.append("## Extracted Claims")
    ctx.append("")
    for i, claim in enumerate(report.get("claims", []), 1):
        ctx.append(f"### Claim {i} ({claim['type']})")
        ctx.append(f"- **Text:** {claim['text']}")
        ctx.append(f"- **Section:** {claim['section']}")
        ctx.append(f"- **Line:** {claim['line']}")
        ctx.append(f"- **Context:** {claim['context']}")
        ctx.append("")

    if fetched_sources:
        ctx.append("## Authoritative Source Content")
        ctx.append("")
        for name, content in fetched_sources.items():
            ctx.append(f"### {name}")
            ctx.append("```")
            ctx.append(content[:3000])
            ctx.append("```")
            ctx.append("")

    ctx.append("## Current Page Content")
    ctx.append("```markdown")
    ctx.append(page_content)
    ctx.append("```")

    return "\n".join(ctx)


def select_pages(filter_page=None, filter_tier=None, top_n=None):
    """Select pages to process based on filters."""
    if not VERIFY_DIR.exists():
        print("Error: No verification reports found. Run: python3 sprue/scripts/verify-content.py")
        sys.exit(1)

    reports = []
    for f in sorted(VERIFY_DIR.glob("*.yaml")):
        report = yaml.safe_load(f.read_text())
        if not report:
            continue
        slug = report.get("page", f.stem)
        if filter_page and slug != filter_page:
            continue
        if filter_tier and report.get("risk_tier") != filter_tier:
            continue
        reports.append(report)

    # Sort by claim density (more claims = more to verify)
    reports.sort(key=lambda r: r.get("claims_extracted", 0), reverse=True)

    if top_n:
        reports = reports[:top_n]

    return reports


def log_fix(slug, section, old_text, new_text, source_url, evidence):
    """Append a fix to the fix log."""
    FIX_LOG.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "page": slug,
        "section": section,
        "old": old_text[:200],
        "new": new_text[:200],
        "source": source_url,
        "evidence": evidence[:200],
    }
    with open(FIX_LOG, "a") as f:
        f.write(json.dumps(entry) + "\n")


def main():
    args = sys.argv[1:]
    filter_page = None
    filter_tier = None
    top_n = None
    fetch = "--no-fetch" not in args

    i = 0
    while i < len(args):
        if args[i] == "--page" and i + 1 < len(args):
            filter_page = args[i + 1]; i += 2
        elif args[i] == "--tier" and i + 1 < len(args):
            filter_tier = args[i + 1]; i += 2
        elif args[i] == "--top" and i + 1 < len(args):
            top_n = int(args[i + 1]); i += 2
        else:
            i += 1

    reports = select_pages(filter_page, filter_tier, top_n)
    if not reports:
        print("No pages matched the filter criteria.")
        return

    FIX_DIR.mkdir(parents=True, exist_ok=True)
    manifest = yaml.safe_load(Path("wiki/.index/manifest.yaml").read_text()) or {}
    manifest.pop("_meta", None)
    processed = 0

    for report in reports:
        slug = report["page"]
        path, content = load_page_content(slug)
        if not content:
            continue

        # Fetch authoritative sources — look up from sources.yaml by page tech tags
        fetched = {}
        if fetch:
            sources_db = {}
            if SOURCES_FILE.exists():
                sources_db = yaml.safe_load(SOURCES_FILE.read_text()) or {}
            # Match page tech tags against sources.yaml keys
            page_meta = manifest.get(slug, {})
            page_techs = page_meta.get("topic", [])
            # Also check slug itself as a source key
            lookup_keys = list(page_techs) + [slug]
            auth_sources = []
            for key in lookup_keys:
                if key.lower() in sources_db:
                    auth_sources.extend(sources_db[key.lower()])
            # Deduplicate by URL
            seen_urls = set()
            auth_sources = [s for s in auth_sources if s["url"] not in seen_urls and not seen_urls.add(s["url"])]

            if auth_sources:
                search_terms = [c["text"] for c in report.get("claims", [])[:5]]
                for src in auth_sources[:2]:  # Limit to 2 sources
                    print(f"  Fetching {src['name']}...")
                    text = fetch_url(src["url"], search_terms)
                    if text:
                        fetched[src["name"]] = text

        corrections = load_active_corrections(slug)
        ctx = build_fix_context(slug, report, content, fetched, corrections)

        out_path = FIX_DIR / f"{slug}.md"
        out_path.write_text(ctx, encoding="utf-8")
        processed += 1

    print(f"✅ Fix context prepared for {processed} pages")
    print(f"   Output: {FIX_DIR}/")
    print(f"\nNext step: LLM agent reads each context file and applies fixes.")
    print(f"See sprue/protocols/fix-protocol.md for the agent workflow.")


if __name__ == "__main__":
    main()
