#!/usr/bin/python

import os
import sys
import threading
from threading import Thread

from SystemCall import SystemCall


class Screen(Thread):

    def __init__(self, width, height, posx, posy):
        Thread.__init__(self)
        self.width = width
        self.height = height
        self.posx = posx
        self.posy = posy
        self.filesFolder = ""
        self.delay = 2
        self._stop = threading.Event()

    def run(self):
        self.cmd = "impressive  --nologo -t FadeOutFadeIn -x -f -a "+str(self.delay)+" -Q -g " + \
                str(self.width)+"x"+str(self.height)+"+"+str(self.posx) + \
                "+"+str(self.posy)+" "
        while not self.stopped():
            files = sorted([os.path.join(self.filesFolder, file)
                            for file in os.listdir(self.filesFolder)], key=os.path.getctime)
            if len(files) > 0:
                fileList = (" ").join(files)
                cmd = self.cmd+fileList
                SystemCall(cmd, False)

    def setFilesDir(self, dir):
        self.filesFolder = dir

    def setDelay(self, delay):
        self.delay = delay

    def stopped(self):
        return self._stop.isSet()

    def stop(self):
        self._stop.set()
