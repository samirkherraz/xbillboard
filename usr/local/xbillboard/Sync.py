#!/usr/bin/python

import os
import sys
import threading
from threading import Thread
import time
from SystemCall import SystemCall


class Sync(Thread):
    def __init__(self, url, localdir, delay):
        Thread.__init__(self)
        self._stop = threading.Event()
        self.url = url
        self.localdir = localdir
        self.delay = int(delay)

    def run(self):
        self.cmd = "wget -N "+self.url+" -P "+self.localdir
        while not self.stopped():
            SystemCall(self.cmd, False)
            time.sleep(self.delay)

    def stopped(self):
        return self._stop.isSet()

    def cleanUp(self):
        SystemCall("rm -vf "+self.localdir+"*", False)

    def stop(self):
        self._stop.set()
