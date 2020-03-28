# performance.py
"""
Template to run performance tests to improve ga algorithm

"""

import copy
import time

import examples
from ga import pp_ga


def main():
    ga = scenario()

    gas = (scenario1(copy.deepcopy(ga)), scenario2(copy.deepcopy(ga)), scenario3(copy.deepcopy(ga)))
    n_runs = 10
    costs = []
    times = []
    for ga in gas:
        start = time.time()
        cost = sum([ga.run(iter_max=50)[1] for _ in range(n_runs)])/n_runs
        times.append(time.time() - start)
        costs.append(cost)

    for ga, cost, t in zip(gas, costs, times):
        print('Mutation rate: ', ga.mutation_rate)
        print('Average costs: ', cost)
        print('Time consumption: ', t)
        print()


def scenario():
    net = examples.create_net2()

    # Degrees of freedom for optimization
    variables = (('sgen', 'q_mvar', 0),
                 ('sgen', 'q_mvar', 1),
                 ('sgen', 'q_mvar', 2),
                 ('sgen', 'q_mvar', 3),
                 ('sgen', 'q_mvar', 4),
                 ('sgen', 'q_mvar', 5),
                 ('sgen', 'q_mvar', 6),
                 ('sgen', 'q_mvar', 7),
                 ('sgen', 'q_mvar', 8),
                 ('trafo', 'tap_pos', 0),
                 ('trafo', 'tap_pos', 1))

    ga = pp_ga.GeneticAlgorithm(pop_size=100, variables=variables,
                                net=net, mutation_rate=0.001,
                                obj_fct='min_p_loss',
                                constraints='all')

    return ga


def scenario1(ga):
    """ standard settings """
    ga.mutation_rate = 0.05
    return ga


def scenario2(ga):
    """ standard settings """
    ga.mutation_rate = 0.02
    return ga


def scenario3(ga):
    """ standard settings """
    ga.mutation_rate = 0.01
    return ga


if __name__ == '__main__':
    main()
