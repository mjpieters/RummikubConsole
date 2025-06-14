# SPDX-License-Identifier: MIT
from __future__ import annotations

from enum import StrEnum
from itertools import chain
from typing import TYPE_CHECKING, Self

import cvxpy as cp
import numpy as np

from .gamestate import GameState
from .types import SolverMode, SolverSolution

if TYPE_CHECKING:
    from .ruleset import RuleSet


class MILPSolver(StrEnum):
    """Mixed-integer Linear Programming solver to use"""

    # OSS solvers
    CBC = "CBC"
    """COIN-OR (EPL-2.0), https://github.com/coin-or/CyLP"""

    GLPK_MI = "GLPK_MI"
    """GNU Linear Programming Kit (GPL-3.0-only), https://www.gnu.org/software/glpk/ (via https://pypi.org/p/cvxopt)"""

    HIGHS = "HIGHS"
    """HiGHS (MIT), https://highs.dev/ (via https://pypi.org/p/highspy)"""

    SCIP = "SCIP"
    """SCIP (Apache-2.0), https://scipopt.org/ (via https://pypi.org/p/pyscipopt)"""

    SCIPY = "SCIPY"
    """SciPy (BSD-3-Clause), https://scipy.org/, default solver (built on HiGHS)"""

    # Commercial solvers
    COPT = "COPT"
    """COPT (LicenseRef-Commercial), https://github.com/COPT-Public/COPT-Release"""

    CPLEX = "CPLEX"
    """IBM CPLEX (LicenseRef-Commercial), https://www.ibm.com/docs/en/icos"""

    GUROBI = "GUROBI"
    """Gurobi (LicenseRef-Commercial), https://www.gurobi.com/"""

    MOSEK = "MOSEK"
    """Mosek (LicenseRef-Commercial), https://www.mosek.com/"""

    XPRESS = "XPRESS"
    """Fico XPress, (LicenseRef-Commercial), https://www.fico.com/en/products/fico-xpress-optimization"""

    @classmethod
    def supported(cls) -> set[Self]:
        installed: set[str] = set(cp.installed_solvers())
        return {member for member in cls if member in installed}


# These are tried in order based on what is installed
DEFAULT_MILP_BACKENDS = (MILPSolver.HIGHS, MILPSolver.SCIPY)


class RummikubSolver:
    """Solvers for finding possible tile placements in Rummikub games

    Builds on the approach described by D. Den Hertog, P. B. Hulshof,
    Solving Rummikub Problems by Integer Linear Programming, The Computer
    Journal, Volume 49, Issue 6, November 2006, Pages 665-669,
    https://doi.org/10.1093/comjnl/bxl033

    Adapted to work with different Rummikub rule sets, including having
    a different number of possible jokers from repeated number tiles within
    the same colour, as well as much better initial tile placement and
    joker handling in general.

    Creates cvxpy solvers *once* and use parameters to improve efficiency.

    """

    def __init__(self, ruleset: RuleSet, backend: MILPSolver | None = None) -> None:
        if backend is None:
            supported = MILPSolver.supported()
            backend = next(d for d in DEFAULT_MILP_BACKENDS if d in supported)
        self.backend = backend

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
        if ruleset.jokers:
            numbertiles, jokers = tiles[:-1], tiles[-1]
            joker_constraints = [
                # You can place multiple jokers from your rack, but there are
                # never more than *ruleset.jokers* of them.
                jokers >= 0,
                jokers <= ruleset.jokers,
            ]

        constraints: list[cp.Constraint] = [
            # placed sets can only be taken from selected rack tiles and what
            # was already placed on the table.
            smatrix @ sets == table + tiles,
            # the selected tiles must all come from your rack
            tiles <= rack,
            # A given set could appear multiple times, but never more than
            # *repeats* times.
            sets >= 0,
            sets <= ruleset.repeats,
            # You can place multiple tiles with the same colour and number
            # but there are never more than *ruleset.repeats* of them.
            numbertiles >= 0,
            numbertiles <= ruleset.repeats,
            # variable joker constraints for the current ruleset
            *joker_constraints,
        ]

        p: dict[SolverMode, cp.Problem] = {}
        # Problem solver maximising number of tiles placed
        p[SolverMode.TILE_COUNT] = cp.Problem(cp.Maximize(cp.sum(tiles)), constraints)  # type: ignore[reportUnknownMemberType]

        # Problem solver maximising the total value of tiles placed
        tilevalue = np.tile(
            np.arange(ruleset.numbers, dtype=np.uint16) + 1, ruleset.colours
        )
        if ruleset.jokers:
            tilevalue = np.append(tilevalue, 0)
        p[SolverMode.TOTAL_VALUE] = cp.Problem(
            cp.Maximize(cp.sum(tiles @ tilevalue)),  # type: ignore[reportUnknownMemberType]
            constraints,
        )

        # Problem solver used for the opening move ("initial meld").
        # Initial meld scoring is based entirely on the sets formed, and must
        # be equal to or higher than the minimal score. Maximize the tile count
        # _without jokers_.
        setvalue = np.array(ruleset.setvalues, dtype=np.uint16)
        initial_constraints = [
            *constraints,
            sets @ setvalue >= ruleset.min_initial_value,
        ]
        p[SolverMode.INITIAL] = cp.Problem(
            cp.Maximize(cp.sum(numbertiles)),  # type: ignore[reportUnknownMemberType]
            initial_constraints,
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
        else:
            self.table.value = state.table_array

        prob = self._problems[mode]
        value = prob.solve(solver=self.backend)  # type: ignore[reportUnknownMemberType]
        if TYPE_CHECKING:
            assert isinstance(value, float)
        if np.isinf(value):
            # no solution for the problem (e.g. no combination of tiles on
            # the rack leads to a valid set or has enough points when opening)
            return SolverSolution((), ())

        # convert index counts to repeated indices, as Python scalars
        # similar to what Counts.elements() produces.
        tiles = self.tiles.value
        if TYPE_CHECKING:
            assert tiles is not None
        (tidx,) = tiles.nonzero()
        # add 1 to the indices to get tile numbers
        selected_tiles = np.repeat(tidx + 1, tiles[tidx].astype(int)).tolist()

        sets = self.sets.value
        if TYPE_CHECKING:
            assert sets is not None
        (sidx,) = sets.nonzero()
        selected_sets = np.repeat(sidx, sets[sidx].astype(int)).tolist()

        return SolverSolution(selected_tiles, selected_sets)
