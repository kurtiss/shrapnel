#!/usr/bin/env python
# encoding: utf-8
"""
config.py

Created by Kurtiss Hare on 2010-02-10.
Copyright (c) 2010 Medium Entertainment, Inc. All rights reserved.
"""

import threading

def _split_name(name):
    if '.' not in name:
        name += ".__default__"
    return name.split('.')

def instance(name, *args, **kwargs):
    cls_name, method_name = _split_name(name)
    provider = ProviderMetaclass.find(cls_name)
    if provider._instance == None:
        provider._instance = provider()

    return provider._instance.__provide__(method_name)

def settings(name):
    cls_name, method_name = _split_name(name)
    provider = ProviderMetaclass.find(cls_name)()
    return provider.get_config(method_name)

def list_instances():
    """
    Return a list of all top-level instance names.  This will not include any
    specific configuration.  For instance, only 'foo' will be included in the
    list if 'foo', 'foo.bar', 'foo.baz', etc are valid.
    """
    return ProviderMetaclass._subclasses.keys()



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

    @classmethod
    def find(cls, cls_name):
        try:
            return cls._subclasses[cls_name]
        except KeyError:
            raise LookupError, "Couldn't find provider class for {0}".format(cls_name)


class SingletonProvider(object):
    def __init__(self, *args, **kwargs):
        self._instances = dict()
        super(SingletonProvider, self).__init__(*args, **kwargs)

    def __provide__(self, method_name):
        try:
            result = self._instances[method_name]
        except KeyError:
            with threading.Lock():
                try:
                    result = self._instances[method_name]
                except KeyError:
                    result = self.get_config(method_name)

        return result


class InstanceProvider(object):
    def __provide__(self, method_name):
        config = self. get_config(method_name)
        return self.construct(config)


class Provider(object):
    __metaclass__ = ProviderMetaclass
    __abstract__ = True
    _instance = None

    def __defaults__(self):
        return dict()

    def construct(self, configuration):
        return configuration

    def get_config(self, method_name):
        config_method = getattr(self, method_name)
        config = {}
        config.update(self.__defaults__())
        config.update(config_method())
        return config

    def __init__(self):
        self._instances = {}
        super(Provider, self).__init__()

    def __default__(self):
        return dict()

    def __provide__(self, method_name):
        raise RuntimeError("A __provide__ method has not been set for this provider.")


class MongoConnectionProvider(SingletonProvider, Provider):
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
            host        = 'localhost',
            port        = 27017,
            database    = 'database',
            timeout     = None,
            r_host      = None,
            r_port      = None
        )


class MongoProvider(Provider):
    __abstract__ = True

    class DummyDB(object):
        def __getattr__(self, name):
            raise NotImplementedError

    def __provide__(self, method_name):
        from . import mongodb
        config_method = getattr(self, method_name)
        config = dict(self.__defaults__().items() + config_method().items())
        if config.get('dummy', False):
            from warnings import warn
            warn("Using Dummy Mongodb.  If you don't know what this means, disable the dummy option in your mongo settings.")
            return self.DummyDB()

        return mongodb.MongoHelper(method_name, config)

    def __defaults__(self):
        # better option?
        return dict(
            provider = 'no_provider_defined'
        )

_client_data = threading.local()
class MemcacheProvider(InstanceProvider, Provider):
    __abstract__ = True

    def construct(self, config):
        global _client_data
        if not hasattr(_client_data, 'conn'):
            import memcache
            _client_data.conn = memcache.Client(["%s:%d" % (config['host'], config['port'])], debug=config['debug'])
        return _client_data.conn

    def __defaults__(self):
        return dict(
            host = 'localhost',
            port = 11211,
            debug = 0
        )


class DbPoolProvider(SingletonProvider, Provider):
    __abstract__ = True

    def construct(self, config):
        import db
        return db.ConnectionPool.instance(
            config['host'],
            config['database'],
            config['user'],
            config['password']
        )

    def __defaults__(self):
        return dict(
            host            = 'localhost:3306', # '/path/to/mysql.sock'
            database        = 'database',
            user            = None,
            password        = None
        )


class DatabaseProvider(InstanceProvider, Provider):
    __abstract__ = True

    def construct(self, config):
        import db
        return db.Connection(config['pool'])

    def __defaults__(self):
        return dict(
            pool    = '__default__'
        )


class ConfigurationLookupError(LookupError):
    pass
