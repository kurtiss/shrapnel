import pymongo.connection
import pymongo.errors

import functools
import config


def reconnecting(key, retries = 2):
    def decorator(undecorated):
        @functools.wraps(undecorated)
        def decorated(*args, **kwargs):
            exc = None
            db = config.instance(key)

            try:
                for i in xrange(0, retries):
                    try:
                        return undecorated(db, *args, **kwargs)
                    except (pymongo.errors.AutoReconnect), e:
                        exc = e
            finally:
                pass
                #db.connection.end_request()

            raise exc
        return decorated
    return decorator