#!/usr/bin/env python
# encoding: utf-8
"""
db.py

Created by Kurtiss Hare on 2010-02-22.
Copyright (c) 2010 Medium Entertainment, Inc. All rights reserved.
"""

import security


def in_list(values, subs):
	unique = "sub_%s_%%d" % security.uuid()
	lst = []
	i = 0

	for value in values:
		key = unique % i
		i += 1
		
		params[key] = value
		lst.append("%(%s)s" % sub_key)

	return "(%s)" % lst.join(',')