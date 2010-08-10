#!/usr/bin/env python
# encoding: utf-8
"""
poolit.py

Created by Kurtiss Hare on 2010-08-10.
Copyright (c) 2010 Medium Entertainment, Inc. All rights reserved.
"""

import tornado.ioloop
import functools


def poolit(pool, callback, func, args, kwargs):
    def wrapper(result):
        ioloop = tornado.ioloop.IOLoop.instance()
        ioloop.add_callback(functools.partial(callback, result))
    pool.apply_async(func, args, kwargs, wrapper)