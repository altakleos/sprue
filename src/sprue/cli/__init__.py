"""Sprue CLI entry point."""

import click

from sprue import __version__


@click.group()
@click.version_option(version=__version__, prog_name="sprue")
def main() -> None:
    """Sprue — build and operate LLM-readable knowledge bases."""


from sprue.cli.init import init
from sprue.cli.upgrade import upgrade

main.add_command(init)
main.add_command(upgrade)


if __name__ == "__main__":
    main()
