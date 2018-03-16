#!/usr/bin/python

import ConfigParser
import os
import sys
from time import sleep
from ScreenManager import ScreenManager
from Sync import Sync
from GtkKeyHandler import GtkKeyHandler, Gtk
from SystemCall import SystemCall

class Loader():

    def initConfig(self, filename):

        self.config = ConfigParser.RawConfigParser()
        self.config.read(filename)
        self.dataDir = self.config.get('General', 'DataDir')
        self.screenDelay = self.config.get('General', 'ScreenDelay')
        self.syncDelay = self.config.get('General', 'SyncDelay')
        self.activeScreen = self.config.get('General', 'ActiveScreen').splitlines()
        self.layoutx = self.config.getint('General', 'LayoutX')
        self.layouty = self.config.getint('General', 'LayoutY')

    def configCheck(self):

        return len(self.activeScreen) == self.layoutx*self.layouty

    def initScreens(self):
        self.Screens = ScreenManager().getLayout(self.layoutx, self.layouty)

    def prepare(self):
        for i in range(self.layoutx):
            for j in range(self.layouty):
                sc = self.activeScreen[self.layoutx*i+j]
                isCopy = None
                Dir = None
                try:
                    isCopy = self.config.get(sc, "CopyOf")
                    Dir = self.dataDir+isCopy+"/"
                except:
                    isCopy = None
                    Dir = self.dataDir+sc+"/"
                    try:
                        os.stat(Dir)
                    except:
                        os.mkdir(Dir)
                    fileList = self.config.get(sc, 'FileList').splitlines()
                    for f in fileList:
                        self.Syncs.append(Sync(f, Dir, self.syncDelay))

                self.Screens[self.layoutx*i+j].setFilesDir(Dir)

                try:
                    delay = self.config.get(sc, "Delay")
                    self.Screens[layoutx*i+j].setDelay(delay)
                except:
                    self.Screens[self.layoutx*i+j].setDelay(self.screenDelay)

    def start(self):
        for s in self.Syncs:
            s.cleanUp()
            s.start()

        for s in self.Screens:
            s.start()

    def stop(self):
        os.killpg(os.getpid(), 9)
    



    def __init__(self,config):
        
        self.Syncs = []
        self.Screens = []
        self.config = None
        self.dataDir = None
        self.screenDelay = None
        self.syncDelay = None
        self.activeScreen = None
        self.layoutx = None
        self.layouty = None
        self.initConfig(config)

        if self.configCheck():
            self.initScreens()
            self.prepare()
        else:
            raise Exception('A very specific bad thing happened.')


if __name__ == '__main__':
    try:
        l = Loader(sys.argv[1])
        l.start()
        window = GtkKeyHandler()
        window.show_all()
        Gtk.main()
        l.stop()

    except Exception as e:
        print e
