#!/usr/bin/env python
# encoding: utf-8
"""
security.py

Created by Kurtiss Hare on 2010-01-28.
Copyright (c) 2010 Medium Entertainment, Inc. All rights reserved.
"""

import base64
import uuid as uuid_module
import hashlib
import random


def uuid():
	return webencode(uuid_module.uuid4().bytes)
	
def hash(value):
	return webencode(hashlib.sha1(value).digest())
	
def webencode(value):
	return base64.b64encode(value, ('-', '_')).rstrip('=')
	
def tiny_guid(value, namespace = 'default', min_chars = 4):
    characters = list('0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ')
    factors = [
        839299365868340224,
        13537086546263552,
        218340105584896,
        3521614606208,
        56800235584,
        916132832,
        14776336,
        238328,
        3844,
        62,
        1
    ]
    offset_test = len(factors) - min_chars - 1

    output = []

    for (offset, factor) in enumerate(factors):
        if value >= factor:
            index = value / factor
            output.append(index)
            value -= index * factor
        elif len(output) or offset > offset_test:
            output.append(0)

    for i in xrange(len(output) - 1, -1, -1):
        column_characters = list(characters)
        random.seed("pXe2eYsKTQyc6NKuKwJonQ:{0}:{1}".format(namespace, ''.join(output[i+1:])))
        random.shuffle(column_characters)
        output[i] = column_characters[output[i]]

    return ''.join(output)    