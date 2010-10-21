#!/usr/bin/env python
# encoding: utf-8
"""
command.py

Created by Kurtiss Hare on 2010-02-10.
Copyright (c) 2010 Medium Entertainment, Inc. All rights reserved.
"""

from shrapnel import config
import logging
import logging.handlers
import optparse
import os
import signal
import sys
import time
import tornado.httpserver
import tornado.ioloop
from tornado.options import options as tornado_options, parse_command_line
import tornado.web
import shrapnel.classtools


class ShrapnelApplication(object):
    cmd_options = []

    def get_tornado_server(self, application):
        return tornado.httpserver.HTTPServer(application)
        
    def get_tornado_application(self):
        return tornado.web.Application([])
        
    def __init__(self, path, version = '', command = None):
        self.autoreload = False
        self.path = path
        self.version = version
        self.command = command or self.serve

    @property
    def _tornado_server(self):
        if not hasattr(self, '_tornado_server_instance'):
            self._tornado_server_instance = self.get_tornado_server(self._tornado_application)
        return self._tornado_server_instance
    
    @property
    def _tornado_application(self):
        if not hasattr(self, '_tornado_application_instance'):
            self._tornado_application_instance = self.get_tornado_application()
            settings = self._tornado_application_instance.settings
            settings['template_path'] = settings.get('template_path', os.path.join(self.path, 'templates'))

        return self._tornado_application_instance

    def run(self):
        parser = optparse.OptionParser(
            usage       = "usage: %prog [options]",
            version     = "%%prog %s" % (self.version,),
            description = "Tornado Web Server +shrapnel"
        )

        parser.add_option("-p", "--port",
            action  = "store",
            dest    = "port",
            default = "80",
            help    = "The port on which the server should be run."
        )
        
        parser.add_option("-P", "--pidfile",
            action  = "store",
            dest    = "pidfile",
            default = None,
            help    = "The path to a file which will contain the server's process ID."
        )
        
        parser.add_option("-e", "--errorlog",
            action  = "store",
            dest    = "errorlog",
            default = None,
            help    = "The path to a file which will contain the server's error log messages."
        )
        
        parser.add_option("-i", "--infolog",
            action  = "store",
            dest    = "infolog",
            default = None,
            help    = "The path to a file which will contain the server's informational log messages."
        )       

        parser.add_option('--profile',
                action='store_true',
                dest='profile',
                default=None,
                help='Turn profiling on',
                )
        parser.add_option('--no-profile',
                action='store_false',
                dest='profile',
                help='Turn profiling off',
                )

        parse_command_line([])
        for args, kwargs in self.cmd_options:
            parser.add_option(*args, **kwargs)

        self.options, args = parser.parse_args()
        if self.options.profile is not None:
            tornado_options.enable_appstats=self.options.profile
        os.chdir(self.path)

        # tornado.locale.load_translations(
        #   os.path.join(os.path.dirname(__file__), "translations")
        # )

        signal.signal(signal.SIGINT, self.graceful_stop)
        signal.signal(signal.SIGTERM, self.graceful_stop)
        self.start(self.options)

    def _daemonize(self, options):
        # http://code.activestate.com/recipes/278731/
        pid = os.fork()

        if pid == 0:
            os.setsid()
            pid2 = os.fork()

            if pid2 != 0:
                os._exit(0)
        else:
            os._exit(0)

        import resource

        os.chroot("/")
        os.umask(0)

        if os.access(options.pidfile, os.F_OK):
            f = open(options.pidfile, "r")
            f.seek(0)
            old_pid = f.readline()
            
            if os.path.exists("/proc/{0}".format(old_pid)):
                print "Old PID file exists, and process is still running: {0}".format(options.pidfile)
                sys.exit(1)
            else:
                print "Cleaning old PID file, which points to a non-running process."
                os.remove(options.pidfile)

        maxfd = resource.getrlimit(resource.RLIMIT_NOFILE)[1]

        if (maxfd == resource.RLIM_INFINITY):
            maxfd = 1024

        for fd in range(3, maxfd):
            try:
                os.close(fd)
            except  OSError:
                pass

        sys.stdin.close()

        if options.infolog or options.errorlog:
            _setup_logging(options)

        if options.infolog:
            sys.stdout = _LoggingDescriptor(logging.info)
        else:
            sys.stdout = _NullDescriptor()
        
        if options.errorlog:
            sys.stderr = _LoggingDescriptor(logging.error)
        else:
            sys.stderr = _NullDescriptor()  

        f = open(options.pidfile, "w")
        f.write("{0}".format(os.getpid()))
        f.close()

    def start(self , options):
        if options.pidfile:
            self._daemonize(options)
        elif options.infolog or options.errorlog:
            _setup_logging(options)
        
        # TODO: can't wait to get rid of this
        self._pid = os.getpid()
        shrapnel.classtools.ProcessFunction.procpool
        
        self._tornado_server.listen(int(options.port))

        if (self.autoreload):
            import tornado.autoreload
            tornado.autoreload.start()

        try:
            self.command()
            self.graceful_stop()
        except KeyboardInterrupt, e:
            self.graceful_stop()
            
    def serve(self):
        self._tornado_server.io_loop.start()
        
    def graceful_stop(self, *args, **kwargs):
        if os.getpid() == self._pid:
            self._tornado_server.stop()
            io_loop = self._tornado_server.io_loop

            if io_loop.running():
                print "running"
                check_graceful_stop = tornado.ioloop.PeriodicCallback(
                    self._poll_graceful_stop, 
                    250, 
                    io_loop = io_loop
                )

                check_graceful_stop.start()

                io_loop.add_timeout(
                    time.time() + 10000, 
                    self._graceful_stop_now
                )
            else:
                self._graceful_stop_now()
    
    def _graceful_stop_now(self):
        self._tornado_server.io_loop.stop()
        shrapnel.classtools.ProcessFunction.procpool.close()
        self.stop()
        sys.exit(0)

    def _poll_graceful_stop(self):
        if len(self._tornado_server.io_loop._handlers) == 1:
            self._graceful_stop_now()
    
    def stop(self):
        pass


def _setup_logging(options):
    class _InfoFilter(logging.Filter):
        def filter(self, record):
            levelno = record.__dict__.get('levelno', 0)
            if levelno >= logging.INFO and levelno <= logging.WARNING:
                return 1
            return 0
            
    class _ErrorFilter(logging.Filter):
        def filter(self, record):
            if record.__dict__.get('levelno', 0) >= logging.ERROR:
                return 1
            return 0
    
    logger = logging.getLogger()
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    if options.infolog:
        handler = logging.handlers.WatchedFileHandler(options.infolog)
        handler.setLevel(logging.INFO)
        handler.setFormatter(formatter)
        handler.addFilter(_InfoFilter())
        logger.addHandler(handler)
    
    if options.errorlog:
        handler = logging.handlers.WatchedFileHandler(options.errorlog)
        handler.setLevel(logging.ERROR)
        handler.setFormatter(formatter)
        handler.addFilter(_ErrorFilter())
        logger.addHandler(handler)


class _NullDescriptor(object):
    def write(self, value):
        pass
    
    def flush(self):
        pass

class _LoggingDescriptor(object):
    def __init__(self, logger):
        self.logger = logger

    def write(self, data):
        self.logger(data)       

    def flush(self):
        pass
