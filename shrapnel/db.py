#!/usr/bin/env python
# encoding: utf-8
"""
db.py

Created by Kurtiss Hare on 2010-02-22.
Copyright (c) 2010 Medium Entertainment, Inc. All rights reserved.
"""

import security
import tornado.database


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
        query = formatter.format(query, format_args, format_kwargs)
        
        try:
            result = callable(query, *formatter.parameters)
        except tornado.database.OperationalError:
            self.reconnect()
            result = callable(query, *formatter.parameters)

        return result