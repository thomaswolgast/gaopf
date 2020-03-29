# obj_functs.py
"""
A collection of various objective functions for the pandapower ga-OPF

"""


def min_p_loss(net):
    """ Minimize active power losses for a given network. """
    gen = (sum(net.res_ext_grid.p_mw)
           + sum(net.res_sgen.p_mw)
           + sum(net.res_gen.p_mw))
    load = sum(net.storage.p_mw) + sum(net.load.p_mw)
    p_loss = gen - load

    return p_loss


def max_p_feedin(net):
    """ Maximize active power feed-in of all generators. Negative sign
    necessary, because all objective functions must be min problems. """
    return -(sum(net.res_sgen.p_mw) + sum(net.res_gen.p_mw))


def min_v2_deviations(net):
    """ Minimize quadratic voltage deviations from reference voltage
    (1 pu). """
    return sum((net.res_bus.vm_pu-1)**2)


def min_pp_costs(net):
    """ Minimize total costs as implemented in pandapower network.
    Useful if cost function is already implemented or for comparison with
    pandapower-OPF. Attention: Not equivalent to 'net.res_cost' after
    pp-OPF, because internal cost calculation of pandapower is strange. """

    # TODO: piece-wise costs not implemented yet!
    costs = 0
    for idx in net.poly_cost.index:
        element = net.poly_cost.element[idx]
        et = net.poly_cost.et[idx]

        costs += net.poly_cost.cp0_eur[idx] + net.poly_cost.cq0_eur[idx]
        costs += (net[f'res_{et}']['p_mw'][element]
                  * net.poly_cost['cp1_eur_per_mw'][idx])
        costs += (net[f'res_{et}']['p_mw'][element]**2
                  * net.poly_cost['cp2_eur_per_mw2'][idx])
        costs += (net[f'res_{et}']['q_mvar'][element]
                  * net.poly_cost['cq1_eur_per_mvar'][idx])
        costs += (net[f'res_{et}']['q_mvar'][element]**2
                  * net.poly_cost['cq2_eur_per_mvar2'][idx])

    return costs
