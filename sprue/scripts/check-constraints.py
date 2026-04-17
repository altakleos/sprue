#!/usr/bin/env python3
"""Check that no wiki page violates active factual corrections in memory/corrections.md.

For each correction, verifies on its scoped page(s):
  1. The `wrong` substring is ABSENT.
  2. The `probe` substring (if specified) is PRESENT.

This closes the correction loop: a page that deletes the wrong sentence
without adding the correct content is flagged as MISSING_PROBE.

Violation kinds:
  WRONG_PRESENT   — wrong substring found (lingering incorrect content)
  MISSING_PROBE   — probe specified but absent (fix not actually applied)
  INCOMPLETE_FIX  — both wrong AND probe present (old and new coexist)

Usage:
  python3 sprue/scripts/check-constraints.py           # violations to stdout (for verify.sh)
  python3 sprue/scripts/check-constraints.py --json    # structured records for tooling
"""

import re
import sys
from pathlib import Path

CORRECTIONS_FILE = Path("memory/corrections.md")
WIKI = Path("wiki")


def parse_corrections():
    """Extract active corrections from memory/corrections.md."""
    if not CORRECTIONS_FILE.exists():
        return []

    text = CORRECTIONS_FILE.read_text(encoding="utf-8")

    # Remove retired block
    retired_start = text.find("<!-- retired")
    if retired_start != -1:
        text = text[:retired_start]

    corrections = []
    current = {}

    for line in text.split("\n"):
        line = line.strip()

        # New correction entry: - **page / topic**: instruction
        m = re.match(r'^-\s+\*\*(.+?)\s*/\s*(.+?)\*\*:\s*(.+)', line)
        if m:
            if current.get("page"):
                corrections.append(current)
            current = {
                "page": m.group(1).strip(),
                "topic": m.group(2).strip(),
                "instruction": m.group(3).strip(),
            }
            continue

        m = re.match(r'^wrong:\s*["\']?(.+?)["\']?\s*$', line)
        if m and current:
            current["wrong"] = m.group(1).strip()
            continue

        m = re.match(r'^right:\s*["\']?(.+?)["\']?\s*$', line)
        if m and current:
            current["right"] = m.group(1).strip()
            continue

        m = re.match(r'^probe:\s*["\']?(.+?)["\']?\s*$', line)
        if m and current:
            current["probe"] = m.group(1).strip()
            continue

    if current.get("page"):
        corrections.append(current)

    return corrections


def find_page(page_hint):
    """Find a wiki page file by slug or partial name."""
    candidates = list(WIKI.glob(f"**/{page_hint}.md"))
    if candidates:
        return candidates[0]
    for p in WIKI.rglob("*.md"):
        if page_hint.lower() in p.stem.lower():
            return p
    return None


def check_violations(corrections):
    """Return a list of violation records (dicts).

    Each record has: kind, page, page_path, correction, wrong, probe (maybe None),
    right (maybe None), instruction. Multiple kinds may be emitted per correction.
    """
    records = []

    for c in corrections:
        wrong = c.get("wrong")
        if not wrong:
            continue

        page_file = find_page(c["page"])
        if not page_file:
            continue

        content = page_file.read_text(encoding="utf-8").lower()
        wrong_lower = wrong.lower().strip('"\'')
        probe = c.get("probe")
        probe_lower = probe.lower().strip('"\'') if probe else None

        wrong_present = wrong_lower in content
        probe_present = probe_lower in content if probe_lower else None

        base = {
            "page": c["page"],
            "page_path": str(page_file),
            "instruction": c.get("instruction"),
            "wrong": wrong,
            "right": c.get("right"),
            "probe": probe,
        }

        if wrong_present and probe_lower and probe_present:
            # Both coexist — fix is incomplete
            records.append({**base, "kind": "INCOMPLETE_FIX"})
        elif wrong_present:
            records.append({**base, "kind": "WRONG_PRESENT"})
        elif probe_lower and not probe_present:
            # wrong absent, probe specified and absent — the closure case
            records.append({**base, "kind": "MISSING_PROBE"})

    return records


def format_violation(r):
    kind = r["kind"]
    page = r["page_path"]
    if kind == "WRONG_PRESENT":
        return (f"CONSTRAINT VIOLATION: {page} contains \"{r['wrong']}\" "
                f"(correction: use \"{r.get('right', '?')}\" instead)")
    if kind == "MISSING_PROBE":
        return (f"MISSING PROBE: {page} — correction \"{r['instruction']}\" "
                f"probe \"{r['probe']}\" absent (wrong also absent — "
                f"fix may have deleted the content without adding the correction)")
    if kind == "INCOMPLETE_FIX":
        return (f"INCOMPLETE FIX: {page} contains both wrong \"{r['wrong']}\" "
                f"and probe \"{r['probe']}\" — old and new claims coexist")
    return f"{kind}: {page}"


def main():
    json_mode = "--json" in sys.argv

    corrections = parse_corrections()
    records = check_violations(corrections) if corrections else []

    if json_mode:
        import json
        print(json.dumps({"records": records}, indent=2))
        return

    for r in records:
        print(format_violation(r))


if __name__ == "__main__":
    main()
