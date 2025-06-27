from __future__ import annotations

from collections import Counter
from enum import Enum
from itertools import chain
from typing import TYPE_CHECKING

from rummikub_solver import Tile

from ._types import Colour, CompleterMethod
from ._utils import expand_tileref

if TYPE_CHECKING:
    from ._console import SolverConsole


JOKER = Colour.joker.value


class TileSource(Enum):
    """Where to check for available tiles"""

    NOT_PLAYED = 0  # tiles not on the table or on your rack
    RACK = 1
    TABLE = 2

    @property
    def tile_completer(self) -> CompleterMethod:
        """Create a completer for a given tile source"""

        def completer(
            console: SolverConsole, text: str, line: str, begidx: int, endidx: int
        ) -> list[str]:
            """Complete tile names, but only those that are still available to place"""
            _, *args = (line[:begidx] + line[endidx:]).split()
            # expand groups and runs first
            args = chain.from_iterable(expand_tileref(arg) for arg in args)
            tmap, rmap = console._tile_map, console._r_tile_map  # type: ignore[privateUsage]
            avail = self.available(console) - Counter(
                tmap[a] for a in args if a in tmap
            )

            # if completing a valid tile plus dash, offer all possible
            # tile numbers that could make it a run
            if (
                text[:1] != JOKER
                and len(parts := text.split("-")) == 2
                and (t := tmap.get(parts[0])) in avail
            ):
                if TYPE_CHECKING:
                    assert t is not None
                n = console._ruleset.numbers  # type: ignore[privateUsage]
                c = (t - 1) // n
                opts = (
                    f"{parts[0]}-{rmap[a][1:]}"
                    for a in avail
                    if a > t and (a - 1) // n == c
                )
                return [opt for opt in opts if opt.startswith(text)]

            # alternative options in addition to the main tile names
            options: list[str] = []
            if tmap.get(text) in avail:
                # if text is an available tile, offer a dash to create a run
                options.append(f"{text}-")

            elif all(Colour(t) for t in text):
                # if text consists entirely of colour letters, offer the other colours
                # to form a group
                colours = sorted(
                    {c for t in avail if (c := rmap[t][0]) not in text and c != JOKER}
                )
                options += (f"{text}{c}" for c in colours)

            return options + [
                n for t, c in avail.items() if c and (n := rmap[t]).startswith(text)
            ]

        return completer

    def available(self, console: SolverConsole) -> Counter[Tile]:
        game = console.game
        if self is TileSource.RACK:
            return game.rack.copy()
        elif self is TileSource.TABLE:
            return game.table.copy()
        # NOT_PLAYED
        ruleset = console._ruleset  # type: ignore[privateUsage]
        repeats, jokers = ruleset.repeats, ruleset.jokers
        counts = Counter({t: repeats for t in ruleset.tiles})
        if jokers and jokers != repeats:
            counts[console._tile_map[JOKER]] = jokers  # type: ignore[privateUsage]
        counts -= game.table + game.rack
        return counts

    def parse_tiles(self, console: SolverConsole, args: str) -> list[int]:
        avail = self.available(console)
        tiles: list[int] = []
        for arg in args.split():
            for tile in expand_tileref(arg):
                t = console._tile_map.get(tile)  # type: ignore[privateUsage]
                if t is None:
                    console.error("Ignoring invalid tile:", tile)
                    continue
                if not avail[t]:
                    console.error(f"No {tile} tile available.")
                    continue
                avail[t] -= 1
                tiles.append(t)
        return tiles
