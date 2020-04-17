import numpy as np

from itertools import combinations


class SetGenerator:

    def __init__(self, numbers=13, colours=4, jokers=2, min_len=3):
        self.numbers = numbers
        self.colours = colours
        self.jokers = jokers
        self.min_len = min_len
        self.tiles = self.generate_tiles()
        self.runs = set()
        self.groups = set()
        self.sets = set()
        self.generate_sets()

    def generate_tiles(self):
        return list(range(1, self.numbers * self.colours + 1 + (1 if self.jokers else 0)))

    def generate_sets(self):
        self.runs = self.generate_runs()
        self.groups = self.generate_groups()
        self.sets = self.runs.copy()
        self.sets.update(self.groups)

    def generate_runs(self):
        runs = {()}
        for l in range(self.min_len, self.min_len * 2):
            for c in range(0, self.colours):
                for n in range(1, self.numbers - l + 2):
                    start_num = n + self.numbers * c
                    end_num = start_num + l
                    num_run = set(range(start_num, end_num))
                    combs = self.clean_jokers([sorted(comb) for comb in combinations(
                        [*num_run, *[self.tiles[-1] + i for i in range(0, self.jokers)]], l)])
                    runs.update(combs)
        return runs

    def generate_groups(self):
        groups = set()
        for n in range(1, self.numbers + 1):
            num_group = list(range(n, self.numbers * self.colours + 1, self.numbers))
            for l in range(self.min_len, self.colours + 1):
                combs = self.clean_jokers([sorted(comb) for comb in combinations(
                    [*num_group, *[self.tiles[-1] + i for i in range(0, self.jokers)]], l)])
                groups.update(combs)
        return groups

    def clean_jokers(self, combs):
        joker = self.tiles[-1]
        jokers = list(range(joker, joker + self.jokers))
        for i in range(len(combs)):
            for j in range(len(combs[i])):
                if combs[i][j] in jokers:
                    combs[i][j] = joker
        combs = [tuple(c) for c in combs]
        return combs
