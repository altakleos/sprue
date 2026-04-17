"""Tests for check-sources.py validator (ADR-0028).

Invokes the script via subprocess with SPRUE_INSTANCE_ROOT pointed at
temp fixtures — keeps each test in its own sandbox.
"""
import subprocess
import sys
from pathlib import Path

import pytest

_SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "sprue"
    / "engine"
    / "scripts"
    / "check-sources.py"
)


def _make_page(wiki: Path, name: str, frontmatter: str) -> Path:
    """Write a wiki page with the given frontmatter block + stub body."""
    wiki.mkdir(exist_ok=True)
    p = wiki / name
    p.write_text(f"---\n{frontmatter}\n---\n# {name}\nBody.\n", encoding="utf-8")
    return p


def _run(instance_root: Path, *args: str) -> subprocess.CompletedProcess:
    """Run check-sources.py with instance_root injected via env var."""
    return subprocess.run(
        [sys.executable, str(_SCRIPT), *args],
        env={
            "SPRUE_INSTANCE_ROOT": str(instance_root),
            "PYTHONPATH": str(Path(__file__).resolve().parents[1] / "src"),
            "PATH": "/usr/bin:/bin",
        },
        capture_output=True,
        text=True,
    )


def test_passes_when_sourced_page_has_sources(tmp_path):
    wiki = tmp_path / "wiki"
    _make_page(
        wiki,
        "good.md",
        "author: llm\nprovenance: sourced\nsources:\n  - raw: raw/x.md\n    url: https://x",
    )
    r = _run(tmp_path)
    assert r.returncode == 0, r.stderr


def test_flags_sourced_page_missing_sources(tmp_path):
    wiki = tmp_path / "wiki"
    _make_page(wiki, "bad.md", "author: llm\nprovenance: sourced")
    r = _run(tmp_path)
    assert r.returncode == 1
    assert "sources_missing" in r.stderr
    assert "bad.md" in r.stderr


def test_flags_sourced_page_with_empty_sources(tmp_path):
    wiki = tmp_path / "wiki"
    _make_page(
        wiki, "empty.md", "author: llm\nprovenance: sourced\nsources: []"
    )
    r = _run(tmp_path)
    assert r.returncode == 1
    assert "empty.md" in r.stderr


def test_ignores_synthesized_pages(tmp_path):
    wiki = tmp_path / "wiki"
    _make_page(wiki, "synth.md", "author: llm\nprovenance: synthesized")
    r = _run(tmp_path)
    assert r.returncode == 0, r.stderr


def test_ignores_human_authored_pages(tmp_path):
    wiki = tmp_path / "wiki"
    _make_page(wiki, "human.md", "author: human\nprovenance: sourced")
    r = _run(tmp_path)
    assert r.returncode == 0, r.stderr


def test_no_wiki_dir_exits_cleanly(tmp_path):
    r = _run(tmp_path)
    assert r.returncode == 0, r.stderr


def test_json_output_lists_violations(tmp_path):
    wiki = tmp_path / "wiki"
    _make_page(wiki, "bad.md", "author: llm\nprovenance: sourced")
    r = _run(tmp_path, "--json")
    assert r.returncode == 1
    assert '"sources_missing"' in r.stdout
    assert "bad.md" in r.stdout
