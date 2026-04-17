"""Sprue engine package — protocols, scripts, prompts, defaults.

This package is a data namespace. Engine files are bundled as package
data and accessed at runtime via ``importlib.resources.files``. Python
scripts within ``engine/scripts/`` are invoked as subprocesses, not
imported, so this package does not expose a module-level API.
"""
