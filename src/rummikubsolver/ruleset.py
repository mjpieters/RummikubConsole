from functools import cached_property
from itertools import chain, combinations, islice, product
from typing import Iterable, Optional, Sequence

from .gamestate import GameState
from .solver import RummikubSolver
from .types import Colours, ProposedSolution, SolverMode


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
        minv = self.min_initial_value if mode is SolverMode.INITIAL else 1
        if sol.score < minv:
            return None

        tiles = sol.tiles
        set_indices = sol.set_indices

        if mode is SolverMode.INITIAL:
            # placed initial tiles, can now use rest of rack and table to look
            # for additional tiles to place.
            new_state = state.with_move(sol.tiles)
            stage2 = self._solver(SolverMode.TILE_COUNT, new_state)
            if stage2 is not None:
                tiles = sorted(tiles + stage2.tiles)
                set_indices = stage2.set_indices

        return ProposedSolution(tiles, [self.sets[i] for i in set_indices])

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
        return self._combine_with_jokers(series)

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

    def _combine_with_jokers(self, sets: Iterable[Sequence[int]]) -> set[tuple[int]]:
        if self.joker is None:
            return {tuple(set) for set in sets}
        # combine with jokers; any combination of tokens in the original series
        # replaced by any number of possible jokers.
        jokers = [self.joker] * self.jokers
        combined = (combinations([*set, *jokers], len(set)) for set in sets)
        return set(chain.from_iterable(combined))
