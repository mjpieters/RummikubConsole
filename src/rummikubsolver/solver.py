import cvxpy as cp
import numpy as np

from .ruleset import RuleSet


class RummikubSolver:

    def __init__(self, ruleset: RuleSet):
        self.sets = sorted(ruleset.sets)
        self.repeats = ruleset.repeats
        self.table, self.rack = [], []

        # array of tile 'names', each tile is really index + 1
        self.tiles = np.array(ruleset.tiles, dtype=np.uint16)
        # values for each tile number
        value = np.tile(
            np.arange(ruleset.numbers, dtype=np.uint16) + 1, ruleset.colours
        )
        if ruleset.joker is not None:
            # add 0 value for the joker
            value = np.append(value, 0)
        self.value = value

        # matrix of booleans; is a given tile a member of the given set
        # each column is a set, each row a tile
        self.sets_matrix = np.array(
            [[t in set for set in self.sets] for t in ruleset.tiles],
            dtype=np.bool,
        )

        # how many of each tile are placed on the table or player rack?
        self.table_array = np.zeros(self.tiles.shape, dtype=np.uint8)
        self.rack_array = np.zeros(self.tiles.shape, dtype=np.uint8)

    def add_rack(self, additions):
        self.rack = sorted([*self.rack, *additions])
        self.rack_array[[t - 1 for t in additions]] += 1

    def remove_rack(self, removals):
        rack, rack_array = self.rack, self.rack_array
        for t in removals:
            try:
                rack.remove(t)
                rack_array[t - 1] -= 1
            except ValueError:
                print(f"{t} not on rack")

    def add_table(self, additions):
        self.table = sorted([*self.table, *additions])
        self.table_array[[t - 1 for t in additions]] += 1

    def remove_table(self, removals):
        for t in removals:
            try:
                self.table.remove(t)
                self.table_array[t - 1] -= 1
            except ValueError:
                print(f"{t} not on table")

    def solve(self, maximise="tiles", initial_meld=None):
        if initial_meld is None:
            initial_meld = self.initial
        if initial_meld:
            maximise = "value"

        table = self.table_array
        if initial_meld:
            table = np.zeros_like(table)

        rack = self.rack_array
        value = self.value

        smatrix = self.sets_matrix
        ntiles, nsets = smatrix.shape
        vsets = cp.Variable(nsets, integer=True)
        vtiles = cp.Variable(ntiles, integer=True)

        target = vtiles
        if maximise == "value":
            target = value @ target
        objective = cp.Maximize(cp.sum(target))

        constraints = [
            # sets can only be taken from available and selected tiles
            smatrix @ vsets == table + vtiles,
            # the selected tiles must all come from the rack
            vtiles <= rack,
            # sets can be repeated between 0 and max repeats times
            -vsets <= 0,
            vsets <= self.repeats,
            # tiles can be repeated between 0 and max repeats times
            -vtiles <= 0,
            vtiles <= self.repeats,
            # TODO: Add separate constraints for jokers!
        ]

        prob = cp.Problem(objective, constraints)
        return prob.solve(solver=cp.GLPK_MI), vtiles.value, vsets.value
