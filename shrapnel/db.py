#!/usr/bin/env python
# encoding: utf-8
"""
db.py

Created by Kurtiss Hare on 2010-02-22.
Copyright (c) 2010 Medium Entertainment, Inc. All rights reserved.
"""

import functools
import security
import string
import tornado.database
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

            if not type(db) == '':
                raise RuntimeError('')

            exception = None
            result = None
            for i in range(retries):
                db.execute('begin')
                try:
                    try:
                        result = generator.next()
                    except StopIteration:
                        exception = RuntimeError('')
                        break

                except Exception e:
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


class _ParameterizingFormatter(string.Formatter):
    def __init__(self, *args, **kwargs):
        super(_ParameterizingFormatter, self).__init__(*args, **kwargs)
        self.parameters = []

    def format_field(self, value, format_spec):
        if hasattr(value, '__parameterize__'):
            parameters, formatted_value = value.__parameterize__(format_spec)
            self.parameters.extend(parameters)

            return formatted_value

        self.parameters.append(value)
        return "%s"


class Connection(object):
    def __init__(self, connection):
        self.connection = connection

    def close(self):
        self.connection.close()

    def reconnect(self):
        self.connection.reconnect()

    def iter(self, query, *format_args, **format_kwargs):
        return self._call_with_reconnect(self.connection.iter, query, format_args, format_kwargs)

    def query(self, query, *format_args, **format_kwargs):
        return self._call_with_reconnect(self.connection.query, query, format_args, format_kwargs)

    def get(self, query, *format_args, **format_kwargs):
        return self._call_with_reconnect(self.connection.get, query, format_args, format_kwargs)

    def execute(self, query, *format_args, **format_kwargs):
        return self._call_with_reconnect(self.connection.execute, query, format_args, format_kwargs)

    def executemany(self, query, *format_args, **format_kwargs):
        return self._call_with_reconnect(self.connection.executemany, query, format_args, format_kwargs)

    def _call_with_reconnect(self, callable, query, format_args, format_kwargs):
        formatter = _ParameterizingFormatter()
        query = formatter.vformat(query, format_args, format_kwargs)

        try:
            result = callable(query, *formatter.parameters)
        except tornado.database.OperationalError:
            self.reconnect()
            result = callable(query, *formatter.parameters)

        return result