"""sprue upgrade — atomically replace engine files in a Sprue instance."""

from __future__ import annotations

import importlib.resources as resources
import os
import shutil
import sys
import tempfile
from contextlib import ExitStack
from pathlib import Path

import click
import yaml

import sprue


def _read_schema_version(path: Path) -> int | None:
    """Read schema_version from a YAML file, returning None if absent."""
    if not path.exists():
        return None
    try:
        data = yaml.safe_load(path.read_text())
        if isinstance(data, dict):
            return data.get("schema_version")
    except Exception:
        pass
    return None


@click.command("upgrade")
@click.argument("directory", type=click.Path(exists=True), default=".")
@click.option(
    "--accept-schema-change",
    is_flag=True,
    help="Proceed with upgrade even when schema_version has changed.",
)
def upgrade(directory: str, accept_schema_change: bool) -> None:
    """Upgrade engine files in an existing Sprue instance.

    DIRECTORY defaults to the current working directory.
    Only .sprue/ is replaced — instance content (wiki/, raw/, memory/, etc.)
    is never touched.
    """
    dir_path = Path(directory).resolve()
    dot_sprue = dir_path / ".sprue"
    version_file = dot_sprue / ".sprue-version"

    # --- Validate instance ---
    if not dot_sprue.exists() or not dot_sprue.is_dir():
        click.echo(
            f"Not a Sprue instance (no .sprue/ found at {dir_path}). "
            "Run `sprue init <path>` to create one.",
            err=True,
        )
        sys.exit(1)

    # --- Read current version ---
    if version_file.exists():
        old_version = version_file.read_text().strip()
    else:
        click.echo("Warning: No version file found; assuming pre-versioning.", err=True)
        old_version = "unknown"

    new_version = sprue.__version__

    # --- Already up to date? ---
    if old_version == new_version:
        click.echo(f"Already up to date (version {new_version}).")
        sys.exit(0)

    # --- Schema compatibility check ---
    instance_schema = _read_schema_version(dir_path / "instance" / "config.yaml")
    with ExitStack() as stack:
        engine_src = stack.enter_context(
            resources.as_file(resources.files("sprue.engine"))
        )
        engine_schema = _read_schema_version(engine_src / "defaults.yaml")

    schema_changed = (
        instance_schema is not None
        and engine_schema is not None
        and instance_schema != engine_schema
    )

    if schema_changed and not accept_schema_change:
        click.echo(
            f"Schema change detected (instance: {instance_schema}, engine: {engine_schema}).\n"
            "Review changes in .sprue/defaults.yaml and update instance/config.yaml if needed.\n"
            "Re-run `sprue upgrade --accept-schema-change` after reviewing.",
            err=True,
        )
        sys.exit(2)

    # --- Atomic upgrade ---
    temp_dir: str | None = None
    sidelined: Path | None = None
    try:
        # Create temp dir on SAME filesystem for atomic rename.
        temp_dir = tempfile.mkdtemp(dir=dir_path)
        temp_path = Path(temp_dir)

        # Copy new engine files into temp dir.
        with ExitStack() as stack:
            src = stack.enter_context(
                resources.as_file(resources.files("sprue.engine"))
            )
            # copytree wants the destination to not exist, so copy into a subdir
            # then we'll rename that subdir.
            dest = temp_path / ".sprue"
            shutil.copytree(
                src,
                dest,
                ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "__init__.py"),
            )

        # Write new version file into the staged copy.
        (dest / ".sprue-version").write_text(new_version)

        # Atomic swap: old → sidelined, temp → final.
        sidelined = dir_path / f".sprue.old.{os.getpid()}"

        try:
            os.rename(dot_sprue, sidelined)
        except PermissionError:
            click.echo(
                f"Permission denied: cannot rename {dot_sprue}. "
                "Check file permissions and try again.",
                err=True,
            )
            sys.exit(1)

        try:
            os.rename(dest, dot_sprue)
        except Exception as swap_err:
            # Second rename failed — restore sidelined back to .sprue/.
            click.echo(f"Error during swap: {swap_err}", err=True)
            try:
                os.rename(sidelined, dot_sprue)
                click.echo("Restored previous .sprue/ successfully.", err=True)
            except Exception as restore_err:
                click.echo(
                    f"CRITICAL: Could not restore .sprue/ from {sidelined.name}.\n"
                    f"Restore error: {restore_err}\n"
                    f"Manual recovery: rename '{sidelined}' back to '{dot_sprue}'.",
                    err=True,
                )
            sys.exit(1)

        # Best-effort cleanup of sidelined directory.
        try:
            shutil.rmtree(sidelined)
        except Exception as cleanup_err:
            click.echo(
                f"Warning: Could not remove sidelined directory {sidelined.name}: {cleanup_err}",
                err=True,
            )
        sidelined = None  # Mark as cleaned up.

        # Clean up the now-empty temp dir.
        try:
            temp_path.rmdir()
        except Exception:
            pass
        temp_dir = None  # Mark as cleaned up.

    except PermissionError:
        click.echo(
            f"Permission denied while upgrading {dir_path}. "
            "Check file permissions and try again.",
            err=True,
        )
        sys.exit(1)
    except Exception as exc:
        click.echo(f"Upgrade failed: {exc}", err=True)
        sys.exit(1)
    finally:
        # If temp_dir still exists (copy failed before swap), clean it up.
        if temp_dir and Path(temp_dir).exists():
            shutil.rmtree(temp_dir, ignore_errors=True)

    # --- Success ---
    click.echo(f"Upgraded {dir_path}")
    click.echo(f"  {old_version} → {new_version}")
    if schema_changed:
        click.echo(
            f"  Schema changed ({instance_schema} → {engine_schema}). "
            "Review instance/config.yaml for compatibility."
        )
