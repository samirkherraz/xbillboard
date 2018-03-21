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
        
    def loopjob(self):
        path = os.path.dirname(os.path.realpath(__file__))+"/"
        files = sorted([os.path.join(self.filesFolder, file)
                        for file in os.listdir(self.filesFolder)], key=os.path.getctime)
        if len(files) > 0:
            for f in files:
                SystemCall("python "+path+"GtkPdfViewer.py "+str(self.width)+" "+str(self.height)+" "+str(self.posx)+" "+str(self.posy)+" "+str(self.delay)+" "+f)
            return True
        else:
            return False

    def setFilesDir(self, dir):
        self.filesFolder = dir
