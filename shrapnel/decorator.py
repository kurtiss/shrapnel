from functools import wraps, partial

import tornado.ioloop

def background_func(func):
    """
    A decorator that will convert the decorated function to a BackgroundFunction.
    """
    # Putting this in the decorator function to avoid circular imports
    from shrapnel.classtools import BackgroundFunction
    class FuncClass(BackgroundFunction):
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs
            super(FuncClass, self).__init__()

        def execute(self):
            return func(*self.args, **self.kwargs)

    @wraps(func)
    def decorated(*args, **kwargs):
        return FuncClass(*args, **kwargs)

    return decorated

def nonimmediate(func):
    """
    Decorator that makes *func* return immediately and be called during the
    next iteration of the IO loop.
    """
    ioloop = tornado.ioloop.IOLoop.instance()
    @wraps(func)
    def delayed_call(*args, **kwargs):
        callback = partial(func, *args, **kwargs)
        ioloop.add_callback(callback)
    return delayed_call
