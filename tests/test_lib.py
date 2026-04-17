"""Tests for sprue.engine.scripts.lib shared helpers.

The lib module is imported via sys.path manipulation by scripts, but tests
load it directly via importlib to avoid filesystem gymnastics.
"""
import importlib.util
from pathlib import Path

import pytest

_LIB_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "sprue"
    / "engine"
    / "scripts"
    / "lib.py"
)


@pytest.fixture(scope="module")
def lib():
    spec = importlib.util.spec_from_file_location("sprue_engine_lib", _LIB_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_skip_dirs_is_union(lib):
    """Union must include sources to fix the drift."""
    assert lib.SKIP_DIRS == {".obsidian", ".index", "domains", "sources"}


def test_skip_files_canonical(lib):
    assert lib.SKIP_FILES == {"index.md", "overview.md"}


def test_parse_frontmatter_happy_path(lib, tmp_path):
    p = tmp_path / "page.md"
    p.write_text("---\ntitle: Foo\ntags: [a, b]\n---\n# Heading\nBody text.\n")
    fm, body = lib.parse_frontmatter(p)
    assert fm == {"title": "Foo", "tags": ["a", "b"]}
    assert body.strip().startswith("# Heading")


def test_parse_frontmatter_no_frontmatter(lib, tmp_path):
    p = tmp_path / "page.md"
    p.write_text("# Just a heading\nNo frontmatter here.\n")
    fm, body = lib.parse_frontmatter(p)
    assert fm == {}
    assert "Just a heading" in body


def test_parse_frontmatter_invalid_yaml(lib, tmp_path):
    p = tmp_path / "page.md"
    p.write_text("---\n: bad: yaml: nesting\n---\nBody\n")
    fm, body = lib.parse_frontmatter(p)
    assert fm == {}
    assert "Body" in body


def test_find_wiki_pages_skips_dirs_and_files(lib, tmp_path):
    (tmp_path / "keep.md").write_text("keep")
    (tmp_path / "overview.md").write_text("skip")
    (tmp_path / "index.md").write_text("skip")
    (tmp_path / "sources").mkdir()
    (tmp_path / "sources" / "inside.md").write_text("skip")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "nested.md").write_text("keep")
    (tmp_path / "notes.txt").write_text("non-md")

    pages = lib.find_wiki_pages(tmp_path)
    names = sorted(p.name for p in pages)
    assert names == ["keep.md", "nested.md"]


def test_find_wiki_pages_empty_dir(lib, tmp_path):
    assert lib.find_wiki_pages(tmp_path) == []


def test_normalize_relationship_types_list_form(lib):
    raw = [
        {"name": "deps_on", "display": "depends on"},
        {"name": "supersedes", "display": "supersedes"},
        "not a dict",  # dropped
        {"no_name_key": 1},  # dropped
    ]
    result = lib.normalize_relationship_types(raw)
    assert set(result.keys()) == {"deps_on", "supersedes"}
    assert result["deps_on"]["display"] == "depends on"


def test_normalize_relationship_types_dict_form(lib):
    raw = {"deps_on": {"display": "depends on"}}
    assert lib.normalize_relationship_types(raw) == raw


def test_normalize_relationship_types_none_or_other(lib):
    assert lib.normalize_relationship_types(None) == {}
    assert lib.normalize_relationship_types(42) == {}
