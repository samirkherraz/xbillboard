#!/usr/bin/python

__author__ = "Samir KHERRAZ"
__license__ = "GPLv3"
__maintainer__ = "Samir KHERRAZ"
__email__ = "samir.kherraz@outlook.fr"

import ConfigParser
import os
import sys
import gobject
gobject.threads_init()
import gtk
gtk.gdk.threads_init()
import gtk.gtkgl
import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)
from Screen import Screen
from Sync import Sync


class Loader(gtk.Window):

    """
    initializes the settings from the configuration file
    """

    def initConfig(self, filename):
        try:
            self.config = ConfigParser.RawConfigParser()
            self.config.read(filename)
            self.opengl_use = bool(self.config.get('General', 'OpenGL').upper(
            ) == "YES" or self.config.get('General', 'OpenGL').upper() == "TRUE")
            self.dataDir = self.config.get('General', 'DataDir')
            self.screenDelay = self.config.get('General', 'ScreenDelay')
            self.syncDelay = self.config.get('General', 'SyncDelay')
            self.activeScreen = self.config.get(
                'General', 'ActiveScreen').splitlines()
            self.layoutx = self.config.getint('General', 'LayoutX')
            self.layouty = self.config.getint('General', 'LayoutY')

            print "CONFIGURATION \t\t:\t\t" + filename

            print "OPENGL \t\t\t:\t\t" + str(self.opengl_use)

            print "SCREEN DELAY \t\t:\t\t" + str(self.screenDelay)

            print "SYNC DELAY \t\t:\t\t" + str(self.syncDelay)

            print "DATA DIR FOR SYNC \t:\t\t" + str(self.dataDir)

            print "ACTIVATED SCREENS \t:\t\t" + str(self.activeScreen)

            print "NB SCREEN PER COL \t:\t\t" + str(self.layoutx)

            print "NB SCREEN PER ROW \t:\t\t" + str(self.layouty)

        except:
            raise Exception('invalid configuration file')

    """
    test the consistency of the configuration file
    """

    def configCheck(self):
        return len(self.activeScreen) == self.layoutx*self.layouty

    """
    build the Gtk window
    """

    def prepare(self):
        vBox = gtk.VBox(spacing=0)
        for i in range(self.layouty):
            hBox = gtk.HBox(spacing=0)

            for j in range(self.layoutx):
                if self.opengl_use:
                    canvas = gtk.gtkgl.DrawingArea(self.opengl_config)
                    canvas.set_size_request(128, 128)
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
                        os.system("rm "+Dir+"*")
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
                    screen = Screen(canvas, delay, Dir)
                except:
                    screen = Screen(canvas, self.screenDelay, Dir)

                self.Screens.append(screen)
                canvas.connect("expose-event", screen.on_expose)

            vBox.add(hBox)
        self.add(vBox)
        self.show_all()
    """
    launch round Robin on screens and file synchronization
    """

    def start(self):
        for s in self.Screens:
            s.start()
        for s in self.Syncs:
            s.start()

    """
    Stop Robin Round on screens and sync
    """

    def stop(self):
        for s in self.Screens:
            s.stop()
        for s in self.Syncs:
            s.stop()

    """
    join the threads to wait for their complete stops
    """

    def join(self):
        for s in self.Screens:
            s.join()
        for s in self.Syncs:
            s.join()

    def __init__(self, config):
        gtk.Window.__init__(self)
        self.opengl_use = False
        self.opengl_config = gtk.gdkgl.Config(mode=(gtk.gdkgl.MODE_DOUBLE))

        self.set_title("XBillBoard")
        self.move(0, 0)
        self.set_default_size(self.get_screen().get_width(),
                              self.get_screen().get_height())
        # self.set_default_size(1024,
        #                      500)

        self.set_decorated(False)
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
            raise Exception('The configuration file is invalid')

    def on_key_release(self, widget, ev, data=None):
        if gtk.gdk.keyval_name(ev.keyval) == "Escape":
            gtk.main_quit()


if __name__ == '__main__':
    user_config = os.getenv("HOME")+"/.xbillboard/xbillboard.conf"
    global_config = os.path.abspath("/etc/xbillboard/xbillboard.conf")
    try:
        os.stat(user_config)
        configfile = user_config
    except:
        configfile = global_config

    window = Loader(configfile)
    gtk.gdk.threads_enter()
    gtk.main()
    gtk.gdk.threads_leave()
    window.stop()
    window.join()
