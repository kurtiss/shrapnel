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


def uuid():
	return webencode(uuid_module.uuid4().bytes)
	
def hash(value):
	return webencode(hashlib.sha1(value).digest())
	
def webencode(value):
	return base64.b64encode(value, ('-', '_')).rstrip('=')