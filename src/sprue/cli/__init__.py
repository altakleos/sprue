"""Sprue CLI entry point."""

import click

from sprue import __version__


@click.group()
@click.version_option(version=__version__, prog_name="sprue")
def main() -> None:
    """Sprue — build and operate LLM-readable knowledge bases."""


if __name__ == "__main__":
    main()
