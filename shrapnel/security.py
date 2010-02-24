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
	return base64.b64encode(uuid_module.uuid4().bytes, ('-', '_')).rstrip('=')
	
def hash(value):
	return base64.b64encode(hashlib.sha1(value).digest(), ('-', '_')).rstrip('=')