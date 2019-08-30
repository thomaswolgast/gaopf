# genetic_operators.py
"""
A collection of genetic operators for the pandapower ga-OPF, including selection, crossover, and mutation operators.

"""


class Mixin:
    def tournament(self, group_size: int=4):
        """ Tournament selection: Divive population in groups of size n and
        select the best individuum of each group as parent. """

        self.parents = []
        for idx in range(0, self.pop_size, group_size):
            parent = min(self.pop, key=lambda ind: ind.fitness)
            self.parents.append(parent)
