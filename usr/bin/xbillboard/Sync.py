
__author__ = "Samir KHERRAZ"
__license__ = "GPLv3"
__maintainer__ = "Samir KHERRAZ"
__email__ = "samir.kherraz@outlook.fr"

import os
import sys
from threading import Thread
import threading
import hashlib

class Sync(Thread):
    def __init__(self, url, localdir, delay):
        Thread.__init__(self)
        self.__stop = threading.Event()
        self.name = hashlib.sha256(url.split("/")[-1].encode()).hexdigest()
        self.ext = url.split(".")[-1]
        self.delay = float(delay)
        self.url = url
        self.localdir = localdir
        self.cmd = "wget -q -N '"+self.url+"' -O "+self.localdir+"/"+self.name+"."+self.ext

    def run(self):
        while not self.stopped():
            try:
                open(self.localdir+self.name+"."+self.ext+".sync_lock", 'w').close()
                os.system(self.cmd)
                os.remove(self.localdir+self.name+"."+self.ext+".sync_lock")
                self.__stop.wait(self.delay)
            except:
                print("sync error")

    def stopped(self):
        return self.__stop.isSet()

    def stop(self):
        self.__stop.set()
