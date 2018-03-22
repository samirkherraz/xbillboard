#!/usr/bin/python

import os
import sys
from threading import Thread
import threading

class Sync(Thread):
    def __init__(self, url, localdir, delay):
        Thread.__init__(self)
        self._stop = threading.Event()
        self.delay = float(delay)
        self.url = url
        self.localdir = localdir
        self.cmd = "wget -N "+self.url+" -P "+self.localdir


    def run(self):
        while not self.stopped():
            os.system(self.cmd)
            if not self.stopped():
                self._stop.wait(self.delay)
        print "Sync Exit"

    def cleanUp(self):
        os.system("rm -vf "+self.localdir+"*")


    def stopped(self):
        return self._stop.isSet()

    def stop(self):
        self._stop.set()
