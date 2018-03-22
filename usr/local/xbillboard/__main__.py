#!/usr/bin/python

import ConfigParser
import os
import sys
from Screen import Screen
from Sync import Sync
import gi
from threading import Lock
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GObject


class Loader(Gtk.ApplicationWindow):
   
    def initConfig(self, filename):

        self.config = ConfigParser.RawConfigParser()
        self.config.read(filename)
        self.dataDir = self.config.get('General', 'DataDir')
        self.screenDelay = self.config.get('General', 'ScreenDelay')
        self.syncDelay = self.config.get('General', 'SyncDelay')
        self.activeScreen = self.config.get(
            'General', 'ActiveScreen').splitlines()
        self.layoutx = self.config.getint('General', 'LayoutX')
        self.layouty = self.config.getint('General', 'LayoutY')

    def configCheck(self):

        return len(self.activeScreen) == self.layoutx*self.layouty

    def prepare(self):
        vBox = Gtk.VBox(spacing=0)
        for i in range(self.layoutx):
            hBox = Gtk.HBox(spacing=0)
            for j in range(self.layouty):
                canvas = Gtk.DrawingArea()
                canvas.modify_bg(Gtk.StateType.NORMAL, Gdk.Color(65535,65535,65535))
                hBox.add(canvas)
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

                try:
                    delay = self.config.get(sc, "Delay")
                    screen = Screen(self,canvas,delay, Dir)
                except:
                    screen = Screen(self,canvas,self.screenDelay, Dir)

                self.Screens.append(screen)
                canvas.connect("draw", screen.on_expose)

            vBox.add(hBox)
        self.add(vBox)
        self.show_all()

    def start(self):
        for s in self.Screens:
            s.start()
        for s in self.Syncs:
            s.start()

    def stop(self):
        for s in self.Screens:
            s.stop()
        for s in self.Syncs:
            s.stop()

    def join(self):
        for s in self.Screens:
            s.join()
        for s in self.Syncs:
            s.join()
   


    def render(self,canvas, surface, document):
        if document != None:
            p_width, p_height = document.get_size()
            width = canvas.get_allocation().width
            height= canvas.get_allocation().height
            scale = min(width/p_width, height/p_height)
            if scale != 1:
                    surface.scale(scale, scale)
            document.render(surface)



    def __init__(self, config):
        Gtk.Window.__init__(self, title="XBillBoard")
        sc = Gdk.Screen.get_default()
        self.move(0, 0)
        self.set_default_size(sc.get_width(), sc.get_height())
        self.set_decorated(False)       
        self.connect("delete_event", Gtk.main_quit)
        self.connect("key-press-event", self.on_key_release)

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
            self.prepare()
            self.start()

        else:
            raise Exception('A very specific bad thing happened.')

    def on_key_release(self, widget, ev, data=None):
        if ev.keyval == Gdk.KEY_Escape:  
            Gtk.main_quit()   


if __name__ == '__main__':
    Gdk.threads_init()
    GObject.threads_init()
    window = Loader(sys.argv[1])
    Gtk.main()
    window.stop()
    window.join()

    