from __future__ import annotations

import re
import shutil
from collections.abc import Iterable, Iterator
from typing import TYPE_CHECKING

from ._types import Colour, CompleterMethod

if TYPE_CHECKING:
    from ._console import SolverConsole


def fixed_completer(*options: str, case_insensitive: bool = False) -> CompleterMethod:
    """Generate a completer for a fixed number of arguments"""

    def completer(
        console: SolverConsole, text: str, line: str, begidx: int, endidx: int
    ) -> list[str]:
        if case_insensitive:
            text = text.lower()
        return [opt for opt in options if opt.startswith(text)]

    return completer


def tile_display(tiles: Iterable[str]) -> str:
    """Format a sequence of tiles into columns

    Takes into account terminal width, and adds ANSI colours to the tiles
    displayed. A 2-space indent is added to all lines.

    """
    width = shutil.get_terminal_size()[0] - 4  # 2 space indent, 2 spaces margin
    if width < 3:  # obviously too narrow for even a single tile, ignore
        width = 76
    line: list[str] = []
    lines, used = [line], 0
    for tile in tiles:
        tl = len(tile) + 2  # includes comma and space
        if used + tl - 1 >= width:  # do not count a space at the end
            # start a new line
            used, line = 0, []
            lines.append(line)
        line.append(Colour.c(tile))
        used += tl
    return "  " + ",\n  ".join([", ".join(ln) for ln in lines])


TILEREF = re.compile(
    r"""
    ^(
        # run (single colour, multiple numbers)
        (?P<run>[{c}](?P<start>[1-9][0-9]?)-(?P<end>[1-9][0-9]?))
    |   # group (multiple colours)
        (?P<group>(?P<colours>[{c}]{{2,}})(?P<num>[1-9][0-9]?))
    |   # single tile
        (?P<tile>[{c}][1-9][0-9]?)
    )$
    """.format(c="".join([c.value for c in Colour])),
    flags=re.VERBOSE,
)


def expand_tileref(t: str) -> Iterator[str]:
    if match := TILEREF.match(t):
        if tile := match["tile"]:
            yield tile
        elif run := match["run"]:
            for num in range(int(match["start"]), int(match["end"]) + 1):
                yield f"{run[0]}{num}"
        elif group := match["colours"]:
            num = match["num"]
            yield from (f"{g}{num}" for g in group)
        return
    # pass through, no validation done.
    yield t
