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

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import SKIP_FILES, find_wiki_pages

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))  # adds src/
from sprue.engine_root import instance_root

WIKI = instance_root() / "wiki"
ROOT = instance_root()
ANNOTATIONS = ROOT / "instance" / "state" / "image-annotations.yaml"
_IMG_RE = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")
_REMOTE_PREFIXES = ("http://", "https://", "data:")
_DECORATIVE_CLASSIFICATIONS = {"decorative", "unknown"}


_ISSUE_LABELS = {
    "missing_file": "missing file",
    "empty_alt": "empty alt text",
    "kb_root_relative": "KB-root-relative path — rewrite to 'assets/<file>' (run .sprue/scripts/fix-image-paths.py)",
    "parent_escape_legacy": "legacy '../raw/assets/' path — rewrite to 'assets/<file>' (run .sprue/scripts/fix-image-paths.py)",
    "not_annotated": "referenced image has no annotation in image-annotations.yaml — run compile Step 4 (Triage)",
    "decorative_referenced": "referenced image is classified decorative/unknown in image-annotations.yaml — do not place it in wiki pages",
}


def _load_annotations() -> dict[str, str]:
    """Return mapping: raw/assets/<file> → classification (e.g. 'diagram')."""
    if not ANNOTATIONS.is_file():
        return {}
    doc = yaml.safe_load(ANNOTATIONS.read_text(encoding="utf-8")) or []
    if not isinstance(doc, list):
        return {}
    out: dict[str, str] = {}
    for entry in doc:
        if not isinstance(entry, dict):
            continue
        raw_path = entry.get("raw_path")
        classification = entry.get("classification") or ""
        if raw_path:
            out[raw_path] = classification
    return out


def _pages_to_check() -> list[Path]:
    """Use CONTENT_PAGES env var when set (verify --file scope), else whole wiki."""
    env = os.environ.get("CONTENT_PAGES", "")
    if env and Path(env).is_file():
        paths = [line.strip() for line in Path(env).read_text().splitlines() if line.strip()]
        return [ROOT / p for p in paths if p.endswith(".md")]
    if not WIKI.is_dir():
        return []
    return list(find_wiki_pages(WIKI))


def _violations_for(page: Path, annotations: dict[str, str]) -> list[dict]:
    """Return violation records for image references in *page*.

    Image paths in wiki pages must be relative to the page's directory so
    they render in standard markdown viewers (Obsidian, GitHub, VS Code).
    KB-root-relative paths like ``raw/assets/foo.jpg`` appear valid when
    resolved from ROOT but break in viewers — flag them explicitly.

    When the image resolves to a file under ``raw/assets/``, also verify
    it has a non-decorative annotation in ``image-annotations.yaml``.
    References to un-triaged or decorative images indicate the LLM
    fabricated a reference or picked an image that triage excluded.
    """
    text = page.read_text(encoding="utf-8")
    slug = str(page.relative_to(WIKI)).removesuffix(".md")
    violations: list[dict] = []
    for alt, ref in _IMG_RE.findall(text):
        if ref.startswith(_REMOTE_PREFIXES):
            continue
        # Paths MUST resolve through the page's directory or the wiki/assets
        # symlink. ``assets/<file>`` is the canonical form (ADR-0047).
        # Detect legacy ``../raw/assets/`` form even when the file exists on
        # disk — Obsidian rejects paths that escape the vault.
        stripped = ref.lstrip("./")
        if "raw/assets/" in ref and stripped.startswith("../"):
            violations.append({"page": slug, "path": ref, "issue": "parent_escape_legacy"})
            continue
        page_relative = page.parent / ref
        if not page_relative.is_file():
            if ref.startswith("raw/assets/") and (ROOT / ref).is_file():
                issue = "kb_root_relative"
            else:
                issue = "missing_file"
            violations.append({"page": slug, "path": ref, "issue": issue})
            continue
        if not alt.strip():
            violations.append({"page": slug, "path": ref, "issue": "empty_alt"})
            continue
        # Canonicalize to a ``raw/assets/<file>`` form for annotation lookup.
        try:
            rel = page_relative.resolve().relative_to(ROOT.resolve())
        except ValueError:
            continue
        rel_str = str(rel).replace(os.sep, "/")
        if not rel_str.startswith("raw/assets/"):
            continue  # Non-asset images (e.g., user-dropped) not triage-gated.
        if annotations:
            classification = annotations.get(rel_str)
            if classification is None:
                violations.append({"page": slug, "path": ref, "issue": "not_annotated"})
            elif classification in _DECORATIVE_CLASSIFICATIONS:
                violations.append({"page": slug, "path": ref, "issue": "decorative_referenced"})
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
    annotations = _load_annotations()
    for page in _pages_to_check():
        slug = str(page.relative_to(WIKI)).removesuffix(".md")
        page_v = _violations_for(page, annotations)
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
