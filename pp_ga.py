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

from . import genetic_operators
from .util import Individuum
from .penalty_fcts import penalty_fct


class GeneticAlgorithm(genetic_operators.Mixin):
    def __init__(self, pop_size: int,
                 variables: tuple,
                 net: object,
                 mutation_rate: float,
                 obj_fct='obj_p_loss',
                 constraints: tuple='all',
                 selection: str='tournament',
                 crossover: str='single_point',
                 mutation: dict={'random_init': 1.0},
                 termination: str='none'): #option for termination: 'None', 'cmp_last', 'cmp_average'
        """ TODO: proper documentation. """
        self.pop_size = pop_size
        self.vars = variables
        self.mutation_rate = mutation_rate
        self.constraints = constraints
        self.termination_criteria = termination

        # Pandapower network which state shall be optimized (Make sure that
        # original net does not get altered! -> deepcopy)
        self.net = deepcopy(net)

        self.assert_unit_state('controllable')
        self.assert_unit_state('in_service')

        # Choose objective function (attention: all objective
        # functions must be written as minimization!)
        if isinstance(obj_fct, str):
            # Select from pre-defined objective functions (e.g. reduce loss)
            from . import obj_functs
            self.obj_fct = getattr(obj_functs, obj_fct)
        else:
            # Self-made objective function
            self.obj_fct = obj_fct

        # Choose selection method (TODO: Make manual selection possible!)
        self.sel_operator = selection
        self.cross_operator = crossover
        self.mut_operators = mutation

        self.best_fit_course = []
        self.avrg_fit_course = []
        self.iter = 0


    def assert_unit_state(self, status: str='controllable'):
        """ Assert that units to be optimized are usable beforehand by
        checking 'in_service' or 'controllable' of each actuator. If they
        are not defined, they are assumed to be True. """
        for unit_type, actuator, idx in self.vars:
            if status not in self.net[unit_type]:
                print(f"'{status}' not defined. Assumed to be True!")
                break
            else:
                assert bool(self.net[unit_type][status][idx]) is True, f"""
                            Error: {unit_type}-{idx} is not '{status}'!"""

    def run(self, iter_max: int=None):
        """ Run genetic algorithm until termination. """
        if iter_max is not None:
            self.iter_max = iter_max
            self.termination = self.term_iter_max

        self.init_pop()

        while True:
            if self.iter > 3 and self.termination_criteria == 'cmp_last':
                print(f'Step {self.iter}, diff to last: {(self.best_fit_course[-1]-self.best_fit_course[-2])**2}')
            elif self.iter > 3 and self.termination_criteria == 'cmp_average':
                print(f'Step {self.iter}, diff to average: {(self.best_fit_course[-1]-self.avrg_fit_course[-1])**2}')
            else:
                print(f'Step {self.iter}')
            self.fit_fct()
            if self.termination() is True:
                break
            self.selection(sel_operator=self.sel_operator)
            self.recombination(cross_operator=self.cross_operator)
            self.mutation(self.mutation_rate,
                          mut_operators=self.mut_operators)

            self.iter += 1

        self.opt_net, _ = self.update_net(self.net, self.best_ind)

        # Delete! -> proper logging!
        print(self.best_ind.fitness)
        print(self.opt_net.sgen)
        print(self.opt_net.res_bus)
        print(self.opt_net.trafo)

        # Plot results
        # plt.plot(self.best_fit_course)
        # plt.plot(self.avrg_fit_course)
        # plt.show()

        return self.opt_net, self.best_ind.fitness

    def init_pop(self):
        """ Random initilization of the population. """
        self.pop = [Individuum(self.vars, self.net)
                    for _ in range(self.pop_size)]
        self.best_ind = self.pop[0]
        self.best_ind.fitness = 1e9

    def fit_fct(self):
        """ Calculate fitness for each individual, including penalties for
        constraint violations which gets added to the objective function. """
        for ind in self.pop:
            net, ind.failure = self.update_net(self.net, ind)

            # Check for failed power flow calculation
            if ind.failure is True:
                continue

            # Check if constraints are violated and calculate penalty
            ind.penalty, ind.valid = penalty_fct(net, self.constraints)

            # Assign fitness value to each individual
            ind.fitness = self.obj_fct(net=net) + ind.penalty

        # Delete individuals with failed power flow
        self.pop = [ind for ind in self.pop if not ind.failure]

        # Evaluation of fitness values
        best_ind = min(self.pop, key=lambda ind: ind.fitness)
        self.best_fit_course.append(best_ind.fitness)
        if (best_ind.fitness < self.best_ind.fitness) and best_ind.valid:
            self.best_ind = best_ind

        average_fitness = sum(
            [ind.fitness for ind in self.pop])/len(self.pop)
        self.avrg_fit_course.append(average_fitness)

    def term_iter_max(self):
        """ Terminate if max iteration number is reached. """
        if self.iter >= self.iter_max:
            return True

        if self.iter > 2:
            if self.termination_criteria == 'cmp_last' and (self.best_fit_course[-1]-self.best_fit_course[-2])**2 < 10**-3:
                return True

            if self.termination_criteria == 'cmp_average' and (self.best_fit_course[-1]-self.avrg_fit_course[-1])**2 < 10**-3:
                return True

        return bool(self.iter >= self.iter_max)

    def update_net(self, net, ind):
        """ Update a given pandapower network to the state of a single
        individual and perform power flow calculation. """

        # Update the actuators to be optimized
        for (unit_type, actuator, idx), nmbr in zip(self.vars, ind):
            net[unit_type][actuator][idx] = nmbr.value

        # Update the power flow results by performing pf-calculation
        failure = False
        try:
            pp.runpp(net)
        except:
            print('Power flow calculation failed!')
            failure = True

        return net, failure
