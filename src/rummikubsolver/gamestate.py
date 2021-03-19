# SPDX-License-Identifier: MIT
from __future__ import annotations
from collections import Counter
from typing import Iterable, Sequence

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

    def __init__(self, tile_count: int) -> None:
        self._tile_count = tile_count
        self.reset()

    def reset(self) -> None:
        self.table, self.rack, self.initial = Counter(), Counter(), True
        self.table_array = np.zeros(self._tile_count, dtype=np.int8)
        self.rack_array = np.zeros(self._tile_count, dtype=np.int8)

    def with_move(self, tiles: Sequence[int]) -> GameState:
        """New state with tiles moved

        The tiles are assumed to be on the rack and are moved to the table.
        This doesn't mutate this state but rather creates a new state with
        the new tile locations

        """
        clone = self.__new__(type(self))
        clone._tile_count = self._tile_count

        tcounts = Counter(tiles)
        clone.table = self.table + tcounts
        clone.rack = self.rack - tcounts

        array = np.zeros_like(self.table_array)
        np.add.at(array, np.array(tiles) - 1, 1)
        clone.table_array = np.add(self.table_array, array)
        clone.rack_array = np.subtract(self.rack_array, array)

        return clone

    @property
    def sorted_rack(self) -> list[int]:
        """The rack tile numbers as a sorted list"""
        return sorted(self.rack.elements())

    @property
    def sorted_table(self) -> list[int]:
        """The table tile numbers as a sorted list"""
        return sorted(self.table.elements())

    def add_rack(self, additions: Iterable[int]) -> None:
        self.rack += Counter(additions)
        np.add.at(self.rack_array, np.array(additions) - 1, 1)

    def remove_rack(self, removals: Sequence[int]) -> None:
        self.rack -= Counter(removals)
        rack = self.rack_array
        np.subtract.at(rack, np.array(removals) - 1, 1)
        rack[rack < 0] = 0  # in case we removed tiles not on the rack

    def add_table(self, additions: Iterable[int]) -> None:
        self.table += Counter(additions)
        np.add.at(self.table_array, [t - 1 for t in additions], 1)

    def remove_table(self, removals: Sequence[int]) -> None:
        self.table -= Counter(removals)
        table = self.table_array
        np.subtract.at(table, [t - 1 for t in removals], 1)
        table[table < 0] = 0  # in case we removed tiles not on the rack
