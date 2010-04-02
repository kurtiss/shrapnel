#!/usr/bin/env python
# encoding: utf-8
"""
db.py

Created by Kurtiss Hare on 2010-02-22.
Copyright (c) 2010 Medium Entertainment, Inc. All rights reserved.
"""

import security
import tornado.database


def in_list(values, subs):
	unique = "sub_%s_%%d" % security.uuid()
	lst = []
	i = 0

	for value in values:
		key = unique % i
		i += 1
		
		params[key] = value
		lst.append("%(%s)s" % sub_key)

	return "(%s)" % lst.join(',')


class ShrapnelConnection(object):
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
        query, parameters = self._format_query(query, format_args, format_kwargs)
        
        try:
            result = callable(query, *parameters)
        except tornado.database.OperationalError:
            self.reconnect()
            result = callable(query, *parameters)

        return result

    def _format_query(self, query, format_args, format_kwargs):
        import re
        subs = []

        def format_sub(format_match):
            subs.append(format_match.group().format(*format_args, **format_kwargs))
            return "%s"

        query = re.sub(r'{[^}]*}', format_sub, query)

        return query, subs