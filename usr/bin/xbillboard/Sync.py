
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
        self.name = url.split('/')[::-1][0]
        self.__stop = threading.Event()
        self.name = url.split("/")[-1]
        self.delay = float(delay)
        self.url = url
        self.localdir = localdir
        self.cmd = "wget -q -N "+self.url+" -P "+self.localdir

    def run(self):
        while not self.stopped():
            try:
                open(self.localdir+self.name+".sync_lock", 'w').close()
                os.system(self.cmd)
                os.remove(self.localdir+self.name+".sync_lock")
                self.__stop.wait(self.delay)
            except:
                print("sync error")

    def stopped(self):
        return self.__stop.isSet()

    def wait(self):
        pass
        self.__ready.wait()

    def stop(self):
        self.__stop.set()
