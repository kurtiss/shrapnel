#!/usr/bin/env python
# encoding: utf-8
"""
web.py

Created by Kurtiss Hare on 2010-03-09.
Copyright (c) 2010 Medium Entertainment, Inc. All rights reserved.
"""

import collections
import functools
import itertools
import threading
import tornado.ioloop
import urllib


def url(base, **query):
	return "{0}?{1}".format(base, urllib.urlencode(query))


def flagger(target, callback):
    def wrapper(*args, **kwargs):
        try:
            result = target(*args, **kwargs)
        except Exception as e:
            callback(None, e)
        else:
            callback(result)

    return wrapper


class Plan(object):
    def __init__(self, handler):
        self._handler = handler
        self._waiter_keys = dict()
        self._waiter_results = dict()
        self._lock = threading.Lock()
        self._callback_queue = collections.deque()
        self._next_callback = self._handler.async_callback(self._next_in_callback_queue)
        self._ioloop = tornado.ioloop.IOLoop.instance()

    def wait(self, *keys):
        def decorator(undecorated):
            self._add_waiter(keys, undecorated)
            def replacement(*a, **k):
                raise RuntimeError("{0.__name__} should not be called directly.".format(undecorated))
            return replacement
        return decorator

    def _add_waiter(self, keys, waiter):
        call_now = False

        with self._lock:
            wait_keys = (k for k in keys if k not in self._waiter_results)
            wait_values = itertools.repeat(True)
            conditions = dict(itertools.izip(wait_keys, wait_values))

            if conditions:
                for key in conditions.keys():
                    if not self._waiter_keys.has_key(key):
                        self._waiter_keys[key] = []
                    self._waiter_keys[key].append((conditions, keys, waiter))
            else:
                call_now = True

        if call_now:
            waiter(WaiterResult(keys, self._waiter_results))

    def flag(self, key):
        @self._handler.async_callback
        def callback(result = None, exception = None):
            queued = False

            with self._lock:
                self._waiter_results[key] = (result, exception)
                before_waiters = self._waiter_keys.pop(key, tuple())
                after_waiters = []

                for waiter_stuff in before_waiters:
                    conditions, keys, waiter = waiter_stuff
                    conditions.pop(key)

                    if not conditions:
                        self._callback_queue.append(functools.partial(waiter, WaiterResult(keys, self._waiter_results)))
                        queued = True
                    else:
                        after_waiters.append(waiter_stuff)

                if after_waiters:
                    self._waiter_keys[key] = after_waiters

            if queued:
                self._ioloop.add_callback(self._next_callback)

        return callback

    def _next_in_callback_queue(self):
        try:
            callback = self._callback_queue.popleft()
        except IndexError:
            pass
        else:
            callback()
            self._ioloop.add_callback(self._next_callback)


class WaiterResult(object):
    def __init__(self, keys, results):
        self.keys = keys
        self.results = results

    def get(self, index = 0):
        (result, exception) = self.results[self.keys[index]]
        if exception:
            raise exception
        return result

