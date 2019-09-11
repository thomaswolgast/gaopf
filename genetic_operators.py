# genetic_operators.py
"""
A collection of genetic operators for the pandapower ga-OPF, including selection, crossover, and mutation operators.

"""

import random

import numpy as np

from .util import Individual


class Mixin:
    # ---------------------Selection operators-------------------------
    def selection(self, sel_operator: str='tournament'):
        """ Select above-average individuals from population and make them
        the 'parents' of this generation. The parents are used to produce
        the next generation of individuals. """
        self.parents = []
        getattr(self, sel_operator)()

    def tournament(self, group_size: int=3):
        """ Tournament selection: Divive population in groups of size n and
        select the best individual of each group as parent. """
        for idx in range(0, self.pop_size, group_size):
            group = self.pop[idx:(idx + group_size)]
            parent = min(group, key=lambda ind: ind.fitness)
            self.parents.append(parent)

    # ---------------------Crossover operators-------------------------
    def recombination(self, cross_operator: str='single_point'):
        """ Choose two parents randomly and combine them a single child. """
        self.pop = []

        for _ in range(self.pop_size):
            parent1 = random.choice(self.parents)
            parent2 = random.choice(self.parents)
            crossover = getattr(self, cross_operator)
            child_chromosomes = crossover(parent1, parent2)
            # Create new individual as child of two parents
            child = Individual(self.vars, self.net, child_chromosomes)
            self.pop.append(child)

    def single_point(self, parent1, parent2):
        """ Single Point Crossover: Divide chromosomes at one random point
        and recombine them. """
        cut_point = random.randint(1, len(self.vars) - 1)
        return parent1[0:cut_point] + parent2[cut_point:]

    def average(self, parent1, parent2):
        """ Average crossover: The child is the exact average of both
        parents. Attention: Only applicable to floats! """
        return [(gene1 + gene2) / 2 for gene1, gene2 in zip(parent1, parent2)]

    # ---------------------Mutation operators-------------------------
    def mutation(self, mutation_rate: float,
                 mut_operators: dict={'random_init': 1.0}):
        """ Mutation: Adjust a single gene of every individual with a small
        probability.

        Structure of 'mut_operators':
        {'operator1': probability of operator1, 'operator2': ...}

        Possible mutation operators:
        'random_init': re-initialize value randomly.
        'increase': increase value randomly.
        'decrease': decrease value randomly.
        """

        # Initialize diverse random numbers to decide how mutation goes
        randoms = np.random.rand(len(self.pop), len(self.vars), 2)
        # Check every gene of every individual if to mutate
        for idx1, ind in enumerate(self.pop):
            for idx2, gene in enumerate(ind):
                if randoms[idx1, idx2, 0] > mutation_rate:
                    continue

                # Perform mutation -> Decide which operator to use
                probability = 0
                for mut_operator, prob in mut_operators.items():
                    probability += prob
                    if prob <= randoms[idx1, idx2, 1]:
                        getattr(gene, mut_operator)()
