# SPDX-License-Identifier: MIT
from __future__ import annotations
from collections import Counter
from typing import Optional, Sequence

import numpy as np


class GameState:
    """State of a single game for one player

    Tracks the tiles placed on the table and the rack, and if the player
    has managed to place the initial set of tiles from their rack.

    """

    initial: bool  # initial state, False if the player has placed opening tiles

    _tile_count: int  # total number of possible tiles
    rack: Counter[int]  # tiles on the rack
    table: Counter[int]  # tiles on the table

    # arrays maintained from the above counters for the solver
    # These use signed integers to simplify overflow handling when removing
    # tiles.
    rack_array: np.array[np.int8]  # array with per-tile counts on the rack
    table_array: np.array[np.int8]  # array with per-tile counts on the table

    def __init__(
        self,
        tile_count: int,
        table: Optional[Sequence[int]] = None,
        rack: Optional[Sequence[int]] = None,
    ) -> None:
        self._tile_count = tile_count
        self.reset()
        if table:
            self.add_table(table)
        if rack:
            self.add_rack(rack)

    def reset(self) -> None:
        self.table, self.rack, self.initial = Counter(), Counter(), True
        self.table_array = np.zeros(self._tile_count, dtype=np.int8)
        self.rack_array = np.zeros(self._tile_count, dtype=np.int8)

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}({self._tile_count}, "
            f"table={tuple(self.sorted_table)} rack={tuple(self.sorted_rack)})"
        )

    def with_move(self, tiles: Sequence[int]) -> GameState:
        """New state with tiles moved

        The tiles are verified to be on the rack and are moved to the table.
        This doesn't mutate this state but rather creates a new state with
        the new tile locations

        """
        moved = Counter(tiles)
        if moved - self.rack:
            raise ValueError("Move includes tiles not on the rack")
        table = list((self.table + moved).elements())
        rack = list((self.rack - moved).elements())
        return type(self)(self._tile_count, table, rack)

    def table_only(self) -> GameState:
        """New state with just the table tiles"""
        return type(self)(self._tile_count, self.sorted_table)

    @property
    def sorted_rack(self) -> list[int]:
        """The rack tile numbers as a sorted list"""
        return sorted(self.rack.elements())

    @property
    def sorted_table(self) -> list[int]:
        """The table tile numbers as a sorted list"""
        return sorted(self.table.elements())

    def add_rack(self, additions: Sequence[int]) -> None:
        if not additions:
            return
        self.rack += Counter(additions)
        np.add.at(self.rack_array, np.array(additions) - 1, 1)

    def remove_rack(self, removals: Sequence[int]) -> None:
        if not removals:
            return
        self.rack -= Counter(removals)
        rack = self.rack_array
        np.subtract.at(rack, np.array(removals) - 1, 1)
        rack[rack < 0] = 0  # in case we removed tiles not on the rack

    def add_table(self, additions: Sequence[int]) -> None:
        if not additions:
            return
        self.table += Counter(additions)
        np.add.at(self.table_array, np.array(additions) - 1, 1)

    def remove_table(self, removals: Sequence[int]) -> None:
        if not removals:
            return
        self.table -= Counter(removals)
        table = self.table_array
        np.subtract.at(table, np.array(removals) - 1, 1)
        table[table < 0] = 0  # in case we removed tiles not on the rack
