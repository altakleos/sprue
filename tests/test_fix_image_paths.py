"""Tests for the mechanical image path fixer.

``fix-image-paths.py`` rewrites KB-root-relative asset references in wiki
pages to page-relative form. Its job is to be idempotent, depth-aware, and
strictly scoped to ``raw/assets/`` paths — without touching anything else.
"""
import importlib.util
import os
import sys
from pathlib import Path

import pytest


_SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "sprue"
    / "engine"
    / "scripts"
    / "fix-image-paths.py"
)


@pytest.fixture
def fixer(monkeypatch, tmp_path):
    """Load the script as a module, pointing instance_root at tmp_path."""
    src = Path(__file__).resolve().parents[1] / "src"
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))
    monkeypatch.setenv("SPRUE_INSTANCE_ROOT", str(tmp_path))
    # Clear the memoized instance_root() so this test sees tmp_path.
    from sprue import engine_root as er_mod  # type: ignore
    er_mod._clear_cache()
    (tmp_path / "wiki").mkdir()
    (tmp_path / "raw" / "assets").mkdir(parents=True)
    (tmp_path / "raw" / "assets" / "x.jpg").write_text("fake")
    (tmp_path / "raw" / "assets" / "y.png").write_text("fake")

    spec = importlib.util.spec_from_file_location("fix_image_paths", _SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    yield module
    # Clear cache again so subsequent tests/fixtures aren't polluted.
    er_mod._clear_cache()


def test_depth_1_rewrite(fixer, tmp_path):
    page = tmp_path / "wiki" / "foo.md"
    page.write_text("# Foo\n\n![alt](raw/assets/x.jpg)\n")
    count = fixer.fix_page(page)
    assert count == 1
    assert "![alt](../raw/assets/x.jpg)" in page.read_text()


def test_depth_2_rewrite(fixer, tmp_path):
    subdir = tmp_path / "wiki" / "cats"
    subdir.mkdir()
    page = subdir / "bar.md"
    page.write_text("# Bar\n\n![alt](raw/assets/y.png)\n")
    count = fixer.fix_page(page)
    assert count == 1
    assert "![alt](../../raw/assets/y.png)" in page.read_text()


def test_already_correct_untouched(fixer, tmp_path):
    page = tmp_path / "wiki" / "good.md"
    original = "# Good\n\n![alt](../raw/assets/x.jpg)\n"
    page.write_text(original)
    count = fixer.fix_page(page)
    assert count == 0
    assert page.read_text() == original


def test_remote_urls_untouched(fixer, tmp_path):
    page = tmp_path / "wiki" / "remote.md"
    original = "![alt](https://example.com/foo.jpg)\n![alt](http://x.com/y.png)\n"
    page.write_text(original)
    assert fixer.fix_page(page) == 0
    assert page.read_text() == original


def test_non_asset_paths_untouched(fixer, tmp_path):
    page = tmp_path / "wiki" / "other.md"
    original = "![alt](images/foo.jpg)\n![alt](./local.png)\n"
    page.write_text(original)
    assert fixer.fix_page(page) == 0
    assert page.read_text() == original


def test_idempotent(fixer, tmp_path):
    page = tmp_path / "wiki" / "foo.md"
    page.write_text("![alt](raw/assets/x.jpg)\n")
    assert fixer.fix_page(page) == 1
    after_first = page.read_text()
    # Second pass must be a no-op — the path now starts with "../"
    assert fixer.fix_page(page) == 0
    assert page.read_text() == after_first


def test_mixed_page(fixer, tmp_path):
    """Only the bad reference is rewritten; other refs are preserved."""
    page = tmp_path / "wiki" / "mixed.md"
    page.write_text(
        "# Mixed\n\n"
        "![good](../raw/assets/y.png)\n"
        "![bad](raw/assets/x.jpg)\n"
        "![remote](https://example.com/z.gif)\n"
        "![other](diagrams/flow.svg)\n"
    )
    assert fixer.fix_page(page) == 1
    text = page.read_text()
    assert "![good](../raw/assets/y.png)" in text
    assert "![bad](../raw/assets/x.jpg)" in text
    assert "![remote](https://example.com/z.gif)" in text
    assert "![other](diagrams/flow.svg)" in text


def test_non_wiki_page_noop(fixer, tmp_path):
    """Pages outside wiki/ are skipped regardless of content."""
    page = tmp_path / "notebook" / "scratch.md"
    page.parent.mkdir()
    original = "![alt](raw/assets/x.jpg)\n"
    page.write_text(original)
    assert fixer.fix_page(page) == 0
    assert page.read_text() == original
