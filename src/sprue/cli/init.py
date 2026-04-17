"""sprue init — scaffold a new Sprue knowledge base instance."""

from __future__ import annotations

import importlib.resources as resources
import shutil
import sys
from contextlib import ExitStack
from datetime import date
from pathlib import Path

import click

import sprue


# Directories scaffolded in every new instance.
_INSTANCE_DIRS = ("instance", "raw", "wiki", "notebook", "inbox", "memory", "state")

# Template files: (source name inside sprue.templates, destination relative to target).
_TEMPLATE_MAP = (
    ("AGENTS.md", "AGENTS.md"),
    ("README.md", "README.md"),
    (".gitignore", ".gitignore"),
    ("identity.md", "instance/identity.md"),
    ("config.yaml", "instance/config.yaml"),
)


def _render(text: str, variables: dict[str, str]) -> str:
    """Replace {{key}} placeholders with values from *variables*."""
    for key, value in variables.items():
        text = text.replace("{{" + key + "}}", value)
    return text


@click.command("init")
@click.argument("directory", type=click.Path())
@click.option("--identity", default=None, help="One-sentence identity statement (audience + scope).")
@click.option("--force", is_flag=True, help="Overwrite existing .sprue/ directory.")
def init(directory: str, identity: str | None, force: bool) -> None:
    """Scaffold a new Sprue knowledge base instance.

    DIRECTORY is the target path for the new KB. Created if it does not exist.
    """
    target = Path(directory).resolve()
    dot_sprue = target / ".sprue"

    # --- Idempotency check (T19) ---
    if dot_sprue.exists() and not force:
        click.echo(
            f"Error: Instance already exists at {target}. "
            "Use `sprue upgrade` to update the engine, or `sprue init --force` to reinitialize.",
            err=True,
        )
        sys.exit(1)

    # --- Resolve identity (T20: non-TTY fallback) ---
    if identity is None:
        if sys.stdin.isatty():
            identity = click.prompt(
                "Enter a one-sentence identity "
                "(audience + scope, e.g., 'Engineering notes on distributed systems for senior engineers')"
            )
        else:
            click.echo(
                "Error: --identity flag required when stdin is not a TTY. "
                "Example: sprue init my-kb --identity 'Cooking recipes for home chefs.'",
                err=True,
            )
            sys.exit(2)

    # --- Copy engine files into .sprue/ ---
    target.mkdir(parents=True, exist_ok=True)

    with ExitStack() as stack:
        src = stack.enter_context(resources.as_file(resources.files("sprue.engine")))
        if dot_sprue.exists() and force:
            shutil.rmtree(dot_sprue)
        shutil.copytree(
            src,
            dot_sprue,
            dirs_exist_ok=force,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "__init__.py"),
        )

    # --- Scaffold instance directories ---
    for dirname in _INSTANCE_DIRS:
        (target / dirname).mkdir(parents=True, exist_ok=True)

    # --- Render templates ---
    variables = {
        "identity": identity,
        "sprue_version": sprue.__version__,
        "created_date": date.today().isoformat(),
    }

    with ExitStack() as stack:
        templates_dir = stack.enter_context(
            resources.as_file(resources.files("sprue.templates"))
        )
        for src_name, dest_rel in _TEMPLATE_MAP:
            template_text = (templates_dir / src_name).read_text()
            rendered = _render(template_text, variables)
            dest = target / dest_rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(rendered)

    # --- Write .sprue-version ---
    (dot_sprue / ".sprue-version").write_text(sprue.__version__)

    # --- Success ---
    click.echo(f"Initialized Sprue KB at {target}")
    click.echo(f"  .sprue/          — engine files (v{sprue.__version__})")
    for dirname in _INSTANCE_DIRS:
        click.echo(f"  {dirname + '/':15s} — created")
    click.echo(f"  AGENTS.md        — agent bootstrap")
    click.echo(f"  README.md        — project readme")
    click.echo(f"  .gitignore       — default ignores")
    click.echo(f"\nNext steps:\n  cd {directory}\n  sprue verify")
