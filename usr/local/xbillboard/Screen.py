#!/usr/bin/python
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gdk
import os
import sys
from ThLoop import ThLoop
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
                SystemCall("python "+path+"GtkPdfViewer.py "+str(self.width)+" "+str(
                    self.height)+" "+str(self.posx)+" "+str(self.posy)+" "+str(self.delay)+" "+f)
            return True
        else:
            return False

    def setFilesDir(self, dir):
        self.filesFolder = dir


class ScreenManager():
    def __init__(self):
        sc = Gdk.Screen.get_default()
        self.screenWidth = sc.get_width()
        self.screenHeight = sc.get_height()

    def getLayout(self, x, y):
        r = []
        W = self.screenWidth/x
        H = self.screenHeight/y
        xi = 0
        while xi < x:
            yi = 0
            while yi < y:
                r.append(Screen(W, H, xi*W, yi*H))
                yi += 1
            xi += 1
        return r
