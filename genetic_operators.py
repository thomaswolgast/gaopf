# genetic_operators.py
"""
A collection of genetic operators for the pandapower ga-OPF, including selection, crossover, and mutation operators.

"""

import random

import numpy as np

from .util import Individuum


class Mixin:
    # ---------------------Selection operators-------------------------
    def tournament(self, group_size: int=3):
        """ Tournament selection: Divive population in groups of size n and
        select the best individuum of each group as parent. """

        self.parents = []
        for idx in range(0, self.pop_size, group_size):
            group = self.pop[idx:(idx+group_size)]
            parent = min(group, key=lambda ind: ind.fitness)
            self.parents.append(parent)

    # ---------------------Crossover operators-------------------------
    def recombination(self, cross_operator: str='average'):
        """ Choose two parents randomly and combine them a single child. """
        self.pop = []

        for _ in range(self.pop_size):
            parent1 = random.choice(self.parents)
            parent2 = random.choice(self.parents)
            crossover = getattr(self, cross_operator)
            child_chromosomes = crossover(parent1, parent2)
            child = Individuum(self.vars, self.net, child_chromosomes)
            self.pop.append(child)

    def single_point(self, parent1, parent2):
        """ Single Point Crossover: Divide chromosomes at one random point
        and recombine them. """
        cut_point = random.randint(0, len(self.vars))
        child_chromosomes = parent1[0:cut_point] + parent2[cut_point:]
        return child_chromosomes

    def average(self, parent1, parent2):
        """ Average crossover: The child is the exact average of both
        parents. Attention: Only applicable to floats! """
        child_chromosomes = [(gene1+gene2)/2
                             for gene1, gene2 in zip(parent1, parent2)]
        return child_chromosomes

    # ---------------------Mutation operators-------------------------
    def mutation(self, mutation_rate: float):
        """ Mutation: Adjust a single gene of every individuum with a small
        probability. """
        randoms = np.random.rand(len(self.pop), len(self.vars))
        for idx1, ind in enumerate(self.pop):
            for idx2, gene in enumerate(ind):
                if randoms[idx1, idx2] < mutation_rate:
                    # TODO: Include other mutations!
                    self.randomize(gene)

    def randomize(self, value):
        """ Adjust value to random new value within given boundaries. """
        value.random_init()
