# util.py
""" Some util classes for the pandapower ga-OPF.

"""

import random


class Individual:
    def __init__(self, vars_in: tuple, net: object, set_vars: tuple=None):
        if set_vars is not None:
            self.vars = set_vars
            assert isinstance(set_vars[0], LmtNumber)
        else:
            self.random_init(vars_in, net)
        self.reset()

    def random_init(self, vars_in, net):
        self.vars = []
        for unit_type, actuator, idx in vars_in:
            if actuator == 'p_mw' or actuator == 'q_mvar' or actuator == 'p_kw' or actuator == 'q_kvar':
                var = LmtNumber(
                    nmbr_type='float',
                    min_boundary=net[unit_type][f'min_{actuator}'][idx],
                    max_boundary=net[unit_type][f'max_{actuator}'][idx])
            elif actuator == 'tap_pos':
                var = LmtNumber(
                    nmbr_type='int',
                    min_boundary=net[unit_type]['tap_min'][idx],
                    max_boundary=net[unit_type]['tap_max'][idx])

            self.vars.append(var)

    def reset(self):
        self.fitness = None
        # Did this individual lead to failed power flow calculation?
        self.failure = None
        # Valid solution? All constraints satisfied?
        self.valid = None

    def __repr__(self):
        return str(self.vars)

    def __iter__(self):
        yield from self.vars

    def __len__(self):
        return len(self.vars)

    def __setitem__(self, idx, value):
        self.vars[idx] = value

    def __getitem__(self, idx):
        return self.vars[idx]


class LmtNumber:
    """ A number that is restricted to a given range of values. """

    def __init__(self, nmbr_type: str, min_boundary, max_boundary,
                 set_value=None):
        assert nmbr_type in ('float', 'int')
        self.type = nmbr_type

        assert max_boundary > min_boundary
        self.min_boundary = min_boundary
        self.max_boundary = max_boundary
        self.range = self.max_boundary - self.min_boundary

        if set_value is not None:
            self.value = set_value
        else:
            self.random_init()

    def __repr__(self):
        return str(self.value)

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, set_value):
        # Make sure integer remains integer (round randomly)
        if self.type == 'int':
            self._value = round(set_value + random.random() / 2)
        else:
            self._value = set_value

        # Make sure 'value' stays always within boundaries.
        self._value = max(
            min(self.max_boundary, self._value), self.min_boundary)

    # TODO: Make subclassed instead of type-checking?!
    def random_init(self):
        """ Init value with a random number between the boundaries """
        if self.type == 'float':
            self.value = random.random() * self.range + self.min_boundary
        elif self.type == 'int':
            self.value = random.randint(self.min_boundary, self.max_boundary)

    def increase(self):
        """ Increase value slightly. """
        if self.type == 'float':
            # Increase by random value between 0% and 100%
            self.value += random.random() * self.range
        elif self.type == 'int':
            self.value += 1

    def decrease(self):
        """ Increase value slightly. """
        if self.type == 'float':
            # Decrease by random value between 0% and 100%
            self.value -= random.random() * self.range
        elif self.type == 'int':
            self.value -= 1
