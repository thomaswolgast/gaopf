# main.py
"""
Test the genetic algorithm for pandapower

"""

import numpy as np
import pandas as pd
import pandapower as pp
import pandapower.networks as pn

import pp_ga

"""
TODO:
- Zwei arrays für int und float, um die operatoren für beides zu optimieren
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
"""


def main():
    net = scenario2()
    net_ref = scenario2ref()
    return net, net_ref


def scenario1():
    """ Test OPF compared to pandapower OPF-tutorial. """
    variables = (('gen', 'p_mw', 0), ('gen', 'p_mw', 1))
    net = create_net1()

    ga = pp_ga.GeneticAlgorithm(pop_size=50, variables=variables,
                                net=net, mutation_rate=0.001,
                                obj_fct=obj_fct1,
                                constraints='all')
    ga.run(iter_max=30)

    # Compare with pp-OPF
    net = create_net1()
    costeg = pp.create_poly_cost(net, 0, 'ext_grid', cp1_eur_per_mw=10)
    costgen1 = pp.create_poly_cost(net, 0, 'gen', cp1_eur_per_mw=10)
    costgen2 = pp.create_poly_cost(net, 1, 'gen', cp1_eur_per_mw=10)
    pp.runopp(net)
    print(net.res_cost)


def scenario2():
    """ Test OPF with larger network (cigre mv with pv and wind). """
    net = create_net2()

    # Degrees of freedom for optimization
    # TODO: how to make easy? (if index == xxx: use all indexes)
    variables = (('sgen', 'q_mvar', 0),
                 ('sgen', 'q_mvar', 1),
                 ('sgen', 'q_mvar', 2),
                 ('sgen', 'q_mvar', 3),
                 ('sgen', 'q_mvar', 4),
                 ('sgen', 'q_mvar', 5),
                 ('sgen', 'q_mvar', 6),
                 ('sgen', 'q_mvar', 7),
                 ('sgen', 'q_mvar', 8),)
                 # ('trafo', 'tap_pos', 0),
                 # ('trafo', 'tap_pos', 1))
    # For trafo: ('trafo, 'tap_pos', 0)

    ga = pp_ga.GeneticAlgorithm(pop_size=150, variables=variables,
                                net=net, mutation_rate=0.001,
                                obj_fct='min_p_loss',
                                constraints='all')

    net_opt, costs = ga.run(iter_max=15)
    print(f'Costs of ga-OPF: {costs}')

    return net_opt


def scenario2ref():
    # Comparison with pp-opf:
    net = create_net2()
    pp.create_poly_cost(net, 0, 'ext_grid', cp1_eur_per_mw=1)
    for idx in net.sgen.index:
        pp.create_poly_cost(net, idx, 'sgen', cp1_eur_per_mw=1)
    for idx in net.load.index:
        pp.create_poly_cost(net, idx, 'load', cp1_eur_per_mw=-1)
    pp.runopp(net, verbose=False)
    from obj_functs import min_p_loss
    # Pandapower costs not working: loads are not considered!
    print(f'Costs of pandapower-OPF: {min_p_loss(net)}')
    return net


def obj_fct1(net):
    """ Re-create the pandapower tutorial from:
    https://github.com/e2nIEE/pandapower/blob/master/tutorials/opf_basic.ipynb
    """
    costs = 0

    costs += sum(net.res_ext_grid['p_mw']) * 10
    costs += sum(net.res_gen['p_mw']) * 10

    return costs


def create_net1():
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
    eg = pp.create_ext_grid(net, bus1, min_p_mw=-1000, max_p_mw=1000)
    g0 = pp.create_gen(net, bus3, p_mw=80, min_p_mw=0, max_p_mw=80,  vm_pu=1.01, controllable=True)
    g1 = pp.create_gen(net, bus4, p_mw=100, min_p_mw=0, max_p_mw=100, vm_pu=1.01, controllable=True)

    return net


def create_net2():
    """ Net and constraints for optimale reactive power flow. """
    net = pn.create_cigre_network_mv(with_der='pv_wind')

    # Max and min reactive power feed-in
    cos_phi = 0.95
    max_q = np.array([p * (np.arctan(np.arccos(cos_phi))) for p in net.sgen.p_mw])
    min_q = np.array([-p * (np.arctan(np.arccos(cos_phi)))
                      for p in net.sgen.p_mw])
    net.sgen['max_q_mvar'] = pd.Series(max_q, index=net.sgen.index)
    net.sgen['min_q_mvar'] = pd.Series(min_q, index=net.sgen.index)

    # Max and min active power feed-in (workaround! easier way?)
    net.sgen['max_p_mw'] = pd.Series(
        [p*1.01 for p in net.sgen.p_mw], index=net.sgen.index)
    net.sgen['min_p_mw'] = pd.Series(
        [p*0.99 for p in net.sgen.p_mw], index=net.sgen.index)

    # Make sgens controllable
    net.sgen['controllable'] = pd.Series(
        [True for _ in net.sgen.index], index=net.sgen.index)

    # Max and min active/reactive power feed-in of external grid
    net.ext_grid['max_p_mw'] = pd.Series(
        [1000000 for _ in net.ext_grid.index], index=net.ext_grid.index)
    net.ext_grid['min_p_mw'] = pd.Series(
        [-1000000 for _ in net.ext_grid.index], index=net.ext_grid.index)
    net.ext_grid['max_q_mvar'] = pd.Series(
        [1000000 for _ in net.ext_grid.index], index=net.ext_grid.index)
    net.ext_grid['min_q_mvar'] = pd.Series(
        [-1000000 for _ in net.ext_grid.index], index=net.ext_grid.index)

    # Voltage band
    max_dU = 0.05
    net.bus['min_vm_pu'] = pd.Series(
        [1-max_dU for _ in net.bus.index], index=net.bus.index)
    net.bus['max_vm_pu'] = pd.Series(
        [1+max_dU for _ in net.bus.index], index=net.bus.index)

    # Line loadings
    max_loading = 100
    net.line['max_loading_percent'] = pd.Series(
        [max_loading for _ in net.line.index], index=net.line.index)

    # Trafo loadings
    max_loading = 100
    net.trafo['max_loading_percent'] = pd.Series(
        [max_loading for _ in net.trafo.index], index=net.trafo.index)

    return net


if __name__ == '__main__':
    main()
