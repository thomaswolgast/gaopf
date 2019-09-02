# penalty_fcts.py
"""
A collection of penalty functions to punish selected constraint violations.

"""


def penalty_fct(net, constraints):
    """ Punish a set of constraints. Possible are: voltage band violation
    (String: 'voltage_band'), max line loading ('line_load'), max trafo
    loading ('trafo_load' and/or 'trafo3w_load'). """
    # TODO: Add option to make penelty adjustable! -> ((constraint1, penalty1) ...) ?

    if isinstance(constraints, str):
        if constraints == 'none':
            return 0, True
        elif constraints == 'all':
            constraints = ('voltage_band', 'line_load',
                           'trafo_load', 'trafo3w_load')

    penalty = 0
    for constraint in constraints:
        penalty += eval(constraint)(net)

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
    # TODO: divide upper and lower boundary into two functions?
    # TODO: Make costs adjustable!
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
