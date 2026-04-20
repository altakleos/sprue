#!/usr/bin/env python3
"""fix-image-paths.py — rewrite KB-root-relative and ``../raw/assets`` refs
to page-local ``assets/<file>`` form (routed through the ``wiki/assets``
symlink; see ADR-0047).

LLM agents repeatedly emit markdown image references like
``![...](raw/assets/foo.jpg)`` or ``![...](../raw/assets/foo.jpg)``.
Neither form renders in Obsidian: the first is KB-root-relative (Obsidian
resolves from the vault which is ``wiki/``), the second resolves outside
the vault (Obsidian refuses to follow). Both must be rewritten to
``assets/<file>``, which routes through the symlink ``wiki/assets`` →
``../raw/assets`` — this works in Obsidian, GitHub, and VS Code.

The rewriter is:
  - Idempotent (pages already using ``assets/<file>`` are untouched)
  - Depth-invariant (pages at any nesting level under ``wiki/`` use the
    same path form because it's page-relative to the vault root)
  - Strictly scoped to legacy asset prefixes — remote URLs, user-placed
    images, and non-asset paths are left alone

This script is the primary mechanical defense against the recurring
broken-image-path regression. It runs:
  1. At compile Step 11 via the verify.py pre-flight hook
  2. Manually via ``python3 .sprue/scripts/fix-image-paths.py <path>``

``check-images.py`` remains as a safety net for edge cases.

Usage:
  python3 .sprue/scripts/fix-image-paths.py wiki/foo.md
  python3 .sprue/scripts/fix-image-paths.py wiki/cats/bar.md --quiet
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))  # adds src/
from sprue.engine_root import instance_root

ROOT = instance_root()
WIKI = ROOT / "wiki"
ANNOTATIONS_FILE = ROOT / "instance" / "state" / "image-annotations.yaml"
# Match markdown image tags whose path contains a legacy asset prefix:
#   ![alt](raw/assets/foo.jpg)
#   ![alt](../raw/assets/foo.jpg)
#   ![alt](../../raw/assets/foo.jpg)
# The replacement is page-relative to the vault root where the symlink lives:
#   depth 1 (wiki/foo.md)           → assets/foo.jpg
#   depth 2 (wiki/cats/foo.md)      → ../assets/foo.jpg
#   depth N                         → ../ × (N-1) + assets/foo.jpg
# The symlink wiki/assets → ../raw/assets makes every form resolve through
# the vault — Obsidian requires paths to stay inside the vault.
_LEGACY_RE = re.compile(r"(!\[[^\]]*\]\()(?:(?:\.\./)+)?raw/assets/([^)]+)\)")
# Traceability HTML comments (``<!-- original: https://... -->``) are added
# by import Step 5d to the RAW file as a breadcrumb. They should not leak
# into wiki pages — imports.yaml and image-annotations.yaml already carry
# the source URL. Strip the comment (and any trailing blank line) when
# normalizing a wiki page.
_ORIG_COMMENT_RE = re.compile(
    r"[ \t]*<!--\s*original:[^\n]*?-->[ \t]*\n?",
    re.IGNORECASE,
)
# Locate image tags with canonical (assets/...) or ancestor-relative
# (../assets/...) paths for caption injection. Captures:
#   1 = whole image line up to path
#   2 = relative path inside the parens, with leading ../ stripped
#       so we can look up by ``raw/assets/<filename>``
_CANON_IMG_RE = re.compile(
    r"!\[([^\]]*)\]\(((?:\.\./)*assets/([^)]+))\)"
)
# Detect an existing caption line (*Figure N: ...*) so we don't duplicate.
_CAPTION_RE = re.compile(r"^\*Figure\s+\d+:\s", re.IGNORECASE)
# Also catch ``assets/<file>`` from pages nested under wiki/<dir>/ — the
# bare form resolves correctly only for pages directly under wiki/. Pages
# deeper need ``../`` × (depth - 1) to reach the vault-root symlink.
# We flag both legacy and wrongly-rooted canonical refs uniformly.


def _load_annotations_by_filename() -> dict[str, dict]:
    """Return ``{filename: annotation_record}`` keyed by asset basename.

    The annotation's ``raw_path`` is ``raw/assets/<file>``; wiki page refs
    use ``assets/<file>`` (possibly prefixed with ``../``). We key by the
    bare filename so any form of path matches the same asset.

    Empty dict on missing/unreadable file — caption injection degrades
    gracefully.
    """
    if not ANNOTATIONS_FILE.is_file():
        return {}
    try:
        doc = yaml.safe_load(ANNOTATIONS_FILE.read_text(encoding="utf-8")) or []
    except Exception:
        return {}
    if not isinstance(doc, list):
        return {}
    out: dict[str, dict] = {}
    for entry in doc:
        if not isinstance(entry, dict):
            continue
        raw_path = entry.get("raw_path") or ""
        if not raw_path.startswith("raw/assets/"):
            continue
        filename = raw_path.removeprefix("raw/assets/")
        out[filename] = entry
    return out


def _inject_captions(text: str, annotations: dict[str, dict]) -> tuple[str, int]:
    """Inject ``*Figure N: <description>*`` italics beneath each canonical
    image reference whose asset has a non-decorative annotation.

    Skips images that already have a caption directly below (``*Figure ...``).
    Skips decorative/unknown classifications — those shouldn't be in the
    page at all, and adding a caption would dignify a mistake. Skips
    annotations with no ``description`` field.

    Returns ``(new_text, count_of_captions_added)``.
    """
    if not annotations:
        return text, 0

    lines = text.split("\n")
    out_lines: list[str] = []
    count = 0
    figure_num = 0  # page-local counter

    i = 0
    while i < len(lines):
        line = lines[i]
        out_lines.append(line)
        m = _CANON_IMG_RE.match(line.strip())
        if not m:
            i += 1
            continue
        filename = m.group(3)
        ann = annotations.get(filename)
        if not ann:
            i += 1
            continue
        classification = str(ann.get("classification") or "").lower()
        if classification in {"decorative", "unknown"}:
            i += 1
            continue
        description = (ann.get("description") or "").strip()
        if not description:
            i += 1
            continue
        # Look ahead past one blank line to see if a caption already exists.
        j = i + 1
        while j < len(lines) and not lines[j].strip():
            j += 1
        if j < len(lines) and _CAPTION_RE.match(lines[j].strip()):
            i += 1
            continue
        # Inject: blank line (if next isn't already blank) + caption line.
        figure_num += 1
        if i + 1 < len(lines) and lines[i + 1].strip():
            out_lines.append("")
        # Ensure description ends with period for typographic consistency.
        desc = description if description.endswith((".", "?", "!")) else description + "."
        out_lines.append(f"*Figure {figure_num}: {desc}*")
        count += 1
        i += 1

    return "\n".join(out_lines), count


def _rewrite(text: str, prefix: str) -> tuple[str, int, int]:
    """Return (new_text, path_count, comment_count).

    ``prefix`` is ``"../"`` × (page_depth - 1) where ``page_depth`` is the
    page's depth under ``wiki/`` (1 for ``wiki/foo.md``, 2 for
    ``wiki/cats/foo.md``, ...). The rewritten path is ``prefix + assets/<file>``
    which routes through the vault-root symlink.

    Also strips ``<!-- original: ... -->`` HTML comments that leak from
    raw/ into wiki pages. The comment is valuable breadcrumb in raw/ but
    noise in the wiki view; ``imports.yaml`` already carries the mapping.
    """
    path_count = 0

    def sub(m: re.Match) -> str:
        nonlocal path_count
        path_count += 1
        return f"{m.group(1)}{prefix}assets/{m.group(2)})"

    text, comment_count = _ORIG_COMMENT_RE.subn("", text)
    # Collapse any blank-line runs left behind by comment removal so the
    # wiki page stays visually clean. At most one consecutive blank line.
    if comment_count:
        text = re.sub(r"\n{3,}", "\n\n", text)
    new_text = _LEGACY_RE.sub(sub, text)
    return new_text, path_count, comment_count


def fix_page(page: Path) -> tuple[int, int, int]:
    """Normalize image paths, strip stray traceability comments, and inject
    captions from ``image-annotations.yaml``.

    Returns ``(path_count, comment_count, caption_count)``. Any/all may be
    zero. Pages not under ``wiki/`` return ``(0, 0, 0)``.
    """
    try:
        rel = page.resolve().relative_to(WIKI.resolve())
    except ValueError:
        return 0, 0, 0
    depth = len(rel.parts) - 1
    prefix = "../" * depth
    text = page.read_text(encoding="utf-8")
    new_text, path_count, comment_count = _rewrite(text, prefix)
    annotations = _load_annotations_by_filename()
    new_text, caption_count = _inject_captions(new_text, annotations)
    if new_text != text:
        page.write_text(new_text, encoding="utf-8")
    return path_count, comment_count, caption_count


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("path", help="Wiki page to normalize")
    parser.add_argument("--quiet", action="store_true", help="Suppress output")
    args = parser.parse_args()

    page = Path(args.path)
    if not page.is_absolute():
        page = ROOT / page
    if not page.is_file():
        if not args.quiet:
            print(f"⏭️  Not a file: {args.path}")
        return 0  # Not an error — no-op on missing files.

    path_count, comment_count, caption_count = fix_page(page)
    if (path_count or comment_count or caption_count) and not args.quiet:
        try:
            display = page.relative_to(ROOT)
        except ValueError:
            display = page
        edits: list[str] = []
        if path_count:
            edits.append(f"{path_count} image path(s)")
        if comment_count:
            edits.append(f"{comment_count} stray '<!-- original: ... -->' comment(s)")
        if caption_count:
            edits.append(f"{caption_count} caption(s) added")
        print(f"🔧 Fixed {', '.join(edits)} in {display}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
