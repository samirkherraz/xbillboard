#!/usr/bin/python

import os
import sys
import threading
from threading import Thread
import time


class ThLoop(Thread):

    def __init__(self, delay):
        Thread.__init__(self)
        self._stop = threading.Event()
        self.delay = float(delay)

    def run(self):
        while not self.stopped():
            if not self.loopjob():
                time.sleep(self.delay)

    def stopped(self):
        return self._stop.isSet()

    def stop(self):
        self._stop.set()

    def setDelay(self, delay):
        self.delay = float(delay)
