"""sprue upgrade — atomically replace engine files in a Sprue instance."""

from __future__ import annotations

import importlib.resources as resources
import os
import re
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


def _read_schema_window(path: Path) -> tuple[int, int] | None:
    """Read supported_schema_versions {min, max} from a YAML file."""
    if not path.exists():
        return None
    try:
        data = yaml.safe_load(path.read_text())
        if not isinstance(data, dict):
            return None
        window = data.get("supported_schema_versions")
        if not isinstance(window, dict):
            return None
        wmin = window.get("min")
        wmax = window.get("max")
        if isinstance(wmin, int) and isinstance(wmax, int):
            return (wmin, wmax)
    except Exception:
        pass
    return None


def _merge_rules(instance_path: Path, template_path: Path) -> tuple[list[str], list[str], list[str]]:
    """Append rules from the template into the instance rules.yaml by name,
    update scope of existing rules when it differs from the template, and
    remove instance rules that the template has retired.

    Preserves user-edited commands and ordering for rules the template still
    knows about. Platform-defined rules that the template removed are dropped
    — they typically reference engine scripts that have been deleted.

    Retired rules are identified by a naming prefix convention — any rule
    whose name starts with ``check-`` or matches a known-platform name is
    managed by the platform. User-added rules (e.g., ``user-custom-rule``)
    with names that never appeared in any template are preserved.

    Returns (added, scope_updated, removed). Best-effort on parse errors.
    """
    try:
        instance_doc = yaml.safe_load(instance_path.read_text(encoding="utf-8")) or []
        template_doc = yaml.safe_load(template_path.read_text(encoding="utf-8")) or []
    except Exception:
        return [], [], []
    if not isinstance(instance_doc, list) or not isinstance(template_doc, list):
        return [], [], []
    by_name = {r["name"]: r for r in template_doc if isinstance(r, dict) and r.get("name")}
    template_names = set(by_name)
    existing_names = {r.get("name") for r in instance_doc if isinstance(r, dict)}

    # Retired platform rules — rules in the instance whose command points at
    # a .sprue/scripts/ path. Those are platform-managed; if the template
    # no longer has them, drop them.
    def _is_platform(rule: dict) -> bool:
        cmd = rule.get("command")
        if isinstance(cmd, list) and any(isinstance(c, str) and ".sprue/scripts/" in c for c in cmd):
            return True
        shell = rule.get("shell") or ""
        return isinstance(shell, str) and ".sprue/scripts/" in shell

    kept: list[dict] = []
    removed: list[str] = []
    scope_updated: list[str] = []
    for rule in instance_doc:
        if not isinstance(rule, dict):
            kept.append(rule)
            continue
        name = rule.get("name")
        if name not in template_names and _is_platform(rule):
            removed.append(name)
            continue
        tpl = by_name.get(name)
        if tpl and tpl.get("scope") != rule.get("scope"):
            rule["scope"] = tpl.get("scope")
            scope_updated.append(name)
        kept.append(rule)

    added_rules: list[dict] = [
        rule for rule in template_doc
        if isinstance(rule, dict) and rule.get("name") and rule["name"] not in existing_names
    ]
    added_names = [r["name"] for r in added_rules]

    if not added_rules and not scope_updated and not removed:
        return [], [], []

    # If nothing structural changed — only appending new rules with no scope
    # updates or removals — preserve existing text byte-for-byte.
    if added_rules and not scope_updated and not removed:
        existing_text = instance_path.read_text(encoding="utf-8").rstrip()
        appended = yaml.safe_dump(added_rules, sort_keys=False, default_flow_style=False).rstrip()
        instance_path.write_text(existing_text + "\n\n" + appended + "\n", encoding="utf-8")
    else:
        full = kept + added_rules
        text = yaml.safe_dump(full, sort_keys=False, default_flow_style=False)
        instance_path.write_text(text, encoding="utf-8")

    return added_names, scope_updated, removed


def _sweep_stale_artifacts(dir_path: Path) -> None:
    """Remove leftover .sprue.old.* and tmp* dirs from a prior interrupted run.

    Addresses Momus M5: SIGKILL mid-copytree can leave dangling directories
    that ``finally`` clauses never get to clean up. This sweep runs at the
    start of every ``sprue upgrade`` invocation to reclaim them.

    Safe: only deletes directories matching our own naming patterns:
      - ``.sprue.old.<pid>`` from the atomic swap (pid is digits)
      - ``tmpXXXXXXXX`` from ``tempfile.mkdtemp`` (8 chars of [a-zA-Z0-9_])
    """
    sprue_old = re.compile(r"^\.sprue\.old\.\d+$")
    mkdtemp = re.compile(r"^tmp[A-Za-z0-9_]{8}$")
    for child in dir_path.iterdir():
        if not child.is_dir():
            continue
        if sprue_old.match(child.name) or mkdtemp.match(child.name):
            try:
                shutil.rmtree(child)
            except OSError:
                # Best-effort; do not fail the upgrade over sweep errors.
                pass


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

    if dot_sprue.is_symlink():
        click.echo(
            f".sprue/ at {dir_path} is a symlink. `sprue upgrade` does not follow "
            "symlinks to avoid unintentionally modifying shared engine directories. "
            "Replace the symlink with a concrete directory, or upgrade the target "
            "directly.",
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
        _sweep_stale_artifacts(dir_path)
        click.echo(f"Already up to date (version {new_version}).")
        sys.exit(0)

    _sweep_stale_artifacts(dir_path)

    # --- Schema compatibility check ---
    # Prefer range-based (supported_schema_versions window); fall back to
    # exact match for engines that predate the window declaration.
    instance_schema = _read_schema_version(dir_path / "instance" / "config.yaml")
    with ExitStack() as stack:
        engine_src = stack.enter_context(
            resources.as_file(resources.files("sprue.engine"))
        )
        engine_schema = _read_schema_version(engine_src / "defaults.yaml")
        engine_window = _read_schema_window(engine_src / "defaults.yaml")

    if instance_schema is None:
        # No instance-declared schema — nothing to check.
        schema_changed = False
    elif engine_window is not None:
        wmin, wmax = engine_window
        schema_changed = not (wmin <= instance_schema <= wmax)
    elif engine_schema is not None:
        schema_changed = instance_schema != engine_schema
    else:
        schema_changed = False

    if schema_changed and not accept_schema_change:
        if engine_window is not None:
            wmin, wmax = engine_window
            detail = (
                f"instance: {instance_schema}, engine supports: [{wmin}, {wmax}]"
            )
        else:
            detail = f"instance: {instance_schema}, engine: {engine_schema}"
        click.echo(
            f"Schema change detected ({detail}).\n"
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

    # --- Create missing tool-hook shims (additive only, never overwrites) ---
    try:
        with ExitStack() as stack:
            tpl_dir = stack.enter_context(
                resources.as_file(resources.files("sprue.templates"))
            )
            from sprue.cli.init import _HOOK_MAP

            for src_path, dest_rel in _HOOK_MAP:
                dest = dir_path / dest_rel
                if not dest.exists():
                    src_file = tpl_dir / src_path
                    if src_file.exists():
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        dest.write_text(src_file.read_text())
    except Exception:
        pass  # Best-effort; don't fail upgrade over shim creation.

    # --- Install missing instance-side templates (additive only) ---
    # Some templates (like memory/rules.yaml) were added to init.py after
    # early KBs were created. Install them on upgrade if they don't exist,
    # so existing KBs pick up defaults like the verify rules bundle.
    # Never overwrites user-edited files — only copies if the destination
    # doesn't exist.
    _UPGRADE_ADDITIVE_TEMPLATES = (
        ("memory/rules.yaml", "memory/rules.yaml"),
    )
    installed: list[str] = []
    merged_added: list[str] = []
    merged_updated: list[str] = []
    merged_removed: list[str] = []
    try:
        with ExitStack() as stack:
            tpl_dir = stack.enter_context(
                resources.as_file(resources.files("sprue.templates"))
            )
            for src_path, dest_rel in _UPGRADE_ADDITIVE_TEMPLATES:
                dest = dir_path / dest_rel
                if not dest.exists():
                    src_file = tpl_dir / src_path
                    if src_file.exists():
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        dest.write_text(src_file.read_text())
                        installed.append(dest_rel)
                elif dest_rel == "memory/rules.yaml":
                    # Merge new rules from the template into the existing
                    # instance file by `name`. Preserves user edits and ordering.
                    src_file = tpl_dir / src_path
                    if src_file.exists():
                        merged_added, merged_updated, merged_removed = _merge_rules(dest, src_file)
    except Exception:
        pass  # Best-effort; don't fail upgrade over template install.

    # --- Create wiki/assets symlink if missing (ADR-0047) ---
    # Existing KBs pre-dating the symlink convention won't have it.
    # Create it here so Obsidian can render raw/assets/ from inside wiki/.
    assets_symlink_created = False
    assets_link = dir_path / "wiki" / "assets"
    if (dir_path / "wiki").is_dir() and not (assets_link.is_symlink() or assets_link.exists()):
        try:
            assets_link.symlink_to(Path("..") / "raw" / "assets")
            assets_symlink_created = True
        except OSError:
            pass  # Windows without dev mode, read-only fs, etc.

    # --- Seed missing state files ---
    # Matches init behavior; older KBs scaffolded before seed-state-files
    # didn't get these created, so agents hit "file not found" on first
    # import. Empty files parse as None/[] in all consumers.
    seeded_state: list[str] = []
    state_dir = dir_path / "instance" / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    for rel_name in ("imports.yaml", "compilations.yaml", "image-annotations.yaml", "verifications.yaml"):
        seed = state_dir / rel_name
        if not seed.exists():
            seed.write_text("")
            seeded_state.append(f"instance/state/{rel_name}")

    # --- Success ---
    click.echo(f"Upgraded {dir_path}")
    click.echo(f"  {old_version} → {new_version}")
    if installed:
        for path in installed:
            click.echo(f"  Installed: {path}")
    if merged_added:
        click.echo(f"  Added rules: {', '.join(merged_added)}")
    if merged_updated:
        click.echo(f"  Updated rule scope: {', '.join(merged_updated)}")
    if merged_removed:
        click.echo(f"  Retired rules: {', '.join(merged_removed)}")
    if assets_symlink_created:
        click.echo("  Created wiki/assets → ../raw/assets symlink (for Obsidian)")
    if seeded_state:
        click.echo(f"  Seeded empty state files: {', '.join(seeded_state)}")
    if schema_changed:
        click.echo(
            f"  Schema changed ({instance_schema} → {engine_schema}). "
            "Review instance/config.yaml for compatibility."
        )
