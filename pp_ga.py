# pp_ga.py
"""
An optimal power flow algorithm based on a genetic algorithm for pandapower
networks.

"""

from copy import deepcopy
import datetime
import json
import os
import sys

import matplotlib.pyplot as plt
import pandas as pd
import pandapower as pp

from . import genetic_operators
from .util import Individual
from .penalty_fcts import penalty_fct


class GeneticAlgorithm(genetic_operators.Mixin):
    def __init__(self,
                 pop_size: int,
                 variables: list,
                 net: object,
                 mutation_rate: float,  # TODO: Find good default!
                 obj_fct='obj_p_loss',
                 constraints: tuple='all',
                 selection: str='tournament',
                 crossover: str='single_point',
                 mutation: dict={'random_init': 1.0},
                 termination: str='cmp_last',
                 plot: bool=False,
                 save: bool=False):
        """
        pop_size: Population size; number of parallel solutions (called
        individuals here).

        variables: All degrees of freedom for optimization. A list of tuples
        like: (unit_type, actuator, index), e.g. ('sgen', 'p_mv', 1).

        net: A pandapower net object with defined constraints.

        mutation_rate: The probability a single variable gets altered
        randomly. Look into genetic algorithm literature for information.

        obj_fct: A user- or pre-defined objective function to minimize. Use
        your own function here or use string of pre-defined function name.
        See "obj_functs.py" for pre-implemented functions like 'min_p_loss'.

        constraints: A tuple of system constraints to consider. Options are:
        ('voltage_band', 'line_load', 'trafo_load', 'trafo3w_load').
        If constraints is set to 'all', all of the above are considered.
        (Constraints like max/min p/q/tap are always considerd and must be
        defined!)

        selection: A string that defines the selection operator. Normally no
        adjustment required! See "genetic_operators.py" for possible options.

        crossover: Same as for selection operator.

        mutation: Dictionary that defines the mutation operators to use and
        their respective probabilities. See "genetic_operators.py".

        termination: String that defines criterion for termination of the
        optimization. Possibilities are:
        'cmp_avrg': Compare best to average solution. Terminate if similar.
        'cmp_last': Compare best solution to best solutions n steps before.
        Terminate if only marginal improvement.
        For both, 10^-3 is the boundary for termination.

        plot: If True -> Course of best results gets plotted in the end.
        (Warning: stops running of the code! Set save=True to prevent that)

        save: If True -> Save results and logger to newly created folder.
        Plot into that folder, too.

        """

        assert (len(variables) >= 1), 'Error: No degrees of Freedom!'

        self.pop_size = pop_size
        self.vars = variables
        self.mutation_rate = mutation_rate
        self.constraints = constraints
        self.termination_crit = termination

        # Pandapower network which state shall be optimized (Make sure that
        # original net does not get altered! -> deepcopy)
        self.net = deepcopy(net)

        self.assert_unit_state('controllable')
        self.assert_unit_state('in_service')
        self.set_defaults()

        # Choose objective function (attention: all objective
        # functions must be written as minimization!)
        if isinstance(obj_fct, str):
            # Select from pre-defined objective functions (e.g. reduce loss)
            from . import obj_functs
            self.obj_fct = getattr(obj_functs, obj_fct)
        else:
            # Self-made objective function
            self.obj_fct = obj_fct

        self.sel_operator = selection
        self.cross_operator = crossover
        self.mut_operators = mutation

        self.total_best_fit_course = []
        self.best_fit_course = []
        self.avrg_fit_course = []

        self.plot = plot
        self.save = save

        if save is True:
            self.create_path()

    def assert_unit_state(self, status: str='controllable'):
        """ Assert that units to be optimized are usable beforehand by
        checking 'in_service' or 'controllable' of each actuator. If they
        are not defined, they are assumed to be True. """
        for unit_type, _, idx in self.vars:
            if status not in self.net[unit_type]:
                print(f"'{status}' of {unit_type}_{idx} not defined. Assumed to be True!")
            else:
                assert bool(self.net[unit_type][status][idx]) is True, f"""
                Error: {unit_type}-{idx} is not '{status}'!"""

    def set_defaults(self):
        """ If some boundaries are not given, set them to default value. """
        # TODO: Do only, if voltage band is constraint
        if 'min_vm_pu' not in self.net.bus:
            u_min = 0.9
            self.net.bus['min_vm_pu'] = pd.Series(
                [u_min for _ in self.net.bus.index], index=self.net.bus.index)
            print(f'Set "min_vm_pu" to default ({u_min}) for all buses')

        if 'max_vm_pu' not in self.net.bus:
            u_max = 1.1
            self.net.bus['max_vm_pu'] = pd.Series(
                [u_max for _ in self.net.bus.index], index=self.net.bus.index)
            print(f'Set "max_vm_pu" to default ({u_max}) for all buses')

        # TODO: Do only, if loading is constraint
        for unit in ('trafo', 'trafo3w', 'line'):
            if len(self.net[unit].index) == 0:
                continue
            if 'max_loading_percent' not in self.net[unit]:
                max_loading = 100
                self.net[unit]['max_loading_percent'] = pd.Series(
                    [max_loading for _ in self.net[unit].index],
                    index=self.net[unit].index)
                print(f'Set "max_loading_percent" to default ({max_loading}) for all "{unit}"')

    def run(self, iter_max: int=None):
        """ Run genetic algorithm until termination. Return optimized
        pandapower network and the value of the respective objective fct. """
        self.iter_max = iter_max

        self.init_pop()

        self.iter = 0
        while True:
            print(f'Step {self.iter}')
            self.fit_fct()
            if self.termination() is True:
                break
            self.selection(sel_operator=self.sel_operator)
            self.recombination(cross_operator=self.cross_operator)
            self.mutation(self.mutation_rate,
                          mut_operators=self.mut_operators)

            self.iter += 1

        if self.best_ind.valid is False:
            # TODO: proper logging instead!
            # Or raise error here like pandapower does?
            print(f'Attention: Solution does not fulfill all constraints!')

        self.opt_net, _ = self.update_net(self.net, self.best_ind)
        self.create_result()
        self.save_net(best_net=self.opt_net)

        # Plot results
        if self.plot is True:
            self.plot_fit_courses()

        return self.opt_net, self.best_ind.fitness

    def init_pop(self):
        """ Random initilization of the population. """
        self.pop = [Individual(self.vars, self.net)
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

        # Delete individuals with failed power flow (not evaluatable)
        self.pop = tuple(filter(lambda ind: not ind.failure, self.pop))

        # Evaluation of fitness values
        best_ind = min(self.pop, key=lambda ind: ind.fitness)
        self.best_fit_course.append(best_ind.fitness)
        if (best_ind.fitness < self.best_ind.fitness):
            self.best_ind = best_ind
        self.total_best_fit_course.append(self.best_ind.fitness)

        average_fitness = sum(
            [ind.fitness for ind in self.pop]) / len(self.pop)
        self.avrg_fit_course.append(average_fitness)

    def termination(self):
        """ Terminate if max iteration number is reached. """
        if self.iter_max:
            if self.iter >= self.iter_max:
                return True

        # TODO: make functions for everyone of these?!
        if self.termination_crit == 'cmp_last':
            iter_range = round(self.iter * 0.2) + 5
            # TODO: Hardcoded! (Make it variable? User can define "early" or "late" termination)
            if self.iter > iter_range:
                improvement = self.total_best_fit_course[-iter_range - 1] - self.total_best_fit_course[-1]
                try:
                    rel_improvement = (improvement
                        / self.total_best_fit_course[-iter_range - 1])
                except ZeroDivisionError:
                    return True
                min_improvement = 10**-3  # TODO: Hardcoded!
                print(f'Relative improvement in last {iter_range} steps: {rel_improvement}')
                if rel_improvement < min_improvement:
                    return True

        if self.termination_crit == 'cmp_avrg':
            diff_to_avrg = self.avrg_fit_course[-1] - self.total_best_fit_course[-1]
            rel_diff_to_avrg = diff_to_avrg / self.avrg_fit_course[-1]
            min_difference = 10**-3  # TODO: Hardcode
            print(f'Relative difference to average: {rel_diff_to_avrg}')
            if rel_diff_to_avrg < min_difference:
                return True

    def update_net(self, net, ind):
        """ Update a given pandapower network to the state of a single
        individual and perform power flow calculation. """

        # Update the actuators to be optimized
        for (unit_type, actuator, idx), nmbr in zip(self.vars, ind):
            net[unit_type][actuator][idx] = nmbr.value

        # Update the power flow results by performing pf-calculation
        failure = False
        try:
            pp.runpp(net, enforce_q_lims=True)
        except KeyboardInterrupt:
            print('Optimization interrupted by user!')
            sys.exit()
        except:
            print('Power flow calculation failed!')
            # TODO: Include unit test to make sure this works!
            failure = True

        return net, failure

    def plot_fit_courses(self, average_inclusive=False):
        """ Plot the total best fitness value, the best fitness value of the
        respective step as course over the iterations. (Optionally: Plot the
        average fitness. Problematic because of penalties) """

        plt.plot(self.best_fit_course, label='Best costs')
        plt.plot(self.total_best_fit_course, label='Total best costs')
        if average_inclusive is True:
            plt.plot(self.avrg_fit_course, label='Average costs')
        plt.legend(loc='upper right')

        plt.ylabel('Total costs')
        plt.xlabel('Iteration number')

        if self.save is True:
            format_type = 'png'
            plt.savefig(f'{self.path}optimization_course.{format_type}',
                        format=format_type,
                        bbox_inches='tight')
            plt.close()
        else:
            plt.show()

    def create_path(self):
        """ Create folder for data saving. The name of the folder is the
        current date and time. Attention: time in virtualbox and time in host
        system are not always synchronous! """
        t = datetime.datetime.now().replace(microsecond=0).isoformat()
        self.path = f'ga_opf_pp/Results/{t}/'.replace(':', '.').replace('T', ' ')
        os.makedirs(self.path)

    def save_net(self, best_net, format_='pickle'):
        """ Save pandapower network to pickle file. """
        if self.save is True:
            filename = 'best_net'
            if format_ == 'pickle':
                pp.to_pickle(best_net, self.path+filename+'.p')
            elif format_ == 'json':
                pp.to_json(best_net, self.path+filename+'.json')
            else:
                print(f'File format "{format_}" not implemented yet!')

    def create_result(self):
        """ Create tuple of the variables and what best values were found for
        them. """
        self.result = tuple(
            [a, b, c, float(d.value)]
            for (a, b, c), d in zip(self.vars, self.best_ind))

        if self.save:
            with open(f'{self.path}results.json', 'w') as file:
                json.dump(self.result, file)
