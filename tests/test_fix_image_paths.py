"""Tests for the mechanical image path fixer.

``fix-image-paths.py`` rewrites legacy asset references (``raw/assets/...``,
``../raw/assets/...``, ``../../raw/assets/...``) to the canonical page-local
form ``assets/<file>`` which routes through the ``wiki/assets`` symlink
(see ADR-0047). The rewrite is idempotent, depth-invariant, and strictly
scoped to the ``raw/assets/`` prefix family.
"""
import importlib.util
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
    er_mod._clear_cache()


def test_kb_root_relative_rewrite(fixer, tmp_path):
    """Depth-1 page: ``raw/assets/x.jpg`` → ``assets/x.jpg``."""
    page = tmp_path / "wiki" / "foo.md"
    page.write_text("# Foo\n\n![alt](raw/assets/x.jpg)\n")
    assert fixer.fix_page(page) == 1
    assert "![alt](assets/x.jpg)" in page.read_text()


def test_parent_escape_single_rewrite(fixer, tmp_path):
    """Depth-1 page: legacy ``../raw/assets/`` → ``assets/``."""
    page = tmp_path / "wiki" / "foo.md"
    page.write_text("![alt](../raw/assets/x.jpg)\n")
    assert fixer.fix_page(page) == 1
    assert "![alt](assets/x.jpg)" in page.read_text()


def test_parent_escape_double_rewrite(fixer, tmp_path):
    """Depth-2 page: legacy ``../../raw/assets/`` → ``../assets/``.

    Nested pages must hop up one level to reach the vault-root symlink.
    """
    subdir = tmp_path / "wiki" / "cats"
    subdir.mkdir()
    page = subdir / "bar.md"
    page.write_text("![alt](../../raw/assets/y.png)\n")
    assert fixer.fix_page(page) == 1
    assert "![alt](../assets/y.png)" in page.read_text()


def test_deeply_nested_page_rewrite(fixer, tmp_path):
    """Depth-3 page: ``../../../raw/assets/`` → ``../../assets/``."""
    subdir = tmp_path / "wiki" / "cats" / "breeds"
    subdir.mkdir(parents=True)
    page = subdir / "ragdoll.md"
    page.write_text("![alt](../../../raw/assets/r.jpg)\n")
    assert fixer.fix_page(page) == 1
    assert "![alt](../../assets/r.jpg)" in page.read_text()


def test_canonical_form_untouched(fixer, tmp_path):
    page = tmp_path / "wiki" / "good.md"
    original = "# Good\n\n![alt](assets/x.jpg)\n"
    page.write_text(original)
    assert fixer.fix_page(page) == 0
    assert page.read_text() == original


def test_remote_urls_untouched(fixer, tmp_path):
    page = tmp_path / "wiki" / "remote.md"
    original = "![alt](https://example.com/foo.jpg)\n![alt](http://x.com/y.png)\n"
    page.write_text(original)
    assert fixer.fix_page(page) == 0
    assert page.read_text() == original


def test_non_asset_paths_untouched(fixer, tmp_path):
    """Images in other dirs (user-placed, non-asset) are left alone."""
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
    assert fixer.fix_page(page) == 0
    assert page.read_text() == after_first


def test_mixed_page(fixer, tmp_path):
    """Each legacy form is rewritten; canonical and remote refs stay."""
    page = tmp_path / "wiki" / "mixed.md"
    page.write_text(
        "# Mixed\n\n"
        "![a](assets/a.png)\n"              # already canonical
        "![b](raw/assets/b.png)\n"          # KB-root legacy
        "![c](../raw/assets/c.png)\n"       # parent-escape depth 1
        "![d](../../raw/assets/d.png)\n"    # parent-escape depth 2
        "![e](https://example.com/e.gif)\n" # remote
        "![f](diagrams/flow.svg)\n"         # user-placed
    )
    assert fixer.fix_page(page) == 3
    text = page.read_text()
    assert "![a](assets/a.png)" in text
    assert "![b](assets/b.png)" in text
    assert "![c](assets/c.png)" in text
    assert "![d](assets/d.png)" in text
    assert "![e](https://example.com/e.gif)" in text
    assert "![f](diagrams/flow.svg)" in text


def test_non_wiki_page_noop(fixer, tmp_path):
    """Pages outside wiki/ are skipped regardless of content."""
    page = tmp_path / "notebook" / "scratch.md"
    page.parent.mkdir()
    original = "![alt](raw/assets/x.jpg)\n"
    page.write_text(original)
    assert fixer.fix_page(page) == 0
    assert page.read_text() == original
