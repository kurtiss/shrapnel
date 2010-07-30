from functools import wraps

from shrapnel.classtools import BackgroundFunction

def background_func(func):
    """
    A decorator that will convert the decorated function to a BackgroundFunction.
    """
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
