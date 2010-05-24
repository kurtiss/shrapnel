#!/usr/bin/env python
# encoding: utf-8
"""
caching.py

Created by Kurtiss Hare on 2010-02-25.
Copyright (c) 2010 Medium Entertainment, Inc. All rights reserved.
"""

import bisect
import config
import functools
import itertools
import os
import types
import security


def cached():
    def decorator(undecorated):
        @functools.wraps(undecorated)
        def decorated(*args, **kwargs):
            generator = undecorated(*args, **kwargs)

            if not type(generator) == types.GeneratorType:
                raise RuntimeError("{0.__name__} does not conform to the 'cached' protocol.  It must return a generator.".format(undecorated))

            try:
                mc, cache_key = generator.next()
            except TypeError:
                raise RuntimeError("{0.__name__} does not conform to the 'cached' protocol.  It must yield a (<memcached>, cache_key) tuple.")
            
            if isinstance(cache_key, unicode):
                cache_key = cache_key.encode('ascii')
            
            result = mc.get(cache_key)

            if not result:
                try:
                    result = generator.next()
                except StopIteration:
                    pass

                if result:
                    mc.set(cache_key, result)

            return result
        return decorated
    return decorator


def cached2(key_format, memcached_instance = '__default__'):
    def decorator(undecorated):
        def raise_error(msg, *args, **kwargs):
            msg = msg.format(*args, **kwargs)
            msg = "{0.__name__} does not conform to the 'cached' protocol. {1}".format(undecorated, msg)
            raise RuntimeError(msg)

        if key_format is not None:
            if not callable(getattr(key_format, 'format', None)):
                raise_error("'key_format' must support the .format(...) method.")        

        @functools.wraps(undecorated)
        def decorated(*args, **kwargs):
            generator = undecorated(*args, **kwargs)

            if not type(generator) == types.GeneratorType:
                raise_error("It must return a generator.")

            mc = config.instance("memcache.{0}".format(memcached_instance))

            if not callable(getattr(mc, 'get', None)) or not callable(getattr(mc, 'set', None)):
                raise_error("The <memcached> instance for this function must support the .get(...) and .set(...) methods.")

            try:
                key_format_args = generator.next()
            except StopIteration:
                raise_error("It must yield format arguments to be applied to key_format.")
                
            if not isinstance(key_format_args, tuple):
                key_format_args = (key_format_args,)

            try:
                key = key_format.format(*key_format_args)
            except Exception, e:
                raise_error(str(e))

            if isinstance(key, unicode):
                key = key.encode('ascii')

            result = mc.get(key)

            if not result:
                try:
                    result = generator.next()
                except StopIteration:
                    raise_error("It must yield a value after it yields format arguments.")

                if result:
                    mc.set(key, result)

            return result
        return decorated
    return decorator    
    

class CacheKeyGenerator(object):
    def __init__(self, *key_parts):
        self._file_names = []
        self._file_parts = []
        self._key_parts = key_parts
        self._key = None
    
    def add_files(self, files):
        if files:
            self._key = None

        for f in files:
            index = bisect.bisect(self._file_names, f)
            self._file_names.insert(index, f)
            self._file_parts.insert(index + 1, "{0}:{1}".format(f, os.stat(f).st_mtime))

    @property
    def key(self):
        if not self._key:
            parts = itertools.chain(self._key_parts, self._file_parts)
            parts = (str(part) for part in parts)
            self._key = security.hash(':'.join(parts))

            if isinstance(self._key, unicode):
                self._key = self._key.encode('ascii')

        return self._key