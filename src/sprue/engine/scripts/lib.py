"""Shared utilities for engine scripts.

Consolidates helpers that were duplicated across 9 scripts in
``src/sprue/engine/scripts/``. Addresses the ``SKIP_DIRS`` drift bug where
different scripts saw different page sets.

Scope is deliberately conservative: only variants with matching signatures
are extracted here. Scripts that return divergent types (e.g. a set of slugs
rather than a list of paths, or manifest-based iteration with filters) keep
their local implementation. See
``docs/plans/shared-utils-refactor.md`` for the full migration scope.

Import pattern (scripts are invoked standalone, not as a package):

    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from lib import SKIP_DIRS, SKIP_FILES, parse_frontmatter, find_wiki_pages
"""
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Union

import yaml

# Directories that engine scripts never walk into.
# Union of all variants found in the scripts directory. `sources` was omitted
# from check-frontmatter.py and verify.py historically — this is the silent
# drift that caused different scripts to see different page sets.
SKIP_DIRS: set[str] = {".obsidian", ".index", "domains", "sources"}

# Files engine scripts skip when walking wiki pages.
# Both are auto-generated index pages that should not be verified as content.
SKIP_FILES: set[str] = {"index.md", "overview.md"}

_FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---", re.DOTALL)


def parse_frontmatter(path: Path) -> tuple[dict, str]:
    """Extract YAML frontmatter from a markdown file.

    Returns ``(frontmatter_dict, body_text)``. On missing or invalid
    frontmatter, returns ``({}, full_text)`` — callers avoid ``None`` checks.
    """
    text = path.read_text(encoding="utf-8")
    m = _FRONTMATTER_RE.match(text)
    if not m:
        return {}, text
    try:
        fm = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError:
        fm = {}
    body = text[m.end():]
    return fm, body


def find_wiki_pages(wiki_dir: Path) -> list[Path]:
    """Walk ``wiki_dir`` returning sorted list of content page paths.

    Skips directories in ``SKIP_DIRS`` and files in ``SKIP_FILES``. Only
    returns files ending in ``.md``.
    """
    pages: list[Path] = []
    for root, dirs, files in os.walk(wiki_dir):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in files:
            if f.endswith(".md") and f not in SKIP_FILES:
                pages.append(Path(root) / f)
    return sorted(pages)


def normalize_relationship_types(
    raw: Union[list, dict, None],
) -> dict[str, dict]:
    """Normalize ``relationship_types`` from ``entity-types.yaml``.

    Accepts either a list-of-dicts (each having a ``name`` key) or a
    dict-of-dicts (slug → config). Returns ``dict[slug, config]``. Returns
    ``{}`` for ``None`` or unexpected types — defensive for missing config.
    """
    if raw is None:
        return {}
    if isinstance(raw, list):
        return {
            item["name"]: item
            for item in raw
            if isinstance(item, dict) and "name" in item
        }
    return raw if isinstance(raw, dict) else {}
