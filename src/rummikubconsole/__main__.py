import click

from . import __version__
from .console import SolverConsole
from .ruleset import RuleSet


@click.command(help="Rummikub Solver console")
@click.option(
    "--numbers",
    default=13,
    show_default=True,
    type=click.IntRange(1, 26),
    help="Number of tiles per colour (1 - 26)",
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
    type=click.IntRange(1, 8),
    help="Number of colours for the tilesets (1 - 8)",
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
    help="Mininum number of tiles in a set (2 - 6)",
    metavar="M",
)
@click.option(
    "--min-initial-value",
    default=30,
    show_default=True,
    type=click.IntRange(1, 50),
    help="Minimal tile sum required as opening move",
)
@click.version_option(__version__)
def rsconsole(
    numbers: int = 13,
    repeats: int = 2,
    colours: int = 4,
    jokers: int = 2,
    min_len: int = 3,
    min_initial_value: int = 30,
):
    ruleset = RuleSet(
        numbers=numbers,
        repeats=repeats,
        colours=colours,
        jokers=jokers,
        min_len=min_len,
        min_initial_value=min_initial_value,
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
