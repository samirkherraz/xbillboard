#!/usr/bin/python

__author__ = "Samir KHERRAZ"
__license__ = "GPLv3"
__maintainer__ = "Samir KHERRAZ"
__email__ = "samir.kherraz@outlook.fr"

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
        self.cmd = "wget -q -N "+self.url+" -P "+self.localdir

    def run(self):
        while not self.stopped():
            os.system(self.cmd)
            self._stop.wait(self.delay)

    def stopped(self):
        return self._stop.isSet()

    def stop(self):
        self._stop.set()
