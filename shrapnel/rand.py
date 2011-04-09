#!/usr/bin/env python
# encoding: utf-8
"""
rand.py

Created by Kurtiss Hare on 2010-06-04.
Copyright (c) 2010 Medium Entertainment, Inc. All rights reserved.
"""

import random


class Picker(object):
    def __init__(self):
        self.retainer = Retainer(1)

    def encounter(self, value):
        self.retainer.encounter(value)

    @property
    def value(self):
        try:
            return self.retainer.result[0]
        except IndexError:
            raise ValueError("Picker did not enounter any values.")

class Retainer(object):
    def __init__(self, size):
        self.size = size
        self.counter = 0
        self._result = []

    def encounter(self, item):
        result_len = len(self._result)

        if result_len == self.size:
            self.counter += 1
            if random.random() <= float(self.size) / (self.size + self.counter):
                replace_index = random.randint(0, result_len - 1)
                self._result[replace_index] = item
        else:
            self._result.append(item)

    @property
    def result(self):
        return self._result[:self.size]
