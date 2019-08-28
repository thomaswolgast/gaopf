# pp_ga.py
"""
An optimal power flow algorithm based on a genetic algorithm for pandapower
networks.

Advantages compared to pre-implemented pandapower OPF:
TODO!

"""

import pandapower as pp


class GeneticAlgorithm:
    def __init__(self, pop_size: int, n_iter: int, net=net,
                 obj_fct='obj_P_loss'):
        self.pop_size = pop_size
        self.n_iter = n_iter
        self.net = net

        # Choose fitness/objective function (attention: all objective
        # function must be written as minimization)
        if isinstance(obj_fct, str):
            # Select from pre-defined fitness functions (e.g. reduce loss)
            self.fit_fct = self.__dict__[obj_fct]
        else:
            # Self-made fitness function (objective function)
            self.fit_fct = obj_fct

        # Choose selection method
        self.selection = self.tournament

    def run(self):
        """ Run genetic algorithm until termination. """
        self.init_pop()

        for m in range(self.n_iter):
            self.fit_fct()
            self.selection()
            self.crossover()
            self.mutation()

    def init_pop(self):
        """ Random initilization of the population. """
        self.pop = [self.init_ind(self.net) for _ in range(self.pop_size)]

    def init_ind(self, net):
        ind = []
        for var in self.vars


    def obj_P_loss(self):
        """ Objective function: minimize total active power losses in whole
        network. """
        for ind in self.pop:
            self.update_net(self.net, ind)
            pp.runpp(self.net)

            # TODO: any easier way than summing up?
            losses = 0
            losses += sum(self.net)

            ind.fitness = losses

    def tournament(self, group_size: int=4):
        """ Divive population in groups of size n and select the best
        individuum of each group. """

        self.parents = []
        for idx in range(0, self.pop_size, group_size):
            self.parents
