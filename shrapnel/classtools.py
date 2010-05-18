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