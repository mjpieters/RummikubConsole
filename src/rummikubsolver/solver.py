from __future__ import annotations
from itertools import chain
from typing import TYPE_CHECKING

import cvxpy as cp
import numpy as np

from .gamestate import GameState
from .types import SolverMode, SolverSolution


if TYPE_CHECKING:
    from .ruleset import RuleSet


class RummikubSolver:
    """Solvers for finding possible tile placements in Rummikub games

    Buids on the approach described by den Hertog, Dick & Hulshof,
    P.. (2006). Solving Rummikub Problems by Integer Linear Programming.
    The Computer Journal. 49. 10.1093/comjnl/bxl033.

    Adapted to work with different Rummikub rule sets, including having
    a different number of possible jokers from repeated number tiles within
    the same colour.

    Creates cvxpy solvers *once*, then reuses their parameters to
    improve efficiency.

    """

    def __init__(self, ruleset: RuleSet) -> None:
        # set membership matrix; how many copies of a given tile are present in
        # a given set. Each column is a set, each row a tile
        slen = len(ruleset.sets)
        smatrix = np.zeros((ruleset.tile_count, slen), dtype=np.uint8)
        np.add.at(
            smatrix,
            (
                np.fromiter(chain.from_iterable(ruleset.sets), np.uint8) - 1,
                np.repeat(
                    np.arange(slen), np.fromiter(map(len, ruleset.sets), np.uint16)
                ),
            ),
            1,
        )

        # Input parameters: counts for each tile on the table and on the rack
        table = self.table = cp.Parameter(ruleset.tile_count, "table", nonneg=True)
        rack = self.rack = cp.Parameter(ruleset.tile_count, "rack", nonneg=True)

        # Output variables: counts per resulting set, and counts per
        # tile taken from the rack to be added to the table.
        sets = self.sets = cp.Variable(len(ruleset.sets), "sets", integer=True)
        tiles = self.tiles = cp.Variable(ruleset.tile_count, "tiles", integer=True)

        # Constraints for the optimisation problem
        numbertiles = tiles
        joker_constraints = []
        if ruleset.jokers and ruleset.jokers != ruleset.repeats:
            # Don't include the joker in the repeated tile constraints
            numbertiles = tiles[:-1]
            jokers = tiles[-1]
            joker_constraints = [
                # You can place multiple jokers from your rack, but there are
                # never more than *ruleset.jokers* of them.
                0 <= jokers,
                jokers <= ruleset.jokers,
            ]

        constraints = [
            # placed sets can only be taken from tiles on the table and
            # the rack.
            smatrix @ sets == table + tiles,
            # the selected tiles must all come from the rack
            tiles <= rack,
            # A given set could appear multiple times, but never more than
            # *repeats* times.
            0 <= sets,
            sets <= ruleset.repeats,
            # You can place multiple tiles with the same colour and number
            # but there are never more than *ruleset.repeats* of them.
            0 <= numbertiles,
            numbertiles <= ruleset.repeats,
            *joker_constraints,
        ]

        p: dict[SolverMode, cp.Problem] = {}
        # Problem solver maximising number of tiles placed
        p[SolverMode.TILE_COUNT] = cp.Problem(cp.Maximize(cp.sum(tiles)), constraints)

        # Problem solver maximising the total value of tiles placed
        tilevalue = np.tile(
            np.arange(ruleset.numbers, dtype=np.uint16) + 1, ruleset.colours
        )
        if ruleset.jokers:
            # TODO: add joker penalty value to ruleset and separate out
            # initial phase joker scoring from penalty score case and
            # use the penallty score here.
            tilevalue = np.append(tilevalue, 0)
        p[SolverMode.TOTAL_VALUE] = cp.Problem(
            cp.Maximize(cp.sum(tiles @ tilevalue)), constraints
        )
        self._problems = p

    def __call__(self, mode: SolverMode, state: GameState) -> SolverSolution:
        """Find a solution for the given game state

        Uses the appropriate objective for the given solver mode, and takes
        the rack tile count and table tile count from state.

        """

        # set parameters
        self.rack.value = state.rack_array
        if mode is SolverMode.INITIAL:
            # can't use tiles on the table, set all counts to 0
            self.table.value = np.zeros_like(state.table_array)
            # We need to reach a minimum score, so use the total value
            # goal.
            # TODO: use dedicated solver with scores for jokers
            prob = self._problems[SolverMode.TOTAL_VALUE]
        else:
            self.table.value = state.table_array
            prob = self._problems[mode]

        value = prob.solve(solver=cp.GLPK_MI)
        if prob.status != cp.OPTIMAL:
            return SolverSolution(0, (), ())

        # convert index counts to repeated indices, as Python scalars
        # similar to what Counts.elements() produces.
        tiles = self.tiles.value
        (tidx,) = tiles.nonzero()
        # add 1 to the indices to get tile numbers
        selected_tiles = np.repeat(tidx + 1, tiles[tidx].astype(int)).tolist()

        sets = self.sets.value
        (sidx,) = sets.nonzero()
        selected_sets = np.repeat(sidx, sets[sidx].astype(int)).tolist()

        return SolverSolution(int(value), selected_tiles, selected_sets)
