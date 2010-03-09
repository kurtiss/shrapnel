#!/usr/bin/env python
# encoding: utf-8
"""
web.py

Created by Kurtiss Hare on 2010-03-09.
Copyright (c) 2010 Medium Entertainment, Inc. All rights reserved.
"""

import urllib

def url(base, **query):
	return "{0}?{1}".format(base, urllib.urlencode(query))