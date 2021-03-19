# SPDX-License-Identifier: MIT
from __future__ import annotations
from enum import Enum
from typing import NamedTuple, Optional, Sequence, TYPE_CHECKING

import click


if TYPE_CHECKING:
    from typing import TypedDict

    ColourEnumStyle = TypedDict("ColourEnumStyle", {"fg": str, "reverse": bool})


class Colours(Enum):
    #   letter, ANSI base color, reverse flag
    black = "k", "white", True
    blue = "b", "blue"
    orange = "o", "yellow"
    red = "r", "red"
    green = "g", "green"
    magenta = "m", "magenta"
    white = "w", "white"
    cyan = "c", "cyan"
    joker = "j", "cyan", True

    if TYPE_CHECKING:
        value: str
        style_args: ColourEnumStyle

    def __new__(cls, value: str, colour: str = "white", reverse: bool = False):
        member = object.__new__(cls)
        member._value_ = value
        member.style_args = {"fg": f"bright_{colour}", "reverse": reverse}
        return member

    @classmethod
    def c(cls, text: str, prefix: Optional[str] = None):
        """Add ANSI colour codes to a tile"""
        prefix = prefix or text[0]
        return cls(prefix).style(text)

    def style(self, text: str) -> str:
        return click.style(text, **self.style_args)

    def __str__(self):
        name = self.name
        lidx = name.index(self.value)
        if lidx <= 0:
            return name.title()
        return name[:lidx] + name[lidx].upper() + name[lidx + 1 :]


class SolverMode(Enum):
    INITIAL = "initial"
    TILE_COUNT = "tiles"
    TOTAL_VALUE = "value"


class SolverSolution(NamedTuple):
    """Raw solver solution, containing tile values and set indices"""

    tiles: Sequence[int]
    # indices into the ruleset sets list
    set_indices: Sequence[int]


class ProposedSolution(NamedTuple):
    """Proposed next move to make for a given game state"""

    tiles: Sequence[int]
    sets: Sequence[tuple[int]]
