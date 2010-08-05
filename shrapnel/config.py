#!/usr/bin/env python
# encoding: utf-8
"""
config.py

Created by Kurtiss Hare on 2010-02-10.
Copyright (c) 2010 Medium Entertainment, Inc. All rights reserved.
"""

import threading

def instance(name, *args, **kwargs):
    if '.' not in name:
        name += ".__default__"

    cls_name, method_name = name.split('.')

    try:
        MyProvider = ProviderMetaclass._subclasses[cls_name]
    except KeyError:
        raise LookupError("Couldn't find provider class for {0}, tried {1}{2}ConfigurationProvider.".format(name, cls_name[0].upper(), cls_name[1:].lower()))

    if MyProvider._instance == None:
        MyProvider._instance = MyProvider()

    return MyProvider._instance.__provide__(method_name)


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
                    config_method = getattr(self, method_name)
                    config = dict(self.__defaults__().items() + config_method().items())
                    result = self._instances[method_name] = self.construct(config)

        return result


class InstanceProvider(object):
    def __provide__(self, method_name):
        # pymongo will do the appropriate connection pooling.
        config_method = getattr(self, method_name)
        config = dict(self.__defaults__().items() + config_method().items())
        return self.construct(config)


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

    def __provide__(self, method_name):
        from . import mongodb
        config_method = getattr(self, method_name)
        config = dict(self.__defaults__().items() + config_method().items())
        return mongodb.MongoHelper(method_name, config)

    def __defaults__(self):
        # better option?
        return dict(
            provider = 'no_provider_defined'
        )


class MemcacheProvider(InstanceProvider, Provider):
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
