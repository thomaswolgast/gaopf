# main.py
"""
Test the genetic algorithm for pandapower

"""

import numpy as np
import pandas as pd
import pandapower as pp
import pandapower.networks as pn

from . import pp_ga

"""
TODO:
- Zwei arrays für int und float, um die operatoren für beides zu optimieren (oder ints durch floats ersetzen und immer runden?)
und zu differenzieren?
- Zeitmessung integrieren, um Verbesserungspotenzial zu finden
- Unterschiede zu pandapower-OPF herausarbeiten -> weiterentwickeln sinnvoll?
"""

"""
Vorteile gegenüber PP-OPF:
- P und Q getrennt optimierbar
- beliebige Zielfunktionen
- Trafos mit optimieren
- Switches mit optimieren
- Bessere Chancen auf Konvergenz (mit potenzieller constraint verletzung)
- Constraints können (bzw. müssen) als soft-constraints berücksichtigt werden
-> macht optimale Einhaltung der RB als Zielfunktion möglich (min sum(U^2-1))

Nachteile:
- Langsamer
- Mehr Parameter einzustellen (Populationsgröße, Iterationszahl etc.)
-> mehr Programmieraufwand bei Anwendung
"""


def main():
    scenario2()
    scenario2ref()


def scenario1():
    """ GA-OPF on the grid from the simple pandapower-OPF tutorial. """
    # https://github.com/e2nIEE/pandapower/blob/master/tutorials/opf_basic.ipynb
    variables = (('gen', 'p_mw', 0), ('gen', 'p_mw', 1))
    net = create_net1()

    ga = pp_ga.GeneticAlgorithm(pop_size=50, variables=variables,
                                net=net, mutation_rate=0.001,
                                obj_fct=obj_fct1,
                                constraints='all')
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


def scenario2():
    """ Test OPF with larger network (cigre mv with pv and wind). """
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

    ga = pp_ga.GeneticAlgorithm(pop_size=100, variables=variables,
                                net=net, mutation_rate=0.001,
                                obj_fct='min_p_loss',
                                constraints='all',
                                plot=True,
                                save=True,
                                termination='cmp_last')

    net_opt, best_costs = ga.run(iter_max=30)
    print(f'Costs of ga-OPF: {best_costs}')

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

    from .obj_functs import min_p_loss
    costs = min_p_loss(net)  # Pandapower costs not working: loads are not considered!?
    print(f'Costs of pandapower-OPF: {costs}')

    return net, costs


def scenario3():
    """ Large multi voltage level power grid that contains all possible 
    elements. If this work, everything should work!
    https://pandapower.readthedocs.io/en/v2.1.0/networks/example.html """
    net = create_net2()

    variables = [('sgen', 'q_mvar', idx) for idx in net.sgen.index]
    variables += [('gen', 'q_mvar', idx) for idx in net.gen.index]
    variables += [('shunt', 'step', 0)]
    variables += [('trafo', 'tap_pos', 1)]
    variables += [('trafo3w', 'tap_pos', 0)]


    ga = pp_ga.GeneticAlgorithm(pop_size=250, variables=variables,
                                net=net, mutation_rate=0.001,
                                obj_fct='min_p_loss',
                                constraints='all',
                                plot=True,
                                termination='cmp_last')

    net_opt, best_costs = ga.run(iter_max=40)
    print(f'Costs of ga-OPF: {best_costs}')

    return net_opt, best_costs

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
