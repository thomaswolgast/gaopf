# examples.py
"""
Perform example optimizations of the genetic algorithm to demonstrate how it
can be used.

"""

import numpy as np
import pandas as pd
import pandapower as pp
import pandapower.networks as pn

try:
    from ga import pp_ga
    from ga.obj_functs import min_p_loss
except ImportError:
    from .ga import pp_ga
    from .ga.obj_functs import min_p_loss


def main():
    """ Show some examples and compare results with pandapower OPF """
    scenario1(save=False, plot=True)
    scenario1ref()
    scenario2(save=False, plot=True)
    scenario2ref()
    scenario3(save=False, plot=True)
    scenario3ref()


def scenario1(save=False, plot=False):
    """ GA-OPF on the grid from the simple pandapower-OPF tutorial. """
    # https://github.com/e2nIEE/pandapower/blob/master/tutorials/opf_basic.ipynb
    net = create_net1()
    variables = (('gen', 'p_mw', 0), ('gen', 'p_mw', 1),
                 ('gen', 'vm_pu', 0), ('gen', 'vm_pu', 1))

    ga = pp_ga.GeneticAlgorithm(pop_size=100, variables=variables,
                                net=net, mutation_rate=0.001,
                                obj_fct=obj_fct1,
                                plot=plot,
                                save=save)
    net_opt, best_costs = ga.run(iter_max=20)
    print(f'Costs for GA-OPF: {best_costs}')

    return net_opt, best_costs


def scenario1ref():
    """ pandapower-OPF as reference for scenario 1. """
    net = create_net1()
    pp.create_poly_cost(net, 0, 'ext_grid', cp1_eur_per_mw=10)
    pp.create_poly_cost(net, 0, 'gen', cp1_eur_per_mw=10)
    pp.create_poly_cost(net, 1, 'gen', cp1_eur_per_mw=10)
    pp.runopp(net)
    print(f'Costs for pandapower-OPF: {net.res_cost}')

    return net, net.res_cost


def scenario2(save=False, plot=False):
    """ Test OPF with larger network (cigre mv with pv and wind).
    Demonstrates the usage of tap-changable transformer. """
    net = create_net2()

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

    ga = pp_ga.GeneticAlgorithm(pop_size=150, variables=variables,
                                net=net, mutation_rate=0.001,
                                obj_fct='min_p_loss',
                                constraints='all',
                                plot=plot,
                                save=save)

    net_opt, best_costs = ga.run(iter_max=30)
    print(f'Costs of ga-OPF: {best_costs} (better than pandapower-OPF, because tap-changing is possible)')

    return net_opt, best_costs


def scenario2ref():
    """ pandapower-OPF as reference for scenario 2. """
    net = create_net2()
    pp.create_poly_cost(net, 0, 'ext_grid', cp1_eur_per_mw=1)
    for idx in net.sgen.index:
        pp.create_poly_cost(net, idx, 'sgen', cp1_eur_per_mw=1)
    for idx in net.load.index:
        pp.create_poly_cost(net, idx, 'load', cp1_eur_per_mw=-1)
    pp.runopp(net, verbose=False)

    costs = min_p_loss(net)  # Pandapower costs wrong: loads not considered!?
    print(f'Costs of pandapower-OPF: {costs}')

    return net, costs


def scenario3(save=False, plot=False):
    """ Large multi voltage level power grid that contains all possible
    elements. If this works, everything should work!
    https://pandapower.readthedocs.io/en/v2.1.0/networks/example.html """
    net = create_net3()

    variables = [('sgen', 'q_mvar', idx) for idx in net.sgen.index]
    variables += [('gen', 'vm_pu', idx) for idx in net.gen.index]
    variables += [('shunt', 'step', 0)]
    variables += [('trafo', 'tap_pos', 1)]
    variables += [('trafo3w', 'tap_pos', 0)]

    ga = pp_ga.GeneticAlgorithm(pop_size=150, variables=tuple(variables),
                                net=net, mutation_rate=0.001,
                                obj_fct='min_p_loss',
                                constraints='all',
                                plot=plot,
                                termination='cmp_last',
                                save=save)

    net_opt, best_costs = ga.run(iter_max=30)
    print(f'Costs of ga-OPF: {best_costs}')

    return net_opt, best_costs


def scenario3ref():
    net = create_net3()

    for actuator in ('ext_grid', 'gen', 'sgen'):
        for idx in net[actuator].index:
            pp.create_poly_cost(net, idx, actuator, cp1_eur_per_mw=1)
    for idx in net.load.index:
        pp.create_poly_cost(net, idx, 'load', cp1_eur_per_mw=-1)

    try:
        pp.runopp(net)
        costs = min_p_loss(net)  # Pandapower costs not working: loads are not considered!?
        print(f'Costs of pandapower-OPF: {costs}')
        return net, costs
    except pp.optimal_powerflow.OPFNotConverged:
        print('Pandapower-OPF did not converge for scenario 3! (Because tap-changing not possible?!)')
        return None, None


def obj_fct1(net):
    """ Objective function from simple pp-OPF tutorial. """
    costs = 0
    costs += sum(net.res_ext_grid['p_mw']) * 10
    costs += sum(net.res_gen['p_mw']) * 10

    return costs


def create_net1():
    """ Create net from simple pandapower-OPF tutorial. """
    net = pp.create_empty_network()

    # create buses
    bus1 = pp.create_bus(net, vn_kv=220.)
    bus2 = pp.create_bus(net, vn_kv=110.)
    bus3 = pp.create_bus(net, vn_kv=110.)
    bus4 = pp.create_bus(net, vn_kv=110.)

    # create 220/110 kV transformer
    pp.create_transformer(net, bus1, bus2, std_type="100 MVA 220/110 kV")

    # create 110 kV lines
    pp.create_line(net, bus2, bus3, length_km=70., std_type='149-AL1/24-ST1A 110.0')
    pp.create_line(net, bus3, bus4, length_km=50., std_type='149-AL1/24-ST1A 110.0')
    pp.create_line(net, bus4, bus2, length_km=40., std_type='149-AL1/24-ST1A 110.0')

    # create loads
    pp.create_load(net, bus2, p_mw=60, controllable=False)
    pp.create_load(net, bus3, p_mw=70, controllable=False)
    pp.create_load(net, bus4, p_mw=10, controllable=False)

    # create generators
    pp.create_ext_grid(net, bus1, min_p_mw=-1000, max_p_mw=1000)
    pp.create_gen(net, bus3, p_mw=80, min_p_mw=0, max_p_mw=80, vm_pu=1.01, controllable=True)
    pp.create_gen(net, bus4, p_mw=100, min_p_mw=0, max_p_mw=100, vm_pu=1.01, controllable=True)

    return net


def create_net2():
    """ Cigre MV: Net + constraints for optimal reactive power flow. """
    net = pn.create_cigre_network_mv(with_der='pv_wind')
    net = settings_opf(net)

    # Make trafo tap-changable with tap-range [-2, +2]
    net.trafo.tap_pos = pd.Series([0, 0], index=net.trafo.index)
    net.trafo.tap_neutral = pd.Series([0, 0], index=net.trafo.index)
    net.trafo.tap_min = pd.Series([-2, -2], index=net.trafo.index)
    net.trafo.tap_max = pd.Series([+2, +2], index=net.trafo.index)
    net.trafo.tap_step_percent = pd.Series([2.5, 2.5], index=net.trafo.index)
    net.trafo.tap_step_degree = pd.Series([0, 0], index=net.trafo.index)
    net.trafo.tap_side = pd.Series(['hv', 'hv'], index=net.trafo.index)

    # Make trafo controllable
    net.trafo['controllable'] = pd.Series(
        [True for _ in net.trafo.index], index=net.trafo.index)

    return net


def create_net3():
    """ 57 bus net with all kinds of elements. """
    net = pn.example_multivoltage()
    net = settings_opf(net)

    # Allow more loading (otherwise no valid solution)
    max_loading = 120
    net.line['max_loading_percent'] = pd.Series(
        [max_loading for _ in net.line.index], index=net.line.index)

    max_loading = 110
    net.trafo['max_loading_percent'] = pd.Series(
        [max_loading for _ in net.trafo.index], index=net.trafo.index)

    # Add maximum apparent power additional constraint (as example)
    for gen in ('gen', 'sgen'):
        max_s = (net[gen].max_p_mw**2 + net[gen].max_q_mvar**2)**0.5
        net[gen]['max_s_mva'] = pd.Series(max_s, index=net[gen].index)

    return net


def settings_opf(net, cos_phi=0.95, max_dU=0.05):
    """ Make some general setting for reactive OPF calculation. """

    for type_ in ('gen', 'sgen'):
        # Max and min reactive power feed-in of gens and sgens
        max_q = np.array([p * (np.arctan(np.arccos(cos_phi))) for p in net[type_].p_mw])
        min_q = np.array([-p * (np.arctan(np.arccos(cos_phi)))
                          for p in net[type_].p_mw])
        net[type_]['max_q_mvar'] = pd.Series(max_q, index=net[type_].index)
        net[type_]['min_q_mvar'] = pd.Series(min_q, index=net[type_].index)
        if 'q_mvar' not in net[type_]:
            net[type_]['q_mvar'] = pd.Series(0, index=net[type_].index)

        # Max and min active power feed-in (workaround! easier way?)
        net[type_]['max_p_mw'] = pd.Series(
            [p * 1.01 for p in net[type_].p_mw], index=net[type_].index)
        net[type_]['min_p_mw'] = pd.Series(
            [p * 0.99 for p in net[type_].p_mw], index=net[type_].index)

        # Make controllable
        net[type_]['controllable'] = pd.Series(
            [True for _ in net[type_].index], index=net[type_].index)

    # Max and min active/reactive power feed-in of external grid
    net.ext_grid['max_p_mw'] = pd.Series(
        [1000000 for _ in net.ext_grid.index], index=net.ext_grid.index)
    net.ext_grid['min_p_mw'] = pd.Series(
        [-1000000 for _ in net.ext_grid.index], index=net.ext_grid.index)
    net.ext_grid['max_q_mvar'] = pd.Series(
        [1000000 for _ in net.ext_grid.index], index=net.ext_grid.index)
    net.ext_grid['min_q_mvar'] = pd.Series(
        [-1000000 for _ in net.ext_grid.index], index=net.ext_grid.index)

    # Constraints: Voltage band
    net.bus['min_vm_pu'] = pd.Series(
        [1 - max_dU for _ in net.bus.index], index=net.bus.index)
    net.bus['max_vm_pu'] = pd.Series(
        [1 + max_dU for _ in net.bus.index], index=net.bus.index)

    # Constraints: Line loadings
    max_loading = 100
    net.line['max_loading_percent'] = pd.Series(
        [max_loading for _ in net.line.index], index=net.line.index)

    # Constraints: Trafo loadings
    max_loading = 100
    net.trafo['max_loading_percent'] = pd.Series(
        [max_loading for _ in net.trafo.index], index=net.trafo.index)

    return net


if __name__ == '__main__':
    main()
