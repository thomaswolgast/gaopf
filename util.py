# util.py
""" Some util classes for the pandapower ga-OPF.

"""

import random

import numpy as np


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
            if unit_type == 'gen' and actuator == 'vm_pu':
                # AVR regulation
                var = LmtFloat(
                    min_boundary=net.bus.min_vm_pu[idx],
                    max_boundary=net.bus.max_vm_pu[idx],
                    distribution='normal')  
            elif unit_type == 'gen' or unit_type == 'sgen':
                # Active or reactive power regulation
                var = LmtFloat(
                    min_boundary=net[unit_type][f'min_{actuator}'][idx],
                    max_boundary=net[unit_type][f'max_{actuator}'][idx])                 
            elif actuator == 'tap_pos':
                # Tap-changing transformer regulation
                var = LmtInt(
                    min_boundary=net[unit_type]['tap_min'][idx],
                    max_boundary=net[unit_type]['tap_max'][idx],
                    distribution='normal')
            elif actuator == 'step':
                # Shunt regulation
                var = LmtInt(
                    min_boundary=0,
                    max_boundary=net[unit_type]['max_step'][idx])
            else: 
                raise ValueError(f"""
                    The combination {unit_type}, {actuator}, {idx} is not possible
                    (Maybe not implemented yet)""")

            self.vars.append(var)

    def reset(self):
        self.fitness = None
        # Did this individual lead to failed power flow calculation?
        self.failure = False
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
    def __init__(self, min_boundary, max_boundary,
                 set_value=None, distribution='equally'):
        assert max_boundary > min_boundary
        self.min_boundary = min_boundary
        self.max_boundary = max_boundary
        self.range = self.max_boundary - self.min_boundary
        self.distribution = distribution

        if set_value is not None:
            self.value = set_value
        else:
            self.random_init()

    def __repr__(self):
        return str(self.value)


class LmtInt(LmtNumber):
    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, set_value):
        # Make sure integer remains integer (round randomly)
        self._value = round(set_value + random.random() / 2)

        # Make sure 'value' stays always within boundaries.
        self._value = max(
            min(self.max_boundary, self._value), self.min_boundary)

    def random_init(self):
        if self.distribution == 'equally':
            self.value = random.randint(self.min_boundary, self.max_boundary)
        elif self.distribution == 'normal':
            self.value = round(np.random.normal(0, 0.5) * self.range 
                               + self.min_boundary)
    def increase(self):
        self.value += 1

    def decrease(self):
        self.value -= 1


class LmtFloat(LmtNumber):
    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, set_value):
        # Make sure 'value' stays always within boundaries.
        self._value = max(
            min(self.max_boundary, set_value), self.min_boundary)

    def random_init(self):
        if self.distribution == 'equally':
            self.value = random.random() * self.range + self.min_boundary
        elif self.distribution == 'normal':
            self.value = np.random.normal(0, 0.5) * self.range + self.min_boundary

    def increase(self):
        self.value += random.random() * self.range / 10

    def decrease(self):
        self.value -= random.random() * self.range / 10
