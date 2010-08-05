import functools
import threading

import pymongo.connection
import pymongo.errors

from . import config

class MongoHelper(object):
    def __init__(self, method_name, config):
        self.provider = config["provider"]
        self.key = method_name

    def do(self, *args):
        results = []
        exc = None

        db = self.get_db()
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

    def get_db(self):
        """
        Get a new instance of the mongo db.
        """
        return config.instance("{0}.{1}".format(self.provider, self.key))
