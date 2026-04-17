#!/usr/bin/env python3
"""Type-purity guard — no wiki directory may be dominated by a single `type:` value.

The filesystem is pure navigation; classification is pure data. A directory
whose pages are >= N% a single type is a type-based folder in disguise (the
anti-pattern the Phase 1 directory migration was meant to eliminate). This
guard fires whenever that pattern emerges so the LLM re-places pages by
domain judgment per .sprue/protocols/compile.md step 7.

Threshold + allowlist live in instance/config.yaml under `placement:`.
Platform-agnostic — no directory names are hardcoded here.

Exit 0 on clean, 1 if any directory violates.
"""

import os
import re
import sys
from collections import Counter
from pathlib import Path

# T11: Route engine/instance paths through resolvers.
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))  # adds src/
from sprue.engine_root import instance_root

ROOT = instance_root()
WIKI = instance_root() / "wiki"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import load as load_config

FM_RE = re.compile(r"^---\n(.*?)\n---", re.DOTALL)
TYPE_RE = re.compile(r"^type:\s*(\S+)", re.MULTILINE)


def _load_placement_config():
    cfg = load_config()
    p = cfg.get("placement", {}) or {}
    threshold = float(p.get("single_type_threshold", 95))
    allowlist = set(p.get("allowlist", []) or [])
    return threshold, allowlist


def page_type(path: Path) -> str:
    text = path.read_text(encoding="utf-8", errors="replace")
    m = FM_RE.match(text)
    if not m:
        return ""
    t = TYPE_RE.search(m.group(1))
    return t.group(1).strip() if t else ""


def directory_key(path: Path) -> str:
    """Return the directory path relative to the repo root (e.g. 'wiki/cloud')."""
    return str(path.parent.relative_to(ROOT))


def main() -> int:
    threshold, allowlist = _load_placement_config()

    # Group content pages by parent directory.
    by_dir: dict[str, list[Path]] = {}
    for p in WIKI.rglob("*.md"):
        if "/.index/" in str(p):
            continue
        if p.name in ("overview.md", "index.md"):
            continue
        by_dir.setdefault(directory_key(p), []).append(p)

    violations = []
    for d, pages in sorted(by_dir.items()):
        if d in allowlist:
            continue
        if len(pages) < 3:
            # too small to have a meaningful type distribution
            continue
        types = Counter(page_type(p) for p in pages if page_type(p))
        if not types:
            continue
        dominant_type, dominant_count = types.most_common(1)[0]
        pct = 100.0 * dominant_count / len(pages)
        if pct >= threshold:
            violations.append((d, len(pages), dominant_type, pct, types))

    if not violations:
        return 0

    for d, n, t, pct, types in violations:
        print(f"PLACEMENT VIOLATION: {d} ({n} pages, {pct:.0f}% type:{t})")
        type_summary = ", ".join(f"{k}={v}" for k, v in types.most_common())
        print(f"  types: {type_summary}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
