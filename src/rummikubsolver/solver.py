import cvxpy as cp
import numpy as np


class RummikubSolver:

    def __init__(self, tiles, sets, numbers=13, colours=4, rack=[], table=[]):
        self.tiles = np.array(tiles)
        self.sets = list(sorted(sets))
        self.table = sorted(table)
        self.rack = sorted(rack)

        self.value = np.array([v for c in range(colours) for v in range(1, numbers+1)])
        if self.value.shape != self.tiles.shape:
            self.value = np.append(self.value, 0)

        self.sets_matrix = np.array(
            [np.array([self.sets[j].count(self.tiles[i]) for j in range(len(self.sets))]) for i in
             range(len(self.tiles))])
        self.table_array = np.array([self.table.count(self.tiles[i]) for i in range(len(self.tiles))])
        self.rack_array = np.array([self.rack.count(self.tiles[i]) for i in range(len(self.tiles))])

    def update_arrays(self):
        self.table_array = np.array([self.table.count(self.tiles[i]) for i in range(len(self.tiles))])
        self.rack_array = np.array([self.rack.count(self.tiles[i]) for i in range(len(self.tiles))])

    def add_rack(self, additions):
        for i in additions:
            self.rack.append(i)
            self.rack = sorted(self.rack)
        self.update_arrays()

    def remove_rack(self, removals):
        for i in removals:
            try:
                self.rack.remove(i)
            except ValueError:
                print(f'{i} not on rack')
        self.update_arrays()

    def add_table(self, additions):
        for i in additions:
            self.table.append(i)
            self.table = sorted(self.table)
        self.update_arrays()

    def remove_table(self, removals):
        for i in removals:
            try:
                self.table.remove(i)
            except ValueError:
                print(f'{i} not on table')
        self.update_arrays()

    def solve(self, maximise='tiles', initial_meld=False):
        i = range(len(self.tiles))
        j = range(len(self.sets))

        s = self.sets_matrix
        if initial_meld:
            t = np.zeros(self.table_array.shape)
        else:
            t = self.table_array
        r = self.rack_array
        v = self.value

        x = cp.Variable(len(j), integer=True)
        y = cp.Variable(len(i), integer=True)

        if maximise == 'tiles':
            obj = cp.Maximize(cp.sum(y))
        elif maximise == 'value':
            obj = cp.Maximize(cp.sum(v @ y))
        else:
            print('Invalid maximise function')
            return 0, np.zeros(len(j)), np.zeros(len(i)),

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

        if len(list(prob.solution.primal_vars.keys())) == 0:
            print('No prob.solution.primal_vars')
            return 0, np.zeros(len(i)), np.zeros(len(j))

        return prob.value, prob.solution.primal_vars[list(prob.solution.primal_vars.keys())[0]], \
               prob.solution.primal_vars[list(prob.solution.primal_vars.keys())[1]]
