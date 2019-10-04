# multicore.py

from .util import update_net


def multi_fit_fct(net, variables: tuple, inds: tuple, 
				  penalty_fct, constraints: tuple, obj_fct):
	""" Calculate fitness function for sub-population. """

	# Load json-saved pandapower net -> additonal information gets lost
	# net = pp.from_json(net_name)

	for ind in inds:
		net, ind.failure = update_net(net, ind, variables)

		# Check for failed power flow calculation
		if ind.failure is True:
			continue

		# Check if constraints are violated and calculate penalty
		ind.penalty, ind.valid = penalty_fct(net, constraints)

		# Assign fitness value to each individual
		ind.fitness = obj_fct(net=net) + ind.penalty

	return inds