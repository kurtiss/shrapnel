#!/usr/bin/env python
# encoding: utf-8
"""
config.py

Created by Kurtiss Hare on 2010-02-10.
Copyright (c) 2010 Medium Entertainment, Inc. All rights reserved.
"""

def instance(name, *args, **kwargs):
	if '.' not in name:
		name += ".__default__"

	cls_name, method_name = name.split('.')

	try:
		MyProvider = ProviderMetaclass._subclasses[cls_name]
	except KeyError:
		raise ConfigurationLookupError()
	
	if MyProvider._instance == None:
		MyProvider._instance = MyProvider()

	try:
		result = MyProvider._instance._instances[method_name]
	except KeyError:
		config_method = getattr(MyProvider._instance, method_name)
		config = dict(MyProvider._instance.__defaults__().items() + config_method().items())
		result = MyProvider._instance._instances[method_name] = MyProvider._instance.construct(config)

	return result


class ProviderMetaclass(type):
	_subclasses = {}

	def __new__(cls, name, bases, attrs):
		new_cls = type.__new__(cls, name, bases, attrs)

		if not attrs.pop('__abstract__', False):
			namespace = attrs.get('__namespace__', False)

			if not namespace:
				import re
				match = re.match(r'^(.*)ConfigurationProvider$', name)

				if match:
					namespace = match.group(1).lower()
				else:
					namespace = name

			cls._subclasses[namespace] = new_cls

		return new_cls


class Provider(object):
	__metaclass__ = ProviderMetaclass
	__abstract__ = True
	_instance = None

	def __defaults__(self):
		return dict()

	def construct(self, configuration):
		return configuration

	def __init__(self):
		self._instances = {}
		super(Provider, self).__init__()
		
	def __default__(self):
		return dict()


class MySqlProvider(Provider):
	__abstract__ = True

	def construct(self, config):
		import tornado.database

		return tornado.database.Connection(
			config['host'], 
			config['database'], 
			config['user'], 
			config['password']
		)
		
	def __defaults__(self):
		return dict(
			host = 'localhost:3306', # '/path/to/mysql.sock'
			database = 'database',
			user = None,
			password = None,
		)


class MongoProvider(Provider):
	__abstract__ = True
	
	def construct(self, config):
		import pymongo.connection
		l_port = int(config['port'])
		r_host = config.get('r_host')
		r_port = config.get('r_port') or l_port
		
		if r_host:
			conn = pymongo.connection.Connection.paired(
				(config['host'], l_port), 
				right=(r_host, int(r_port))
			)
		else:
			conn = pymongo.connection.Connection(
				config['host'],
				l_port,
				network_timeout = config['timeout']
			)
		
		return conn[config['database']]

	def __defaults__(self):
		return dict(
			host = 'localhost',
			port = 27017,
			database = 'database',
			timeout = None,
			r_host = None,
			r_port = None,
		)


class MemcacheProvider(Provider):
	__abstract__ = True
	
	def construct(self, config):
		import memcache
		return memcache.Client(["%s:%d" % (config['host'], config['port'])], debug=config['debug'])
	
	def __defaults__(self):
		return dict(
			host = 'localhost',
			port = 11211,
			debug = 0
		)


class ConfigurationLookupError(LookupError):
	pass