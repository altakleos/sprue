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

    # Adapt fix_page signature for existing tests that assert an int: the
    # helper returns just the image-path count, matching the pre-0.1.33
    # API. New tests that care about all counts call module.fix_page
    # directly and unpack the tuple.
    original_fix = module.fix_page

    def _path_count_only(page):
        p, _c, _cap = original_fix(page)
        return p

    module.fix_page = _path_count_only
    module.fix_page_full = original_fix
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


# ---- Comment stripping (leaked <!-- original: ... --> tags) ----


def test_strips_original_comment_alone(fixer, tmp_path):
    """A page with only a leaked traceability comment gets it stripped."""
    page = tmp_path / "wiki" / "foo.md"
    page.write_text(
        "![A cat](assets/x.jpg)\n"
        "<!-- original: https://example.com/cat.jpg -->\n"
    )
    paths, comments, captions = fixer.fix_page_full(page)
    assert paths == 0
    assert comments == 1
    text = page.read_text()
    assert "<!-- original:" not in text
    assert "![A cat](assets/x.jpg)" in text


def test_strips_multiple_original_comments(fixer, tmp_path):
    page = tmp_path / "wiki" / "multi.md"
    page.write_text(
        "![a](assets/a.jpg)\n"
        "<!-- original: https://e.com/a.jpg -->\n\n"
        "Some text.\n\n"
        "![b](assets/b.jpg)\n"
        "<!-- original: https://e.com/b.jpg -->\n"
    )
    paths, comments, captions = fixer.fix_page_full(page)
    assert comments == 2
    assert "<!-- original:" not in page.read_text()


def test_strips_comment_and_rewrites_path_together(fixer, tmp_path):
    """Comment stripping + path rewriting in one pass."""
    page = tmp_path / "wiki" / "mixed.md"
    page.write_text(
        "![a](raw/assets/a.jpg)\n"
        "<!-- original: https://e.com/a.jpg -->\n"
    )
    paths, comments, captions = fixer.fix_page_full(page)
    assert paths == 1
    assert comments == 1
    text = page.read_text()
    assert "![a](assets/a.jpg)" in text
    assert "<!-- original:" not in text


def test_comment_stripping_idempotent(fixer, tmp_path):
    page = tmp_path / "wiki" / "foo.md"
    page.write_text(
        "![a](assets/x.jpg)\n"
        "<!-- original: https://example.com/x.jpg -->\n"
    )
    assert fixer.fix_page_full(page) == (0, 1, 0)
    # Second pass: nothing left to strip.
    assert fixer.fix_page_full(page) == (0, 0, 0)


def test_unrelated_html_comments_untouched(fixer, tmp_path):
    """Only ``<!-- original: ... -->`` is stripped. Other comments stay."""
    page = tmp_path / "wiki" / "foo.md"
    original = (
        "<!-- TODO: add example -->\n"
        "![a](assets/x.jpg)\n"
        "<!-- FIXME: broken link -->\n"
    )
    page.write_text(original)
    paths, comments, captions = fixer.fix_page_full(page)
    assert paths == 0
    assert comments == 0
    assert page.read_text() == original



# ---- Caption injection from image-annotations.yaml ----


def _write_annotations(tmp_path: Path, entries: list[dict]) -> None:
    import yaml
    (tmp_path / "instance" / "state").mkdir(parents=True, exist_ok=True)
    path = tmp_path / "instance" / "state" / "image-annotations.yaml"
    path.write_text(yaml.safe_dump(entries, sort_keys=False))


def test_caption_injected_when_annotation_present(fixer, tmp_path):
    _write_annotations(tmp_path, [
        {"raw_path": "raw/assets/x.jpg", "classification": "informative",
         "description": "A ragdoll kitten resting"},
    ])
    page = tmp_path / "wiki" / "foo.md"
    page.write_text("![A kitten](assets/x.jpg)\n\nMore text.\n")
    paths, comments, captions = fixer.fix_page_full(page)
    assert captions == 1
    text = page.read_text()
    assert "*Figure 1: A ragdoll kitten resting.*" in text
    idx_img = text.index("![A kitten]")
    idx_cap = text.index("*Figure 1:")
    assert idx_img < idx_cap


def test_caption_numbering_increments(fixer, tmp_path):
    _write_annotations(tmp_path, [
        {"raw_path": "raw/assets/a.jpg", "classification": "informative",
         "description": "First image"},
        {"raw_path": "raw/assets/b.jpg", "classification": "informative",
         "description": "Second image"},
    ])
    page = tmp_path / "wiki" / "foo.md"
    page.write_text("![A](assets/a.jpg)\n\n![B](assets/b.jpg)\n")
    _, _, captions = fixer.fix_page_full(page)
    assert captions == 2
    text = page.read_text()
    assert "*Figure 1: First image.*" in text
    assert "*Figure 2: Second image.*" in text


def test_caption_skipped_for_decorative(fixer, tmp_path):
    _write_annotations(tmp_path, [
        {"raw_path": "raw/assets/d.jpg", "classification": "decorative",
         "description": "A divider"},
    ])
    page = tmp_path / "wiki" / "foo.md"
    page.write_text("![](assets/d.jpg)\n")
    _, _, captions = fixer.fix_page_full(page)
    assert captions == 0
    assert "*Figure" not in page.read_text()


def test_caption_skipped_when_no_annotation(fixer, tmp_path):
    _write_annotations(tmp_path, [])
    page = tmp_path / "wiki" / "foo.md"
    page.write_text("![A](assets/orphan.jpg)\n")
    _, _, captions = fixer.fix_page_full(page)
    assert captions == 0


def test_caption_idempotent_when_already_present(fixer, tmp_path):
    _write_annotations(tmp_path, [
        {"raw_path": "raw/assets/x.jpg", "classification": "informative",
         "description": "A kitten"},
    ])
    page = tmp_path / "wiki" / "foo.md"
    page.write_text("![A kitten](assets/x.jpg)\n\n*Figure 1: A kitten.*\n")
    _, _, captions = fixer.fix_page_full(page)
    assert captions == 0


def test_caption_works_for_nested_page(fixer, tmp_path):
    _write_annotations(tmp_path, [
        {"raw_path": "raw/assets/x.jpg", "classification": "informative",
         "description": "A nested image"},
    ])
    subdir = tmp_path / "wiki" / "cats"
    subdir.mkdir()
    page = subdir / "ragdoll.md"
    page.write_text("![](../assets/x.jpg)\n")
    _, _, captions = fixer.fix_page_full(page)
    assert captions == 1
    assert "*Figure 1: A nested image.*" in page.read_text()
