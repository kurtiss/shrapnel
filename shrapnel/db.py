#!/usr/bin/env python
# encoding: utf-8
"""
db.py

Created by Kurtiss Hare on 2010-02-22.
Copyright (c) 2010 Medium Entertainment, Inc. All rights reserved.
"""

import functools
import types


def transaction(retries=1):
    def decorator(undecorated):
        @functools.wraps(undecorated)
        def decorated(*args, **kwargs):
            generator = undecorated(*args, **kwargs)

            if not type(generator) == types.GeneratorType:
                raise RuntimeError("{0.__name__} does not conform to the 'transaction' protocol.  It must return a generator.".format(undecorated))

            try:
                db = generator.next()
            except StopIteration:
                db = None

            if not hasattr(db, 'execute') or not callable(db.execute):
                raise RuntimeError('bad type for "db"')

            exception = None
            result = None
            for i in range(retries):
                db.execute('begin')
                try:
                    try:
                        result = generator.next()
                    except StopIteration:
                        exception = RuntimeError("{0.__name__} does not conform to the 'transaction' protocol.  It must return a generator of sufficient length.".format(undecorated))
                        break

                except Exception as e:
                    db.execute('rollback')
                    generator = undecorated(*args, **kwargs)
                    generator.next()
                    exception = e
                else:
                    db.execute('commit')
                    return result
            raise exception
        return decorated
    return decorator


class InList(object):
    def __init__(self, list):
        self.list = list

    def __parameterize__(self, format_spec):
        return self.list, str(self)

    def __str__(self):
        import itertools
        return "({0})".format(', '.join(itertools.repeat("%s", len(self.list))))