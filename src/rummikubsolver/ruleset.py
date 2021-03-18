from functools import cached_property
from itertools import chain, combinations, islice, product
from typing import Iterable, Optional, Sequence

from .types import Colours


class RuleSet:
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

    @cached_property
    def joker(self) -> Optional[int]:
        if self.jokers:
            return self.numbers * self.colours + 1
        return None

    def create_tile_maps(self) -> tuple[dict[str, int], dict[int, str]]:
        """Create tile number -> name and name -> tile number maps"""
        cols, nums = islice(Colours, self.colours), range(self.numbers)
        names = [f"{c.value}{n + 1}" for c, n in product(cols, nums)]
        if self.joker:
            names.append(Colours.joker.value)
        return dict(zip(names, self.tiles)), dict(zip(self.tiles, names))

    @cached_property
    def tiles(self) -> Sequence[int]:
        tiles = list(range(1, self.numbers * self.colours + 1))
        joker = self.joker
        return tiles if joker is None else [*tiles, joker]

    @cached_property
    def sets(self) -> set[tuple[int]]:
        return {()} | self.runs | self.groups

    @cached_property
    def runs(self) -> set[tuple[int]]:
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

    @cached_property
    def groups(self) -> set[tuple[int]]:
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
