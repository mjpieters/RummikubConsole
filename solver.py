import cvxpy as cp
import numpy as np


class RummikubSolver:

    def __init__(self, tiles, sets, rack=[], table=[]):
        self.tiles = tiles
        self.sets = list(sorted(sets))
        self.table = sorted(table)
        self.rack = sorted(rack)

        self.sets_matrix = np.array(
            [np.array([1 if self.tiles[i] in self.sets[j] else 0 for j in range(len(self.sets))]) for i in
             range(len(self.tiles))])
        self.table_array = np.array([self.table.count(self.tiles[i]) for i in range(len(self.tiles))])
        self.rack_array = np.array([self.rack.count(self.tiles[i]) for i in range(len(self.tiles))])

    def update_arrays(self):
        self.sets_matrix = np.array(
            [np.array([1 if self.tiles[i] in self.sets[j] else 0 for j in range(len(self.sets))]) for i in
             range(len(self.tiles))])
        self.table_array = np.array([self.table.count(self.tiles[i]) for i in range(len(self.tiles))])
        self.rack_array = np.array([self.rack.count(self.tiles[i]) for i in range(len(self.tiles))])

    def add_rack(self, additions):
        for i in additions:
            self.rack.append(i)
            self.rack = sorted(self.rack)
            self.update_arrays()

    def remove_rack(self, removals):
        for i in removals:
            self.rack.remove(i)
            self.update_arrays()

    def add_table(self, additions):
        for i in additions:
            self.table.append(i)
            self.table = sorted(self.table)
            self.update_arrays()

    def remove_table(self, removals):
        for i in removals:
            self.table.remove(i)
            self.update_arrays()

    def solve(self):
        i = range(len(self.tiles))
        j = range(len(self.sets))

        s = self.sets_matrix
        t = self.table_array
        r = self.rack_array

        x = cp.Variable(len(j), integer=True)
        y = cp.Variable(len(i), integer=True)

        obj = cp.Maximize(cp.sum(y))
        constraints = [
            s @ x == t + y,
            y <= r,
            -x <= 0,
            x <= 2,
            -y <= 0,
            y <= 2,
        ]

        prob = cp.Problem(obj, constraints)
        prob.solve(solver=cp.GLPK_MI)

        return prob.value, prob.solution.primal_vars[list(prob.solution.primal_vars.keys())[0]], \
               prob.solution.primal_vars[list(prob.solution.primal_vars.keys())[1]]