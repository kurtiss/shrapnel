#!/usr/bin/env python
# encoding: utf-8
"""
classtools.py

Created by Kurtiss Hare on 2010-05-05.
Copyright (c) 2010 Medium Entertainment, Inc. All rights reserved.
"""

import threading

class UserFunction(object):
    def __new__(cls, *args, **kwargs):
        instance = super(UserFunction, cls).__new__(cls)
        result = None

        if isinstance(instance, cls):
            instance.__init__(*args, **kwargs)
            result = instance()

        if isinstance(result, cls):
            raise RuntimeError("{0.__name__}.__call__ cannot return an instance of {0.__name__}, otherwise the __new__ mechanism would call __init__ twice.".format(cls))

        return result

    def __call__(self):
        pass


class PooledFunction(object):
    def __new__(cls, *args, **kwargs):
        instance = super(PooledFunction, cls).__new__(cls)
        result = None
        
        if isinstance(instance, cls):
            super(cls, )
            instance.__init__()
            instance.__
            result = instance()
        
        if isinstance(result, cls):
            raise RuntimeError("{0.__name__}.__call__ cannot return an instance of {0.__name__}, otherwise the __new__ mechanism would call __init__ twice.".format(cls))

        kwargs['pool']
        
    
    @classmethod
    def reconstruct_and_execute(cls, args, kwargs):
        cls(None, None, None, *args, **kwargs)
        

    def __init__(self, pool, handler, callback, *args, **kwargs):
        self.pool = pool
        self.handler = handler
        self.callback = callback
        self.args = args
        self.kwargs = kwargs
        super(PooledFunction, self).__init__(*args, **kwargs)

    def __call__(self):
        self.pool.apply_async(self.reconstruct_and_execute, (self.args, self.kwargs), dict(), self._callback)

    def _callback(self, result):
        ioloop = tornado.ioloop.IOLoop.instance()
        ioloop.add_callback(functools.partial(self.callback, result))

    def execute(self):
        pass


class BackgroundFunction(UserFunction):
    def __init__(self, callback = None):
        self.callback = callback
        super(BackgroundFunction, self).__init__()

    def __call__(self):
        if self.callback:
            import web
            target = web.flagger(self.execute, self.callback)
        else:
            target = self.execute

        threading.Thread(target = target).start()

    def execute(self):
        pass