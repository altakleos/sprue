#!/usr/bin/env python3
"""check-triage-done.py — ensure image triage ran for sources with captured assets.

For each source in ``imports.yaml`` with a non-empty ``assets`` list, every
asset must have a corresponding entry in ``instance/state/image-annotations.yaml``
keyed by ``content_hash``. Missing annotations mean compile Step 4 (Triage
images) was skipped for that source — the LLM did not classify or describe
the captured images, so downstream page generation has nothing to work with.

This validator does NOT require the wiki page to *use* the images — that is
a judgment the LLM makes during compile. It only enforces that triage
itself happened. Whether any image makes it into the wiki page is the
LLM's call.

Respects ``CONTENT_PAGES`` env var for --file scope. Iterates imports.yaml
entries; filters to those whose ``raw`` matches a page's frontmatter source.

Usage:
  python3 .sprue/scripts/check-triage-done.py          # human
  python3 .sprue/scripts/check-triage-done.py --quiet  # exit code only
  python3 .sprue/scripts/check-triage-done.py --json   # structured
"""
from __future__ import annotations

import argparse
import json as jsonlib
import os
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import parse_frontmatter

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))  # adds src/
from sprue.engine_root import instance_root

ROOT = instance_root()
WIKI = ROOT / "wiki"
IMPORTS = ROOT / "instance" / "state" / "imports.yaml"
ANNOTATIONS = ROOT / "instance" / "state" / "image-annotations.yaml"


def _load_imports() -> list[dict]:
    if not IMPORTS.is_file():
        return []
    doc = yaml.safe_load(IMPORTS.read_text(encoding="utf-8")) or []
    return doc if isinstance(doc, list) else []


def _load_annotation_hashes() -> set[str]:
    if not ANNOTATIONS.is_file():
        return set()
    doc = yaml.safe_load(ANNOTATIONS.read_text(encoding="utf-8")) or []
    if not isinstance(doc, list):
        return set()
    return {e.get("content_hash") for e in doc if isinstance(e, dict) and e.get("content_hash")}


def _pages_to_check() -> list[Path]:
    env = os.environ.get("CONTENT_PAGES", "")
    if env and Path(env).is_file():
        paths = [line.strip() for line in Path(env).read_text().splitlines() if line.strip()]
        return [ROOT / p for p in paths if p.endswith(".md")]
    if not WIKI.is_dir():
        return []
    return sorted(p for p in WIKI.rglob("*.md") if p.is_file())


def _violations_for(
    page: Path,
    imports_by_raw: dict[str, dict],
    annotated_hashes: set[str],
) -> list[dict]:
    try:
        fm, _body = parse_frontmatter(page)
    except Exception:
        return []
    sources = fm.get("sources") or []
    if not isinstance(sources, list):
        return []
    violations: list[dict] = []
    slug = str(page.relative_to(WIKI)).removesuffix(".md")
    for src in sources:
        if not isinstance(src, dict):
            continue
        raw = src.get("raw")
        entry = imports_by_raw.get(raw)
        if not entry:
            continue
        assets = entry.get("assets") or []
        if not isinstance(assets, list):
            continue
        missing = []
        for asset in assets:
            if not isinstance(asset, dict):
                continue
            ch = asset.get("content_hash")
            if ch and ch not in annotated_hashes:
                missing.append(asset.get("local_path") or ch)
        if missing:
            violations.append({
                "page": slug,
                "raw": raw,
                "missing_count": len(missing),
                "total_assets": len(assets),
            })
    return violations


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--quiet", action="store_true", help="Exit code only")
    parser.add_argument("--json", action="store_true", help="JSON output")
    args = parser.parse_args()

    imports_doc = _load_imports()
    if not imports_doc:
        if args.json:
            print(jsonlib.dumps({"violations": []}))
        elif not args.quiet:
            print("⏭️  No imports recorded — nothing to check.")
        return 0

    imports_by_raw = {e.get("raw"): e for e in imports_doc if isinstance(e, dict) and e.get("raw")}
    annotated_hashes = _load_annotation_hashes()

    violations: list[dict] = []
    for page in _pages_to_check():
        violations.extend(_violations_for(page, imports_by_raw, annotated_hashes))

    if args.json:
        print(jsonlib.dumps({"violations": violations}, indent=2))
    elif violations:
        for v in violations:
            print(
                f"Page: {v['page']}  ✖ source has {v['total_assets']} captured image(s) "
                f"but {v['missing_count']} have no annotation in image-annotations.yaml. "
                f"Run compile Step 4 (Triage images) to classify them."
            )
    elif not args.quiet:
        print("✅ Triage check passed — all captured assets have annotations.")

    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main())
