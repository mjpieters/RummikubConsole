# SPDX-License-Identifier: MIT
from __future__ import annotations
from functools import cached_property
from itertools import chain, combinations, islice, product, repeat
from typing import Iterable, Optional, Sequence

from .gamestate import GameState
from .solver import RummikubSolver
from .types import Colours, ProposedSolution, SolverMode, TableArrangement


class RuleSet:
    """Manages all aspects of a specific set of Rummikub rules"""

    def __init__(
        self,
        numbers: int = 13,
        repeats: int = 2,
        colours: int = 4,
        jokers: int = 2,
        min_len: int = 3,
        min_initial_value: int = 30,
    ):
        self.numbers = numbers
        self.repeats = repeats
        self.colours = colours
        self.jokers = jokers
        self.min_len = min_len
        self.min_initial_value = min_initial_value

        self.tile_count = numbers * colours
        self.joker = None
        if jokers:
            self.tile_count += 1
            self.joker = self.tile_count

        self._solver = RummikubSolver(self)

    def new_game(self) -> GameState:
        """Create a new game state for this ruleset"""
        return GameState(self.tile_count)

    def solve(
        self, state: GameState, mode: Optional[SolverMode] = None
    ) -> Optional[ProposedSolution]:
        """Find the best option for placing tiles from the rack

        If no mode is selected, uses the game initial state flag
        to switch between initial and tile-count modes.

        When in initial mode, if there are tiles on the table already,
        adds an extra round of solving if the minimal point threshold has
        been met, to find additional tiles that can be moved onto the
        table in the same turn.

        Returns None if you can't move tiles from the rack to the table.

        """
        if mode is None:
            mode = SolverMode.INITIAL if state.initial else SolverMode.TILE_COUNT

        sol = self._solver(mode, state)
        if not sol.tiles:
            return None

        tiles = sol.tiles
        set_indices = sol.set_indices

        if mode is SolverMode.INITIAL and state.table:
            # placed initial tiles, can now use rest of rack and what is
            # available on the table to look for additional tiles to place.
            new_state = state.with_move(sol.tiles)
            stage2 = self._solver(SolverMode.TILE_COUNT, new_state)
            if stage2 is not None:
                tiles = sorted(tiles + stage2.tiles)
                set_indices = stage2.set_indices

        return ProposedSolution(tiles, [self.sets[i] for i in set_indices])

    def arrange_table(self, state: GameState) -> TableArrangement:
        """Check if the tiles on the table can be arranged into sets

        Produces a series of sets and how many unattached jokers there are.

        """
        table_only, joker = state.table_only(), self.joker
        if joker is not None:
            joker_count = table_only.table[joker]
            table_only.remove_table((self.joker,) * joker_count)

        for jc in range(joker_count + 1):
            if jc:
                table_only.add_table((self.joker,))
            sol = self._solver(SolverMode.TILE_COUNT, table_only)
            if sol.set_indices:
                return TableArrangement(
                    [self.sets[s] for s in sol.set_indices], joker_count - jc
                )

    @cached_property
    def game_state_key(self) -> str:
        """Short string uniquely identifying game states that fit this ruleset"""
        # minimal initial value and minimum set length are not reflected in
        # the game state data so are not part of the key.
        keys = zip(
            "nrcj",
            (self.numbers, self.repeats, self.colours, self.jokers),
        )
        return "".join([f"{k}{v}" for k, v in keys])

    def create_tile_maps(self) -> tuple[dict[str, int], dict[int, str]]:
        """Create tile number -> name and name -> tile number maps"""
        cols, nums = islice(Colours, self.colours), range(self.numbers)
        names = [f"{c.value}{n + 1}" for c, n in product(cols, nums)]
        if self.joker:
            names.append(Colours.joker.value)
        return dict(zip(names, self.tiles)), dict(zip(self.tiles, names))

    @cached_property
    def tiles(self) -> Sequence[int]:
        return list(range(1, self.tile_count + 1))

    @cached_property
    def sets(self) -> Sequence[tuple[int]]:
        return sorted(self._runs() | self._groups())

    @cached_property
    def setvalues(self) -> Sequence[int]:
        n, mlen = self.numbers, self.min_len
        # generate a runlength value matrix indexed by [len(set)][min(set)],
        # giving total tile value for a given set accounting for jokers. e.g. a
        # 3 tile run with lowest number 12 must have a joker acting as the 11 in
        # (j, 12, 13), and for initial placement the sum of numbers would be 36.
        rlvalues = [[0] * (n + 1)]
        for i, rl in enumerate(range(1, mlen * 2)):
            tiles = chain(range(i, n + 1), repeat(n - i))
            rlvalues.append([v + t for v, t in zip(rlvalues[-1], tiles)])

        def _calc(s, _next=next, _len=len, joker=self.joker):
            """Calculate sum of numeric value of tiles in set.

            If there are jokers in the set the max possible value for the run or
            group formed is used.

            """
            nums = ((t - 1) % n + 1 for t in s if t != joker)
            n0 = _next(nums)
            try:
                # n0 == n1: group of same numbers, else run of same colour
                return _len(s) * n0 if n0 == _next(nums) else rlvalues[_len(s)][n0]
            except StopIteration:
                # len(nums) == 1, rest of set is jokers. Can be both a run or a
                # group, e.g. (5, j, j): (5, 5, 5) = 15 or (5, 6, 7) = 18, and
                # (13, j, j): (13, 13, 13) = 39 or (j, j, 13) = 36. Use max to
                # pick best.
                return max(_len(s) * n0, rlvalues[_len(s)][n0])

        return [_calc(set) for set in self.sets]

    def _runs(self) -> set[tuple[int]]:
        colours, ns = range(self.colours), self.numbers
        lengths = range(self.min_len, self.min_len * 2)
        # runs start at a given coloured tile, and are between min_len and
        # 2x min_len (exclusive) tiles long.
        series = (
            range(ns * c + num, ns * c + num + length)
            for c, length in product(colours, lengths)
            for num in range(1, ns - length + 2)
        )
        return self._combine_with_jokers(series, runs=True)

    def _groups(self) -> set[tuple[int]]:
        ns, cs = self.numbers, self.colours
        # groups are between min_len and #colours long, a group per possible
        # tile number value.
        lengths = range(self.min_len, cs + 1)
        fullgroups = (range(num, ns * cs + 1, ns) for num in range(1, ns + 1))
        groups = chain.from_iterable(
            combinations(fg, len) for fg, len in product(fullgroups, lengths)
        )
        return self._combine_with_jokers(groups)

    def _combine_with_jokers(
        self, sets: Iterable[Sequence[int]], runs: bool = False
    ) -> set[tuple[int]]:
        j, mlen = self.joker, self.min_len
        if j is None:
            return set(map(tuple, sets))
        # for sets of minimum length: combine with jokers; any combination of
        # tokens in the original series replaced by any number of possible
        # jokers. For groups, do not generate further combinations for longer sets, as
        # these would leave jokers free for the next player to take. For runs
        # only generate 'inner' jokers.
        longer = lambda s: [tuple(s)]  # noqa: E731
        if runs:
            longer = lambda s: (  # noqa: E731
                (s[0], *c, s[-1]) for c in combinations([*s[1:-1], *js], len(s) - 2)
            )
        js = [j] * self.jokers
        comb = (
            combinations([*s, *js], len(s)) if len(s) == mlen else longer(s)
            for s in sets
        )
        return set(chain.from_iterable(comb))
