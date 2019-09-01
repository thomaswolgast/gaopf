# obj_functs.py
"""
A collection of various fitness functions for the pandapower ga-OPF

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
