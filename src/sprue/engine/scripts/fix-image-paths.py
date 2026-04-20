#!/usr/bin/env python3
"""fix-image-paths.py — rewrite KB-root-relative asset paths to page-relative.

LLM agents repeatedly emit markdown image references like
``![...](raw/assets/foo.jpg)`` in wiki pages. Those paths resolve correctly
when the wiki/ tree is served from the KB root, but break in Obsidian, GitHub,
and VS Code markdown preview — all of which resolve image paths relative to
the markdown file itself.

This helper rewrites ``raw/assets/<file>`` references to the correct
page-relative form (``../`` × depth-from-wiki-root + ``raw/assets/<file>``).
It is idempotent: paths that already start with ``../`` or a remote prefix
are left untouched. Only the ``raw/assets/`` prefix is rewritten; other
local paths (user-placed images, non-asset files) are preserved as-is.

This script is the primary mechanical defense against the recurring
broken-image-path regression. It runs:
  1. Automatically at compile Step 10.5 after the agent writes a page
  2. As a pre-flight hook inside ``verify.py`` when called on a wiki page

Both triggers are belt-and-suspenders. ``check-images.py`` remains as a
safety net for edge cases (wrong filenames, fabricated paths, etc.).

Usage:
  python3 .sprue/scripts/fix-image-paths.py wiki/foo.md
  python3 .sprue/scripts/fix-image-paths.py wiki/cats/bar.md --quiet
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))  # adds src/
from sprue.engine_root import instance_root

ROOT = instance_root()
WIKI = ROOT / "wiki"
# Match markdown image with a local path that begins with "raw/assets/".
# Exclude paths that already start with "./", "../", or a remote prefix by
# requiring the first char after "(" to be "r" (not "." or a protocol).
_BAD_RE = re.compile(r"(!\[[^\]]*\]\()(raw/assets/)")


def _rewrite(text: str, prefix: str) -> tuple[str, int]:
    """Return (new_text, count_of_substitutions).

    ``prefix`` is ``"../"`` * (depth of page under wiki/). We insert it
    between ``(`` and ``raw/assets/`` to produce a page-relative path.
    """
    count = 0

    def sub(m: re.Match) -> str:
        nonlocal count
        count += 1
        return f"{m.group(1)}{prefix}{m.group(2)}"

    return _BAD_RE.sub(sub, text), count


def fix_page(page: Path) -> int:
    """Rewrite KB-root-relative asset paths in *page* to page-relative form.

    Returns the number of paths rewritten. 0 means either no images, all
    images already correct, or the page is not under ``wiki/``.
    """
    try:
        rel = page.resolve().relative_to(WIKI.resolve())
    except ValueError:
        return 0  # Not a wiki page.
    depth = len(rel.parts) - 1  # parts include the filename itself
    prefix = "../" * (depth + 1)  # +1 to escape the wiki/ directory itself
    text = page.read_text(encoding="utf-8")
    new_text, count = _rewrite(text, prefix)
    if count and new_text != text:
        page.write_text(new_text, encoding="utf-8")
    return count


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

    count = fix_page(page)
    if count and not args.quiet:
        try:
            display = page.relative_to(ROOT)
        except ValueError:
            display = page
        print(f"🔧 Fixed {count} image path(s) in {display}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
