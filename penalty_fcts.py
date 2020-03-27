# penalty_fcts.py
"""
A collection of penalty functions to punish selected constraint violations.

"""


def penalty_fct(net, constraints: list):
    """ Punish a set of constraints. Possible are: voltage band violation
    (String: 'voltage_band'), max line loading ('line_load'), max trafo
    loading ('trafo_load' and/or 'trafo3w_load'), max apparent power of
    generators('apparent_power'). """
    # TODO: Add option to make penelty adjustable! -> ((constraint1, penalty1) ...) ?

    if isinstance(constraints, str):
        if constraints == 'none':
            return 0, True
        elif constraints == 'all':
            # Attention: does not include 'apparent_power', because it is not
            # included in original pandapower constraints
            constraints = ('voltage_band', 'line_load',
                           'trafo_load', 'trafo3w_load')

    penalty = sum([eval(constraint)(net) for constraint in constraints])

    # Define under which circumstances a solution is seen as valid
    if penalty > 0:
        valid = False
    else:
        valid = True

    return penalty, valid


def voltage_band(net, costs=1000000):
    """ Punish voltage violations with 1 Meuro per 1pu violation.
    See https://pandapower.readthedocs.io/en/v2.1.0/opf/formulation.html for
    default voltage band values. """
    # TODO: divide upper and lower boundary into two functions?

    penalty = 0
    for idx in net.bus.index:

        u_max = net.bus.max_vm_pu[idx]
        u_min = net.bus.min_vm_pu[idx]

        if net.res_bus.vm_pu[idx] > u_max:
            penalty += (net.res_bus.vm_pu[idx] - u_max) * costs
        elif net.res_bus.vm_pu[idx] < u_min:
            penalty += (u_min - net.res_bus.vm_pu[idx]) * costs

    return penalty


def line_load(net, costs=10000):
    """ Punish line load violation with 10 keuro per 1% violation. """
    return loading(net, costs=costs, unit_type='line')


def trafo_load(net, costs=10000):
    """ Punish trafo load violation with 10 keuro per 1% violation. """
    return loading(net, costs=costs, unit_type='trafo')


def trafo3w_load(net, costs=10000):
    """ Punish trafo load violation with 10 keuro per 1% violation. """
    return loading(net, costs=costs, unit_type='trafo3w')


def loading(net, costs, unit_type: str):
    """ Punish load violation of trafo or line with 'costs' per 1%
    violation. """
    penalty = 0
    for idx in net[unit_type].index:
        max_load = net[unit_type].max_loading_percent[idx]
        if net[f'res_{unit_type}'].loading_percent[idx] > max_load:
            penalty += (net[f'res_{unit_type}'].loading_percent[idx] - max_load) * costs

    return penalty


def apparent_power(net, costs=10000):
    """ Punish violation of max apparent power of generators.

    Add constraint 'max_s_mva' first! Use only if p and q are optimized
    together! """
    penalty = 0
    for gen_type in ('gen', 'sgen'):
        s_gen = (net[gen_type].p_mw**2 + net[gen_type].q_mvar**2)**0.5
        for s in s_sgen:
            if s > net[gen_type].max_s_mva[idx]:
                penalty += (s - net[gen_type].max_s_mva[idx]) * costs

    return penalty
