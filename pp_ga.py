# pp_ga.py
"""
An optimal power flow algorithm based on a genetic algorithm for pandapower
networks.

Advantages compared to pre-implemented pandapower OPF:
TODO!

"""

from copy import deepcopy

import matplotlib.pyplot as plt
import pandapower as pp

import genetic_operators
from util import Individuum
from penalty_fcts import penalty_fct


class GeneticAlgorithm(genetic_operators.Mixin):
    def __init__(self, pop_size: int, variables: tuple, net: object,
                 mutation_rate: float,
                 obj_fct='obj_p_loss', constraints: tuple='all',
                 selection='tournament'):
        self.pop_size = pop_size
        self.vars = variables
        self.mutation_rate = mutation_rate
        self.constraints = constraints

        # Pandapower network which state shall be optimized (Make sure that original net does not get altered! -> deepcopy)
        self.net = deepcopy(net)

        # Choose objective function (attention: all objective
        # functions must be written as minimization!)
        if isinstance(obj_fct, str):
            # Select from pre-defined fitness functions (e.g. reduce loss)
            import obj_functs
            self.obj_fct = getattr(obj_functs, obj_fct)
        else:
            # Self-made fitness function (objective function)
            self.obj_fct = obj_fct

        # Choose selection method (TODO: Make manual selection possible!)
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

        self.opt_net, _ = self.update_net(self.net, self.best_ind)

        print(self.best_ind.fitness)
        print(self.opt_net.sgen)
        print(self.opt_net.res_bus)
        print(self.opt_net.trafo)

        # Plot results
        plt.plot(self.best_fit_course)
        # plt.plot(self.avrg_fit_course)
        plt.show()

        return self.opt_net, self.best_ind.fitness

    def init_pop(self):
        """ Random initilization of the population. """
        self.pop = [Individuum(self.vars, self.net)
                    for _ in range(self.pop_size)]
        self.best_ind = self.pop[0]

    def fit_fct(self):
        """ Calculate fitness for each individuum, including penalties for
        constraint violations. """
        worst_fit = -1000000
        for ind in self.pop:
            net, failure = self.update_net(self.net, ind)
            if failure is True:
                ind.failure = True
                continue

            # Check if constraints are violated and calculate penalty
            penalty, valid = penalty_fct(net, self.constraints)

            # Assign fitness value to each individuum
            ind.fitness = self.obj_fct(net=net) + penalty
            if ind.fitness > worst_fit:
                worst_fit = ind.fitness
            ind.penalty = penalty
            ind.valid = valid

        # Punish individuals were power flow calculation failed so that they
        # are the worst individuals in population
        for ind in self.pop:
            if ind.failure is True:
                ind.fitness = worst_fit + abs(worst_fit)

        # Evaluation of fitness values
        best_ind = min(self.pop, key=lambda ind: ind.fitness)
        self.best_fit_course.append(best_ind.fitness)
        if best_ind.fitness < self.best_ind.fitness:
            # TODO: only accept best individuum if valid=True (constraints!)
            self.best_ind = best_ind
        average_fitness = sum(
            [ind.fitness for ind in self.pop])/len(self.pop)
        self.avrg_fit_course.append(average_fitness)

    def term_iter_max(self):
        """ Terminate if max iteration number is reached. """
        return bool(self.iter >= self.iter_max)

    def update_net(self, net, ind):
        """ Update a given pandapower network to the state of a single
        individuum and perform power flow calculation. """

        # Update the actuators to be optimized
        for (unit_type, actuator, idx), nmbr in zip(self.vars, ind):
            net[unit_type][actuator][idx] = nmbr.value

        # Update the power flow results by performing pf-calculation
        failure = False
        try:
            pp.runpp(net)
        except:
            print('Power flow calculation failed')
            failure = True

        return net, failure
