#!/usr/bin/env python
# encoding: utf-8
"""
command.py

Created by Kurtiss Hare on 2010-02-10.
Copyright (c) 2010 Medium Entertainment, Inc. All rights reserved.
"""

import logging
import logging.handlers
import optparse
import os
import signal
import sys
import tornado.httpserver
import tornado.ioloop
import tornado.web


class ShrapnelApplication(object):
	def get_tornado_server(self, application):
		return tornado.httpserver.HTTPServer(application)
		
	def get_tornado_application(self):
		return tornado.web.Application([])

	def __init__(self, path, version = '', command = None):
		self.autoreload = False
		self.path = path
		self.version = version
		self.command = command or self.serve

	def run(self):
		parser = optparse.OptionParser(
			usage		= "usage: %prog [options]",
			version		= "%%prog %s" % (self.version,),
			description	= "Tornado Web Server +shrapnel"
		)

		parser.add_option("-p", "--port",
			action	= "store",
			dest	= "port",
			default = "80",
			help	= "The port on which the server should be run."
		)
		
		parser.add_option("-P", "--pidfile",
			action	= "store",
			dest	= "pidfile",
			default	= None,
			help	= "The path to a file which will contain the server's process ID."
		)
		
		parser.add_option("-e", "--errorlog",
			action	= "store",
			dest	= "errorlog",
			default	= None,
			help	= "The path to a file which will contain the server's error log messages."
		)
		
		parser.add_option("-i", "--infolog",
			action	= "store",
			dest	= "infolog",
			default	= None,
			help	= "The path to a file which will contain the server's informational log messages."
		)		

		options, args = parser.parse_args()
		os.chdir(self.path)

		# tornado.locale.load_translations(
		# 	os.path.join(os.path.dirname(__file__), "translations")
		# )

		signal.signal(signal.SIGINT, self._do_signal)
		signal.signal(signal.SIGTERM, self._do_signal)
		self.start(options)

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
				print "Old PID file exists, and process is still running: {0}".format(pidfile)
				sys.exit(1)
			else:
				print "Cleaning old PID file, which points to a non-running process."
				os.remove(pid_file)

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

		f = open(pidfile, "w")
		f.write("{0}".format(os.getpid()))
		f.close()

	def start(self , options):
		if options.pidfile:
			self._daemonize(options)
		elif options.infolog or options.errorlog:
			_setup_logging(options)
		
		application = self.get_tornado_application()
		application.settings['template_path'] = application.settings.get('template_path', os.path.join(self.path, 'templates'))		
		server = self.get_tornado_server(application)
		server.listen(int(options.port))

		if (self.autoreload):
			import tornado.autoreload
			tornado.autoreload.start()

		try:
			self.command()
			self.stop()
		except KeyboardInterrupt, e:
			self.stop()
			
	def serve(self):
		tornado.ioloop.IOLoop.instance().start()
		
	def stop(self):
		sys.exit(0)	
		
	def _do_signal(self, signal, frame):
		self.stop()

def _setup_logging(options):
	class _InfoOnlyFilter(logging.Filter):
		def filter(self, record):
			print repr(record.__dict__)
			return 1
	
	class _LogRecord(logging.LogRecord):
		def __init__(self, name, level, *args, **kwargs):
			self.level = level
			super(_LogRecord, self).__init__(self, name, level, *args, **kwargs)

	class _Logger(logging.getLoggerClass()):
		def makeRecord(self, *args, **kwargs):
			print "making record"
			return _LogRecord(*args, **kwargs)

	logging.setLoggerClass(_Logger)
	
	logger = logging.getLogger()
	formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

	if options.infolog:
		handler = logging.handlers.WatchedFileHandler(options.infolog)
		handler.setLevel(logging.INFO)
		handler.setFormatter(formatter)
		handler.addFilter(_InfoOnlyFilter())
		logger.addHandler(handler)
	
	if options.errorlog:
		handler = logging.handlers.WatchedFileHandler(options.errorlog)
		handler.setLevel(logging.WARN)
		handler.setFormatter(formatter)
		logger.addHandler(handler)


class _NullDescriptor(object):
	def write(self, value):
		pass
		
class _LoggingDescriptor(object):
	def __init__(self, logger):
		self.logger = logger

	def write(self, data):
		logger(data)		