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

import genetic_operators


class GeneticAlgorithm(genetic_operators.Mixin):
    def __init__(self, pop_size: int, variables: tuple, net: object,
                 obj_fct='obj_p_loss', penalty_fct='voltage_band',
                 selection='tournament'):
        # Number of individuums (possible solutions)
        self.pop_size = pop_size

        self.vars = variables

        # Pandapower network which state shall be optimized
        self.net = net

        # Choose objective function (attention: all objective
        # function must be written as minimization)
        if isinstance(obj_fct, str):
            # Select from pre-defined fitness functions (e.g. reduce loss)
            import obj_functs
            # TODO: Nicer way to do this?
            self.obj_fct = obj_functs.__dict__[obj_fct]
        else:
            # Self-made fitness function (objective function)
            self.obj_fct = obj_fct

        # Choose penalty function to punish constraint violations (gets
        # added to the fitness)
        if isinstance(penalty_fct, str):
            # Select from pre-defined penalty functions (e.g. voltage only)
            import penalty_fcts
            # TODO: Nicer way to do this?
            self.penalty_fct = penalty_fcts.__dict__[penalty_fct]
        else:
            # Self-made fitness function (objective function)
            self.penalty_fct = penalty_fct

        # Choose selection method
        self.selection = self.tournament

    def run(self, iter_max: int=None):
        """ Run genetic algorithm until termination. """
        if iter_max is not None:
            self.iter_max = iter_max
            self.termination = self.term_iter_max

        self.init_pop()

        self.iter = 0
        while True:
            print(f'Step {self.iter}')
            self.fit_fct()
            print(self.best_ind.fitness)
            if self.termination() is True:
                break
            self.selection()
            print(self.parents)
        #     self.crossover()
        #     self.mutation()

            self.iter += 1

    def init_pop(self):
        """ Random initilization of the population. """
        self.pop = [Individuum(self.vars, self.net)
                    for _ in range(self.pop_size)]

    def fit_fct(self):
        """ Calculate fitness for each individuum, including penalties for
        constraint violations. """
        for ind in self.pop:
            net = self.update_net(self.net, ind)
            penalty, valid = self.penalty_fct(net=net)

            # Assign fitness value to each individuum
            ind.fitness = self.obj_fct(net=net) + penalty
            ind.valid = valid

        self.best_ind = min(self.pop, key=lambda ind: ind.fitness)

    def term_iter_max(self):
        return bool(self.iter >= self.iter_max)

    def update_net(self, net, ind):
        """ Update a given pandapower network to the state of a single
        individuum and perform power flow calculation. """
        for (unit_type, actuator, idx), nmbr in zip(self.vars, ind):
            net[unit_type][actuator][idx] = nmbr.value

        try:
            pp.runpp(net)
        except:
            ind.failure = True
            # TODO: How to punish failure here -> worst fitness!

        return net


class Individuum:
    def __init__(self, vars_in: tuple, net: object):
        self.random_init(vars_in, net)
        self.reset()

    def random_init(self, vars_in, net):
        self.vars = []
        for unit_type, actuator, idx in vars_in:
            if actuator == 'p_mw' or actuator == 'q_mvar':
                var = LmtNumber(
                    nmbr_type='float',
                    min_boundary=net[unit_type][f'min_{actuator}'][idx],
                    max_boundary=net[unit_type][f'max_{actuator}'][idx])
            elif actuator == 'tap_pos':
                var = LmtNumber(
                    nmbr_type='int',
                    min_boundary=net[unit_type]['tap_min'][idx],
                    max_boundary=net[unit_type]['tap_max'][idx])

            self.vars.append(var)

    def reset(self):
        self.fitness = None
        # Did this individuum lead to failed power flow calculation?
        self.failure = None
        # Valid solution? All constraints satisfied?
        self.valid = None

    def __iter__(self):
        yield from self.vars


class LmtNumber:
    """ A number that is restricted to a given range of values. """
    def __init__(self, nmbr_type: str, min_boundary, max_boundary,
                 set_value=None):
        assert nmbr_type in ('float', 'int')
        self.type = nmbr_type

        assert max_boundary > min_boundary
        self.min_boundary = min_boundary
        self.max_boundary = max_boundary
        self.range = self.max_boundary - self.min_boundary

        if set_value is not None:
            self.value = set_value
        else:
            self.value = self.random_init()

    def __repr__(self):
        return str(self.value)

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, set_value):
        """ Make sure 'value' stays always within boundaries. """
        self._value = max(
            min(self.max_boundary, set_value), self.min_boundary)

    def random_init(self):
        """ Init value with a random number between the boundaries """
        if self.type == 'float':
            return random.random() * self.range + self.min_boundary
        elif self.type == 'int':
            return random.randint(self.min_boundary, self.max_boundary)
