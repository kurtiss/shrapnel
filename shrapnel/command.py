#!/usr/bin/env python
# encoding: utf-8
"""
command.py

Created by Kurtiss Hare on 2010-02-10.
Copyright (c) 2010 Medium Entertainment, Inc. All rights reserved.
"""

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

		options, args = parser.parse_args()
		os.chdir(self.path)

		# tornado.locale.load_translations(
		# 	os.path.join(os.path.dirname(__file__), "translations")
		# )

		signal.signal(signal.SIGINT, self._do_signal)
		signal.signal(signal.SIGTERM, self._do_signal)
		self.start(int(options.port))

	def start(self , port):
		try:
			application = self.get_tornado_application()
			server = self.get_tornado_server(application)
			server.listen(port)

			if (self.autoreload):
				import tornado.autoreload
				tornado.autoreload.start()

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