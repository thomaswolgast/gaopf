# pp_ga.py
"""
An optimal power flow algorithm based on a genetic algorithm for pandapower
networks.

Advantages compared to pre-implemented pandapower OPF:
TODO!

"""

import matplotlib.pyplot as plt
import pandapower as pp

from . import genetic_operators
from .util import Individuum
from .penalty_fcts import penalty_fct


class GeneticAlgorithm(genetic_operators.Mixin):
    def __init__(self, pop_size: int, variables: tuple, net: object,
                 mutation_rate: float,
                 obj_fct='obj_p_loss', constraints: tuple='all',
                 selection='tournament'):
        self.pop_size = pop_size
        self.vars = variables
        self.mutation_rate = mutation_rate
        self.constraints = constraints

        # Pandapower network which state shall be optimized
        self.net = net

        # Choose objective function (attention: all objective
        # function must be written as minimization)
        if isinstance(obj_fct, str):
            # Select from pre-defined fitness functions (e.g. reduce loss)
            from . import obj_functs
            # TODO: Nicer way to do this?
            self.obj_fct = obj_functs.__dict__[obj_fct]
        else:
            # Self-made fitness function (objective function)
            self.obj_fct = obj_fct

        # Choose selection method
        self.selection = self.tournament

        self.best_fit_course = []
        self.avrg_fit_course = []
        self.iter = 0

    def run(self, iter_max: int=None):
        """ Run genetic algorithm until termination. """
        if iter_max is not None:
            self.iter_max = iter_max
            self.termination = self.term_iter_max

        self.init_pop()

        while True:
            print(f'Step {self.iter}')
            self.fit_fct()
            if self.termination() is True:
                break
            self.selection()
            self.recombination('single_point')
            self.mutation(self.mutation_rate)

            self.iter += 1

        self.opt_net = self.update_net(self.net, self.best_ind)

        print(self.best_ind.fitness)
        print(self.opt_net.sgen)
        print(self.opt_net.res_bus)

        # Plot results
        plt.plot(self.best_fit_course)
        # plt.plot(self.avrg_fit_course)
        plt.show()

        return self.opt_net, self.best_ind.fitness

    def init_pop(self):
        """ Random initilization of the population. """
        self.pop = [Individuum(self.vars, self.net)
                    for _ in range(self.pop_size)]

    def fit_fct(self):
        """ Calculate fitness for each individuum, including penalties for
        constraint violations. """
        for ind in self.pop:
            net = self.update_net(self.net, ind)
            penalty, valid = penalty_fct(net, self.constraints)

            # Assign fitness value to each individuum
            ind.fitness = self.obj_fct(net=net) + penalty
            ind.penalty = penalty
            ind.valid = valid

        self.best_ind = min(self.pop, key=lambda ind: ind.fitness)
        # TODO: only accept best individuum if valid=True (constraints!)
        self.best_fit_course.append(self.best_ind.fitness)
        average_fitness = sum(
            [ind.fitness for ind in self.pop])/len(self.pop)
        self.avrg_fit_course.append(average_fitness)

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
            print('Power flow calculation failed')
            ind.failure = True
            # TODO: How to punish failure here -> worst fitness!

        return net
