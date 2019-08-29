# obj_functs.py
"""
A collection of various fitness functions for the pandapower ga-OPF

"""


def min_p_loss(net):
    """ Minimize active power losses for a given network. """
    gen = 0
    load = 0
    gen += sum(net.gen.p_mw)
    gen += sum(net.sgen.p_mw)
    # etc.

    load += sum(net.load.p_mw)
    # etc.

    p_loss = gen - load

    return p_loss
