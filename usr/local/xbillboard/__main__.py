#!/usr/bin/python

import ConfigParser
import os
import sys
import gobject
gobject.threads_init()

from Screen import Screen
from Sync import Sync

import gtk
import gtk.gtkgl


class Loader(gtk.Window):

    def initConfig(self, filename):
        try:
            self.config = ConfigParser.RawConfigParser()
            self.config.read(filename)
            self.dataDir = self.config.get('General', 'DataDir')
            self.screenDelay = self.config.get('General', 'ScreenDelay')
            self.syncDelay = self.config.get('General', 'SyncDelay')
            self.activeScreen = self.config.get(
                'General', 'ActiveScreen').splitlines()
            self.layoutx = self.config.getint('General', 'LayoutX')
            self.layouty = self.config.getint('General', 'LayoutY')
        except:
            raise Exception('invalid configuration file')

    def configCheck(self):
        return len(self.activeScreen) == self.layoutx*self.layouty

    def prepare(self):
        vBox = gtk.VBox(spacing=0)
        for i in range(self.layouty):
            hBox = gtk.HBox(spacing=0)
            for j in range(self.layoutx):
                if self.use_opengl:
                    canvas = gtk.gtkgl.DrawingArea()
                else:
                    canvas = gtk.DrawingArea()
                canvas.modify_bg(gtk.STATE_NORMAL, gtk.gdk.Color("#ffffff"))
                hBox.add(canvas)
                sc = self.activeScreen[self.layouty*i+j]
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

                    try:
                        fileList = self.config.get(sc, 'FileList').splitlines()
                        for f in fileList:
                            self.Syncs.append(Sync(f, Dir, self.syncDelay))
                    except:
                        pass

                try:
                    delay = self.config.get(sc, "Delay")
                    screen = Screen(self, canvas, delay, Dir)
                except:
                    screen = Screen(self, canvas, self.screenDelay, Dir)

                self.Screens.append(screen)
                canvas.connect("expose-event", screen.on_expose)

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

    def render(self, canvas, surface, document):
        if document != None:
            p_width, p_height = document.get_size()
            width = canvas.get_allocation().width
            height = canvas.get_allocation().height
            scale = min(width/p_width, height/p_height)
            if scale != 1:
                surface.scale(scale, scale)
            document.render(surface)

    def __init__(self, config, opengl):
        gtk.Window.__init__(self)
        self.use_opengl = opengl
        self.set_title("XBillBoard")
        self.move(0, 0)
        self.set_default_size(self.get_screen().get_width(),
                              self.get_screen().get_height())
        # self.set_decorated(False)
        self.connect("delete_event", gtk.main_quit)
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
        if gtk.gdk.keyval_name(ev.keyval) == "Escape":
            gtk.main_quit()


if __name__ == '__main__':
    
    try:
        configfile = sys.argv[1]
    except:
        configfile = "/etc/xbillboard.conf"
    
    try:
        opengl = bool(sys.argv[2].upper() == "YES" or sys.argv[2].upper() == "TRUE")
    except:
        opengl = False

    print "Config file : " + configfile
    print "Using opengl : " + str(opengl)
    
    window = Loader(configfile, opengl)
    gtk.main()
    window.stop()
    window.join()
