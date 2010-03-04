#!/usr/bin/env python
# encoding: utf-8
"""
caching.py

Created by Kurtiss Hare on 2010-02-25.
Copyright (c) 2010 Medium Entertainment, Inc. All rights reserved.
"""

import bisect
import functools
import os
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
				
			if isinstance(cache_key, unicode):
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
			index = bisect.bisect(filenames, f)
			self._file_names.insert(index, f)
			self._file_parts.insert(index + 1, "{0}:{1}".format(f, os.stat(f).st_mtime))

	@property
	def key(self):
		if not self._key:
			self._key = shrapnel.security.hash(':'.join(self._key_parts + self._file_parts))

			if isinstance(self._key, unicode):
				self._key = self._key.encode('ascii')

		return self._key