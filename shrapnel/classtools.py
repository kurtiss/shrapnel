#!/usr/bin/env python
# encoding: utf-8
"""
classtools.py

Created by Kurtiss Hare on 2010-05-05.
Copyright (c) 2010 Medium Entertainment, Inc. All rights reserved.
"""

import threading, multiprocessing, sys, atexit, copy


# http://stackoverflow.com/questions/2173206/is-there-any-way-to-create-a-class-property-in-python
class classprop(object):
  def __init__(self, f):
    self.f = classmethod(f)
  def __get__(self, *a):
    return self.f.__get__(*a)()


class UserFunction(object):
    def __new__(cls, *args, **kwargs):
        instance = super(UserFunction, cls).__new__(cls)
        run = kwargs.pop('run', True)
        if run:
            return cls._call_from_new(instance, args, kwargs)
        else:
            return instance

    @classmethod
    def _call_from_new(cls, instance, args, kwargs):
        result = None
        if isinstance(instance, cls):
            result = instance()

        if isinstance(result, cls):
            raise RuntimeError("{0.__name__}.__call__ cannot return an instance of {0.__name__}, otherwise the __new__ mechanism would call __init__ twice.".format(cls))

        return result

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def __call__(self):
        pass

def run_background_func(cls, args, kwargs):
    """
    This function is required since we can't pickle bound instance methods.
    """
    instance = cls(run=False, *args, **kwargs)
    return instance.execute()

class BackgroundFunction(UserFunction):
    _procpool = None
    def __init__(self, callback=None, **kwargs):
        self.callback = callback
        super(BackgroundFunction, self).__init__(**kwargs)

    @classprop
    def procpool(cls):
        if not cls._procpool:
            cls._procpool = multiprocessing.Pool()
            def onclose():
                cls._procpool.close()
            atexit.register(onclose)
        return cls._procpool

    @classmethod
    def delay(cls, *args, **kwargs):
        instance = cls(run=False, *args, **kwargs)
        assert instance
        sys.stderr.flush()
        sys.stdout.flush()
        if getattr(instance, 'callback', None):
            callback = nonimmediate(instance.callback)
            result = cls.procpool.apply_async(run_background_func,
                                              args=(instance,), 
                                              callback=callback)
        else:
            result = cls.procpool.apply_async(run_background_func, [cls, args, kwargs])
        return result

    @property
    def target(self):
        if getattr(self, 'callback', None):
            import web
            return web.flagger(self.execute, self.callback)
        else:
            return self.execute

    def __call__(self):
        return threading.Thread(target = self.target).start()

    def execute(self):
        pass
