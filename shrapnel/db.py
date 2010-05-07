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
import weakref

from . import config


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
    Tornado database connection pool.  acquire() to grab a connection and reliniquish(connection) to
    move it back to the pool.  Caching of connections is keyed off thread-local-storage.
    """
    _instances = weakref.WeakValueDictionary()
    _pruner = None
    _pruner_lock = threading.Lock()

    @classmethod
    def instance(cls, *args, **kwargs):
        normalized = cls.normalize_args(*args, **kwargs)
        default_instance = cls(*args, **kwargs)
        instance = cls._instances.setdefault(normalized, default_instance)
        return instance

    @classmethod
    def normalize_args(cls, host, database, user = None, password = None):
        return (host, database, user, password)

    @classmethod
    def prune(cls):
        now = datetime.datetime.utcnow()
        max_idle_time = datetime.timedelta(minutes = 1)
        nonempty_pools = 0

        for instance in cls._instances.values():
            if instance:
                for pool in instance.pools.values():
                    while pool:
                        connection, last_used_time = pool.popleft()

                        if (now - last_used_time) <= max_idle_time:
                            nonempty_pools += 1
                            pool.appendleft((connection, last_used_time))
                            break

        if nonempty_pools == 0:
            with cls._pruner_lock:
                if cls._pruner:
                    cls._pruner.stop()
                    cls._pruner = None

    def __init__(self, *args, **kwargs):
        self.tls = threading.local()
        self.pools = weakref.WeakValueDictionary()
        self.args = args
        self.kwargs = kwargs

    def acquire(self):
        if not hasattr(self.tls, 'pool'):
            self.tls.pool = collections.deque()
            self.pools[id(self.tls.pool)] = self.tls.pool

        try:
            (connection, last_used_time) = self.tls.pool.pop()
        except IndexError:
            connection = self.create()

        return connection

    def create(self):
        return tornado.database.Connection(*self.args, **self.kwargs)

    def reliniquish(self, connection):
        self.tls.pool.append((connection, datetime.datetime.utcnow()))

        with self._pruner_lock:
            if not self._pruner:
                self._pruner = tornado.ioloop.PeriodicCallback(self.prune, 30000)
                self._pruner.start()


class Connection(object):
    def __init__(self, pool = '__default__'):
        self.pool = config.instance("dbpool.{0}".format(pool))
        self._connection = None

    @property
    def connection(self):
        if not self._connection:
            self._connection = self.pool.acquire()
        return self._connection

    def __del__(self):
        self.close()

    def close(self):
        if self._connection:
            self.pool.reliniquish(self._connection)

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

    def executecursor(self, query, *format_args, **format_kwargs):
        formatter = _ParameterizingFormatter()
        query = formatter.vformat(query, format_args, format_kwargs)

        def _executecursor(q, *params):
            cursor = self.connection._db.cursor()
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