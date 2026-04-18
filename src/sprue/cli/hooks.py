"""sprue hooks — create or update tool-specific agent hook shims."""
from __future__ import annotations

import importlib.resources as resources
from contextlib import ExitStack
from pathlib import Path

import click

from sprue.cli.init import _HOOK_MAP


@click.command("hooks")
@click.argument("directory", type=click.Path(), default=".")
@click.option("--force", is_flag=True, help="Overwrite existing hook files.")
def hooks(directory: str, force: bool) -> None:
    """Create or update tool-specific agent hook shims.

    Generates thin shim files (CLAUDE.md, .kiro/steering/, .cursor/rules/,
    etc.) that point to AGENTS.md. By default, only creates missing files.
    Use --force to overwrite existing ones.
    """
    target = Path(directory).resolve()

    created = 0
    skipped = 0
    with ExitStack() as stack:
        tpl_dir = stack.enter_context(
            resources.as_file(resources.files("sprue.templates"))
        )
        for src_path, dest_rel in _HOOK_MAP:
            dest = target / dest_rel
            src_file = tpl_dir / src_path
            if not src_file.exists():
                continue
            if dest.exists() and not force:
                skipped += 1
                continue
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(src_file.read_text())
            created += 1
            click.echo(f"  ✓ {dest_rel}")

    if created:
        click.echo(f"\n{created} hook(s) created.")
    if skipped:
        click.echo(f"{skipped} existing hook(s) skipped (use --force to overwrite).")
    if not created and not skipped:
        click.echo("No hooks to create.")
