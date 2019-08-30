# genetic_operators.py
"""
A collection of genetic operators for the pandapower ga-OPF, including selection, crossover, and mutation operators.

"""

import random

from util import Individuum


class Mixin:
    # ---------------------Selection operators-------------------------
    def tournament(self, group_size: int=2):
        """ Tournament selection: Divive population in groups of size n and
        select the best individuum of each group as parent. """

        self.parents = []
        for idx in range(0, self.pop_size, group_size):
            parent = min(self.pop, key=lambda ind: ind.fitness)
            self.parents.append(parent)

    # ---------------------Crossover operators-------------------------
    def recombination(self, cross_operator: str='single_point'):
        """ Choose two parents randomly and combine them a single child. """
        self.pop = []

        for _ in range(self.pop_size):
            parent1 = random.choice(self.parents)
            parent2 = random.choice(self.parents)
            child = getattr(self, cross_operator)(parent1, parent2)
            self.pop.append(child)

    def single_point(self, parent1, parent2):
        """ Single Point Crossover: Divide chromosomes at one random point
        and recombine them. """
        cut_point = random.randint(0, len(self.vars))
        child_chromosomes = parent1[0:cut_point] + parent2[cut_point:]
        child = Individuum(self.vars, self.net, child_chromosomes)
        return child
