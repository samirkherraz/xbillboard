#!/usr/bin/python

import os
import sys
import threading
from ThLoop import ThLoop

import time

from SystemCall import SystemCall


class Screen(ThLoop):

    def __init__(self, width, height, posx, posy):
        ThLoop.__init__(self, 2)
        self.width = width
        self.height = height
        self.posx = posx
        self.posy = posy
        self.filesFolder = ""
        self.cmd = "impressive  --nologo -t FadeOutFadeIn -x -f -a "+str(self.delay)+" -Q -g " + \
                str(self.width)+"x"+str(self.height)+"+"+str(self.posx) + \
                "+"+str(self.posy)+" "

    def loopjob(self):
        
        files = sorted([os.path.join(self.filesFolder, file)
                        for file in os.listdir(self.filesFolder)], key=os.path.getctime)
        if len(files) > 0:
            fileList = (" ").join(files)
            cmd = self.cmd+fileList
            SystemCall(cmd)
            return True
        else:
            return False

    def setFilesDir(self, dir):
        self.filesFolder = dir
