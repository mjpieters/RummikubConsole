from __future__ import annotations

from typing import TYPE_CHECKING

import click

from . import __version__

if TYPE_CHECKING:
    from rummikub_solver import MILPSolver


def _supported_backends() -> list[MILPSolver]:
    # If run for the very first time, with several backends installed, this call
    # can take _significant_ time. Let the user know things are loading.
    from rummikub_solver import MILPSolver

    click.secho("Rummikub Solver console is loading...\r", nl=False, dim=True)
    return sorted(MILPSolver.supported())


@click.command(help="Rummikub Solver console")
@click.option(
    "--numbers",
    default=13,
    show_default=True,
    type=click.IntRange(2, 26),
    help="Number of tiles per colour (2 - 26)",
    metavar="T",
)
@click.option(
    "--repeats",
    default=2,
    show_default=True,
    type=click.IntRange(1, 4),
    help="Number of repeats per number per colour (1 - 4)",
    metavar="R",
)
@click.option(
    "--colours",
    default=4,
    show_default=True,
    type=click.IntRange(2, 8),
    help="Number of colours for the tilesets (2 - 8)",
    metavar="C",
)
@click.option(
    "--jokers",
    default=2,
    show_default=True,
    type=click.IntRange(0, 4),
    help="Number of jokers in the game (0 - 4)",
    metavar="J",
)
@click.option(
    "--min-len",
    default=3,
    show_default=True,
    type=click.IntRange(2, 6),
    help="Minimum number of tiles in a set (2 - 6)",
    metavar="M",
)
@click.option(
    "--min-initial-value",
    default=30,
    show_default=True,
    type=click.IntRange(1, 50),
    help="Minimal tile sum required as opening move",
)
@click.option(
    "--solver-backend",
    type=click.Choice(_supported_backends(), case_sensitive=False),
    help="Mixed-Integer solver to use.",
    hidden=len(_supported_backends()) == 1,
)
@click.version_option(__version__)
def rsconsole(
    numbers: int = 13,
    repeats: int = 2,
    colours: int = 4,
    jokers: int = 2,
    min_len: int = 3,
    min_initial_value: int = 30,
    solver_backend: MILPSolver | None = None,
):
    from rummikub_solver import RuleSet

    from ._console import SolverConsole

    ruleset = RuleSet(
        numbers=numbers,
        repeats=repeats,
        colours=colours,
        jokers=jokers,
        min_len=min_len,
        min_initial_value=min_initial_value,
        solver_backend=solver_backend,
    )
    cmd = SolverConsole(
        ruleset=ruleset,
        # be tolerant of input character errors, don't break the console
        stdin=click.get_text_stream("stdin", errors="replace"),
        stdout=click.get_text_stream("stdout"),
    )
    cmd.cmdloop()


if __name__ == "__main__":
    rsconsole()
