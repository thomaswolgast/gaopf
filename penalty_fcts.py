# penalty_fcts.py
"""
A collection of penalty functions to punish selected constraint violations.

"""


def all_constraints(net):
    """ Punish the following constraints: voltage band violation, line load
    violation, trafo load violation, three winding trafo violation. The
    punishment is 1 Meuro per 1pu violation. """
    penalty = (voltage_band(net)
               + line_load(net)
               + trafo_load(net)
               + trafo3w_load(net))

    # Define under which circumstances a solution is seen as valid
    if penalty > 0:
        valid = False
    else:
        valid = True

    return penalty, valid


def loading_only(net):
    """ Punish the following constraints: line load violation, trafo load
    violation, three winding trafo violation. The punishment is 1 Meuro per
    1pu violation. """
    penalty = (line_load(net)
               + trafo_load(net)
               + trafo3w_load(net))

    # Define under which circumstances a solution is seen as valid
    if penalty > 0:
        valid = False
    else:
        valid = True

    return penalty, valid


def voltage_band(net):
    """ Punish voltage violations with 1 Meuro per 1pu violation.
    See https://pandapower.readthedocs.io/en/v2.1.0/opf/formulation.html for
    default voltage band values. """

    # TODO: Make costs adjustable
    costs = 1000000

    penalty = 0
    for idx in net.bus.index:
        try:
            u_max = net.bus.max_vm_pu[idx]
        except AttributeError:
            # Set u_max to default value
            u_max = 1.1
            print(f'Set v_max to default ({u_max}) for bus {idx}')

        try:
            u_min = net.bus.min_vm_pu[idx]
        except AttributeError:
            # Set u_min to default value
            u_min = 0.9
            print(f'Set v_min to default ({u_min}) for bus {idx}')

        if net.res_bus.vm_pu[idx] > u_max:
            penalty += (net.res_bus.vm_pu[idx] - u_max) * costs
        elif net.res_bus.vm_pu[idx] < u_min:
            penalty += (u_min - net.res_bus.vm_pu[idx]) * costs

    return penalty


def line_load(net):
    """ Punish line load violation with 10 keuro per 1% violation. """
    return loading(net, costs=10000, unit_type='line')


def trafo_load(net):
    """ Punish trafo load violation with 10 keuro per 1% violation. """
    return loading(net, costs=10000, unit_type='trafo')


def trafo3w_load(net):
    """ Punish trafo load violation with 10 keuro per 1% violation. """
    return loading(net, costs=10000, unit_type='trafo3w')


def loading(net, costs, unit_type: str='trafo'):
    """ Punish load violation of trafo or line with 'costs' per 1%
    violation. """
    penalty = 0
    for idx in net[unit_type].index:
        try:
            max_load = net[unit_type].max_loading_percent[idx]
        except AttributeError:
            # Set u_max to default value
            max_load = 100

        if net[f'res_{unit_type}'].loading_percent[idx] > max_load:
            (net[f'res_{unit_type}'].loading_percent[idx] - max_load) * costs

    return penalty
