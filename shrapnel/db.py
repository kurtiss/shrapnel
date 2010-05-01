#!/usr/bin/env python
# encoding: utf-8
"""
db.py

Created by Kurtiss Hare on 2010-02-22.
Copyright (c) 2010 Medium Entertainment, Inc. All rights reserved.
"""

import collections
import datetime
import functools
import security
import string
import threading
import tornado.database
import tornado.ioloop
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

            if type(db) != Connection:
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


class ConnectionPool(object):
    """
    Tornado database connection pool.  acquire() to grab a connection and release() to
    move it back to the pool.  Caching of connections is keyed off thread-local-storage.
    """
    def __init__(self, args, kwargs):
        self.tls = threading.local()
        self.queue = collections.deque()
        self.args = args
        self.kwargs = kwargs

    def acquire(self):
        connection = getattr(self.tls, 'connection', None)

        if not connection:
            try:
                (connection, last_used_time) = self.queue.pop()
            except IndexError:
                connection = self.create()

            self.tls.connection = connection

        return connection
    
    def create(self):
        print "create!"
        return tornado.database.Connection(*self.args, **self.kwargs)
    
    def release(self):
        connection = getattr(self.tls, 'connection', None)

        if connection:
            self.queue.append((connection, datetime.datetime.utcnow()))
            self.tls.connection = None

    def prune(self):
        now = datetime.datetime.utcnow()
        max_idle_time = datetime.timedelta(minutes = 1)

        while True:
            try:
                connection, last_used_time = self.queue.popleft()
            except IndexError:
                break
            
            if (last_used_time - now) <= max_idle_time:
                self.queue.appendleft((connection, last_used_time))
                break


class Connection(object):
    def __init__(self, *args, **kwargs):
        self.pool = ConnectionPool(args, kwargs)
        self.pruner = tornado.ioloop.PeriodicCallback(self.pool.prune, 30000)
        self.pruner.start()
    
    def __del__(self):
        self.pruner.stop()
        self.close()

    def close(self):
        self.pool.release()

    def reconnect(self):
        self.pool.acquire().reconnect()

    def iter(self, query, *format_args, **format_kwargs):
        return self._call_with_reconnect(self.pool.acquire().iter, query, format_args, format_kwargs)

    def query(self, query, *format_args, **format_kwargs):
        return self._call_with_reconnect(self.pool.acquire().query, query, format_args, format_kwargs)

    def get(self, query, *format_args, **format_kwargs):
        return self._call_with_reconnect(self.pool.acquire().get, query, format_args, format_kwargs)

    def execute(self, query, *format_args, **formats_kwargs):
        return self._call_with_reconnect(self.pool.acquire().execute, query, format_args, format_kwargs)

    def executemany(self, query, *format_args, **format_kwargs):
        return self._call_with_reconnect(self.pool.acquire().executemany, query, format_args, format_kwargs)

    def executecursor(self, query, *format_args, **format_kwargs):
        formatter = _ParameterizingFormatter()
        query = formatter.vformat(query, format_args, format_kwargs)

        def _executecursor(q, *params):
            cursor = self.pool.acquire()._db.cursor()
            cursor.execute(q, params)
            return cursor

        return self._call_with_reconnect(_executecursor, query, *formatter.parameters)

    def _call_with_reconnect(self, callable, query, format_args, format_kwargs):
        formatter = _ParameterizingFormatter()
        query = formatter.vformat(query, format_args, format_kwargs)

        try:
            result = callable(query, *formatter.parameters)
        except tornado.database.OperationalError:
            self.reconnect()
            result = callable(query, *formatter.parameters)

        return result