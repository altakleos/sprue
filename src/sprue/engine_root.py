"""Resolve filesystem roots for Sprue engine and instance directories.

This module is the single source of truth for locating engine files
(defaults.yaml, protocols/, scripts/, etc.) and instance files
(identity.md, config.yaml, wiki/, raw/, etc.).  Every other module
that needs a root path imports from here.

Resolution order — engine_root():
  1. SPRUE_ENGINE_ROOT env var (testing / overrides)
  2. <instance_root>/.sprue  (user-instance case)
  3. Path(__file__).parent / 'engine'  (source-repo / editable-install)
  4. importlib.resources.files('sprue.engine') via as_file()  (installed wheel)

Resolution order — instance_root():
  1. SPRUE_INSTANCE_ROOT env var
  2. Walk upward from cwd for markers (.sprue/, instance/, wiki/)
  3. Fall back to cwd
"""

from __future__ import annotations

import os
from contextlib import ExitStack
from functools import lru_cache
from pathlib import Path

# Module-level ExitStack for materializing importlib Traversables.
# Kept alive for the process lifetime (acceptable per Phase B design).
_resource_stack = ExitStack()

_INSTANCE_MARKERS = (".sprue", "instance", "wiki")


@lru_cache(maxsize=1)
def instance_root() -> Path:
    """Return the instance directory containing wiki/, raw/, memory/, etc.

    Resolution:
      1. SPRUE_INSTANCE_ROOT env var if set.
      2. Walk upward from cwd looking for .sprue/, instance/, or wiki/.
      3. Fall back to cwd.
    """
    env = os.environ.get("SPRUE_INSTANCE_ROOT")
    if env:
        return Path(env).resolve()

    cwd = Path.cwd().resolve()
    for directory in (cwd, *cwd.parents):
        if any((directory / m).exists() for m in _INSTANCE_MARKERS):
            return directory
    return cwd


@lru_cache(maxsize=1)
def engine_root() -> Path:
    """Return the directory containing engine files (defaults.yaml, protocols/, …).

    Resolution:
      1. SPRUE_ENGINE_ROOT env var if set.
      2. <instance_root>/.sprue if it exists.
      3. Path(__file__).parent / 'engine' if it exists (source/editable-install).
      4. importlib.resources.files('sprue.engine') materialized via as_file().
    """
    # Priority 1: explicit override
    env = os.environ.get("SPRUE_ENGINE_ROOT")
    if env:
        return Path(env).resolve()

    # Priority 2: user-instance .sprue/ directory
    dot_sprue = instance_root() / ".sprue"
    if dot_sprue.is_dir():
        return dot_sprue

    # Priority 3: sibling engine/ directory (source checkout or editable install)
    sibling = Path(__file__).resolve().parent / "engine"
    if sibling.is_dir():
        return sibling

    # Priority 4: installed package resources (wheel)
    import importlib.resources as res

    traversable = res.files("sprue.engine")
    return Path(_resource_stack.enter_context(res.as_file(traversable)))


if __name__ == "__main__":
    print(f"engine_root:   {engine_root()}")
    print(f"instance_root: {instance_root()}")
