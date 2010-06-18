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
        return self.retainer.result[0]


class Retainer(object):
    def __init__(self, size):
        self.size = size
        self.counter = 0
        self._result = []

    def encounter(self, item):
        result_len = len(self._result)

        if result_len > 0:
            if random.random() <= min(result_len, self.size) / float(self.counter):
                if result_len >= self.size:
                    replace_index = random.randint(0, result_len - 1)
                    self._result[replace_index] = item
                else:
                    insert_index = random.randint(0, result_len)

                    if insert_index != result_len:
                        self._result.append(self._result[insert_index])
                        self._result[insert_index] = item
                    else:
                        self._result.append(item)
        else:
            self._result.append(item)

        self.counter += 1

    @property
    def result(self):
        return self._result[:self.size]