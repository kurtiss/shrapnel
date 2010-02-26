#!/usr/bin/env python
# encoding: utf-8
"""
caching.py

Created by Kurtiss Hare on 2010-02-25.
Copyright (c) 2010 Medium Entertainment, Inc. All rights reserved.
"""

import functools
import types

def cached():
	def decorator(undecorated):
		@functools.wraps(undecorated)
		def decorated(handler, *args, **kwargs):
			generator = undecorated(handler, *args, **kwargs)

			if not type(generator) == types.GeneratorType:
				raise RuntimeError("{0.__name__} does not conform to the 'cached' protocol.  It must return a generator.".format(undecorated))

			try:
				mc, cache_key = generator.next()
			except TypeError:
				raise RuntimeError("{0.__name__} does not conform to the 'cached' protocol.  It must yield a (<memcached>, cache_key) tuple.")
			
			if not hasattr(handler, '_cache'):
				handler._cache = {}
				
			if isinstance(s, unicode):
				cache_key = cache_key.encode('ascii')
			
			result = handler._cache.get(cache_key, None)

			if not result:
				result = mc.get(cache_key)

				if not result:
					try:
						result = generator.next()
					except StopIteration:
						pass

					if result:
						mc.set(cache_key, result)

				if result:
					handler._cache[cache_key] = result

			return result
		return decorated
	return decorator