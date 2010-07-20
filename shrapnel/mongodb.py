import pymongo.connection
import pymongo.errors

import functools
import config
import threading

class MongoHelper(object):
    def __init__(self, method_name, config):
        self.provider = config["provider"]
        self.key = method_name
        self.db = None

    def do(self, *args):
        db = config.instance("{0}.{1}".format(self.provider, self.key))
        results = []
        exc = None

        try:
            for fn in args:
                for i in xrange(0, 2):
                    try:
                        results.append(fn(db))
                    except (pymongo.errors.AutoReconnect), e:
                        exc = e
                    else:
                        exc = None
                        break

                if exc:
                    raise exc

        finally:
            db.connection.end_request()

        if len(args) == 1:
            return results[0]

        return results