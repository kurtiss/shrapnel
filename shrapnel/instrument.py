import threading, time, os, sys

class ProfilingThread(threading.Thread):
    daemon = True
    def __init__(self, ioloop):
        self.ioloop = ioloop
        threading.Thread.__init__(self)

    def run(self):
        pid = os.getpid()
        outfile_path = os.path.abspath('profdata-{0}.log'.format(pid)) 
        print outfile_path
        sys.stdout.flush()
        outfile = open(outfile_path, 'w')
        while True:
            handler_len = len(self.ioloop._handlers)
            event_len = len(self.ioloop._events)
            callback_len = len(self.ioloop._callbacks)
            print >> outfile, ', '.join([str(time.time()), str(handler_len), str(event_len), str(callback_len)])
            time.sleep(5)
