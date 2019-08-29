# pp_ga.py
"""
An optimal power flow algorithm based on a genetic algorithm for pandapower
networks.

Advantages compared to pre-implemented pandapower OPF:
TODO!

"""

import random

import numpy as np

import pandapower as pp


class GeneticAlgorithm:
    def __init__(self, pop_size: int, variables: tuple, net: object,
                 obj_fct='obj_P_loss'):
        # Number of individuums (possible solutions)
        self.pop_size = pop_size

        self.vars = variables

        # Pandapower network which state shall be optimized
        self.net = net

        # Choose fitness/objective function (attention: all objective
        # function must be written as minimization)
        if isinstance(obj_fct, str):
            # Select from pre-defined fitness functions (e.g. reduce loss)
            self.fit_fct = self.__dict__[obj_fct]
        else:
            # Self-made fitness function (objective function)
            self.fit_fct = obj_fct

        # Choose selection method
        self.selection = self.tournament

    def run(self, iter_max: int=None):
        """ Run genetic algorithm until termination. """
        if iter_max is not None:
            self.iter_max = iter_max
            self.termination = self.term_iter_max

        self.init_pop()

        # self.iter = 0
        # while True:
        #     self.fit_fct()
        #     if self.termination() is True:
        #         break
        #     self.selection()
        #     self.crossover()
        #     self.mutation()

        #     self.iter += 1

    def init_pop(self):
        """ Random initilization of the population. """
        self.pop = [self.random_ind() for _ in range(self.pop_size)]

    def random_ind(self):
        """ Initialize random individuum in the given search space. """
        ind = []
        for unit_type, actuator, idx in self.vars:
            if actuator == 'p_mw' or actuator == 'q_mvar':
                var = LmtNumber(
                    nmbr_type='float',
                    min_boundary=self.net[unit_type][f'min_{actuator}'][idx],
                    max_boundary=self.net[unit_type][f'max_{actuator}'][idx])
            elif actuator == 'tap_pos':
                var = LmtNumber(
                    nmbr_type='int',
                    min_boundary=self.net[unit_type]['tap_min'][idx],
                    max_boundary=self.net[unit_type]['tap_max'][idx])

            ind.append(var)

        return ind

    def term_iter_max(self):
        return bool(self.iter >= self.iter_max)

    def obj_P_loss(self):
        """ Objective function: minimize total active power losses in whole
        network. """
        for ind in self.pop:
            self.update_net(self.net, ind)
            pp.runpp(self.net)

            # TODO: any easier way than summing up?
            losses = 0
            losses += sum(self.net)

            ind.fitness = losses

    def tournament(self, group_size: int=4):
        """ Divive population in groups of size n and select the best
        individuum of each group. """

        self.parents = []
        for idx in range(0, self.pop_size, group_size):
            self.parents


class LmtNumber:
    """ A number that is restricted to a given range of values. """
    def __init__(self, nmbr_type: str, min_boundary, max_boundary,
                 set_value=None):


        assert nmbr_type in ('float', 'int')
        self.type = nmbr_type

        assert max_boundary > min_boundary
        self.min_boundary = min_boundary
        self.max_boundary = min_boundary
        self.range = self.max_boundary - self.min_boundary

        if set_value is not None:
            self.value = set_value
        else:
            self.value = self.random_init()

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, set_value):
        """ Make sure 'value' stays always within boundaries. """
        print(set_value, self.max_boundary, self.min_boundary)
        self._value = max(
            min(self.max_boundary, set_value), self.min_boundary)

    def random_init(self):
        """ Init value with a random number between the boundaries """
        if self.type == 'float':
            self.value = random.random() * self.range + self.min_boundary
        elif self.type == 'int':
            self.value = random.randint(self.min_boundary,
                                        self.max_boundary)