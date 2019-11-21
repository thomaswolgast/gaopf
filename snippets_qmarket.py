# snippets_qmarket.py
"""
Create price curve of a single network for varying reactive power prices at
the coupling point.
"""

import matplotlib.pyplot as plt

import pandas as pd
import pandapower as pp
import pandapower.networks as pn
import numpy as np

p_price = 27.83
q_price2_sgen = 6  # TW: grobe Abschätzung erstmal


def main():
    net = create_lv_grid(cos_phi=0.95, type_='rural_1')

    q_prices = [n/10 for n in range(-15, 20, 5)]
    q_exchange = []
    for q_price in q_prices:
        # Vary reactive power prices at coupling point
        pp.create_poly_cost(net, 0, 'ext_grid',
                            cp1_eur_per_mw=p_price,
                            cq1_eur_per_mvar=q_price)  # q-price!
        pp.runopp(net)
        q_exchange.append(net.res_ext_grid.q_mvar[0])

        # Delete created poly cost (otherwise we have double costs)
        net.poly_cost = net.poly_cost.drop(net.poly_cost.index[-1])

    plt.plot(q_prices, q_exchange)
    plt.show()


def create_lv_grid(cos_phi=0.95, type_='rural_1'):
    """ Use a predefined low voltage grid from pandapower as subordinate
    network. """
    lv_net = pn.create_synthetic_voltage_control_lv_network(type_)

    add_constraints(lv_net, cos_phi)

    # Implement objective function for OPF
    obj_fct(net=lv_net)

    return lv_net


def add_constraints(net, cos_phi=0.95):
    """ Add constraints to make OPF possible. """

    # Max and min reactive power feed-in of generators (only sgens)
    max_q = np.array([p * (np.arctan(np.arccos(cos_phi)))
                      for p in net.sgen.p_mw])
    min_q = np.array([-p * (np.arctan(np.arccos(cos_phi)))
                      for p in net.sgen.p_mw])
    net.sgen['max_q_mvar'] = pd.Series(max_q, index=net.sgen.index)
    net.sgen['min_q_mvar'] = pd.Series(min_q, index=net.sgen.index)

    # Max and min active power feed-in (workaround! easier way?)
    net.sgen['max_p_mw'] = pd.Series(
        [p*1.01 for p in net.sgen.p_mw], index=net.sgen.index)
    net.sgen['min_p_mw'] = pd.Series(
        [p*0.99 for p in net.sgen.p_mw], index=net.sgen.index)

    # Assert sgens to be controllable
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

    # Constraints: Voltage band
    max_dU = 0.05  # +. 5% voltage band
    net.bus['min_vm_pu'] = pd.Series(
        [1-max_dU for _ in net.bus.index], index=net.bus.index)
    net.bus['max_vm_pu'] = pd.Series(
        [1+max_dU for _ in net.bus.index], index=net.bus.index)

    # Constraints: Line and Trafo loadings
    max_loading = 100
    net.line['max_loading_percent'] = pd.Series(
        [max_loading for _ in net.line.index], index=net.line.index)

    net.trafo['max_loading_percent'] = pd.Series(
        [max_loading for _ in net.trafo.index], index=net.trafo.index)


def obj_fct(net):
    """ Objective function used here: Minimize losses with minimal costs for reactive power usage! """
    for actuator in ['sgen', 'gen']:
        for idx in net[actuator].index:
            # Active power price from:
            # https://www.amprion.net/Strommarkt/Marktplattform/Netzverluste/
            pp.create_poly_cost(net, idx, actuator,
                                cp1_eur_per_mw=p_price,
                                cq2_eur_per_mvar2=q_price2_sgen)
            # Quadratic reactive power prices of sgens
    for actuator in ['load', 'storage']:
        for idx in net[actuator].index:
            pp.create_poly_cost(net, idx, actuator,
                                cp1_eur_per_mw=-p_price,
                                cq2_eur_per_mvar2=q_price2_sgen)


if __name__ == '__main__':
    main()
