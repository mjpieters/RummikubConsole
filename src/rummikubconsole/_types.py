# SPDX-License-Identifier: MIT
from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Protocol, Self

import click
from rummikub_solver import Colour as RuleSetColour

if TYPE_CHECKING:
    from typing import TypedDict

    from ._console import SolverConsole

    class ColourEnumStyle(TypedDict):
        fg: str
        reverse: bool


class CompleterMethod(Protocol):
    def __call__(
        self,
        console: SolverConsole,
        text: str,
        line: str,
        begidx: int,
        endidx: int,
    ) -> list[str]: ...


class Colour(Enum):
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
        style_args: ColourEnumStyle

    def __new__(cls, value: str, colour: str = "white", reverse: bool = False):
        member = object.__new__(cls)
        member._value_ = value
        member.style_args = {"fg": f"bright_{colour}", "reverse": reverse}
        return member

    @classmethod
    def from_ruleset(cls, colour: RuleSetColour) -> Self:
        return cls[colour.name.lower()]

    @classmethod
    def c(cls, text: str, prefix: str | None = None) -> str:
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
