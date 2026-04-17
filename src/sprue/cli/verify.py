"""sprue verify — run verification checks against a Sprue instance."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import click

from sprue.engine_root import engine_root, instance_root


@click.command("verify", context_settings={"ignore_unknown_options": True})
@click.argument("args", nargs=-1, type=click.UNPROCESSED)
def verify(args: tuple[str, ...]) -> None:
    """Run verification checks from memory/rules.yaml.

    All arguments are forwarded to the underlying verify.py script.
    Supports --file FILE, --json, --jobs N, and any future flags.
    """
    script = engine_root() / "scripts" / "verify.py"
    if not script.is_file():
        click.echo(
            f"Error: verify.py not found at {script}. "
            "Is the engine installed? Try `sprue upgrade`.",
            err=True,
        )
        sys.exit(1)

    cmd = [sys.executable, str(script), *args]
    cwd = instance_root()

    result = subprocess.run(cmd, cwd=str(cwd))
    sys.exit(result.returncode)
