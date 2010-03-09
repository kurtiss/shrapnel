#!/usr/bin/env python
# encoding: utf-8
"""
web.py

Created by Kurtiss Hare on 2010-03-09.
Copyright (c) 2010 Medium Entertainment, Inc. All rights reserved.
"""

import urllib

def url(base, **query):
	return "{0}?{1}".format(base, dict(
		(_urlencode(key), _urlencode(value)) for key, value in query
	))

def _urlencode(value):
	if not isinstance(value, basestring):
		value = unicode(value)

	return urllib.urlencode(value)