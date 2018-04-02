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
import time
from threading import Thread
import threading


class Permute(Thread):
    def __init__(self, container, main, secondary):
        Thread.__init__(self)
        self._stop = threading.Event()
        self.active = main
        self.inactive = secondary
        self.current = 0
        self.container = container
        self.container.connect_after("switch-page", self.on_expose_end)
        self._on_expose_ended = threading.Event()
        self._on_expose_started = threading.Event()
        self._on_expose_ended.set()

    def sc_resume(self, sc):
        for s in sc:
            s.resume()

    def run(self):
        while not self.stopped():
            tmp = self.active
            self.active = self.inactive
            self.inactive = tmp
            self.current = (self.current + 1) % 2
            self.sc_resume(self.active)
            self._on_expose_started.set()
            self._on_expose_ended.clear()
            gobject.idle_add(self.container.set_current_page,
                             self.current, priority=gobject.PRIORITY_HIGH)
            self._on_expose_ended.wait()
            self.container.show_all
            self.wait()

    def wait(self):
        for s in self.active:
            s.wait()
        print "End Waiting "

    def stopped(self):
        return self._stop.isSet()

    def stop(self):
        self._stop.set()
        self._on_expose_started.clear()
        self._on_expose_ended.set()

    def on_expose_end(self, notebook, page, page_num):
        if self._on_expose_started.isSet():
            self._on_expose_started.clear()
            self._on_expose_ended.set()


class Boot(gtk.Window):

    def _prepare(self):
        self.opengl_config = gtk.gdkgl.Config(mode=(gtk.gdkgl.MODE_DOUBLE))

        self.set_title("XBillBoard")
        self.move(0, 0)
        self.set_default_size(self.get_screen().get_width(),
                              self.get_screen().get_height())
        self.set_decorated(False)
        self.connect("delete_event", gtk.main_quit)
        self.connect("key-press-event", self.on_key_release)
        self.notebook = gtk.Notebook()
        self.notebook.set_show_tabs(False)
        self.notebook.set_show_border(False)

    """
    get config parametter and rise exception if error occured
    """

    def _config_get(self, userspace, key, exception=True):
        try:
            value = self.configuration.get(userspace, key)
        except:
            if exception == True:
                raise Exception(
                    'Configuration Error : '+userspace+"::"+key+" invalid")
            else:
                pass
        return value

    """
    initializes the settings from the configuration file
    """

    def _init_config(self):
        try:
            self.configuration = ConfigParser.RawConfigParser()
            self.configuration.read(self.filename)
        except:
            raise Exception('invalid configuration file')

        self.opengl_use = bool(self._config_get('General', 'OpenGL').upper(
        ) == "YES" or self._config_get('General', 'OpenGL').upper() == "TRUE")
        self.sync_directory = self._config_get('General', 'Sync_Directory')
        self.sync_delay = self._config_get('General', 'Sync_Delay')
        self.screen_list = self._config_get(
            'General', 'Screen_List').splitlines()
        self.layout_x = int(self._config_get('General', 'LayoutX'))
        self.layout_y = int(self._config_get('General', 'LayoutY'))
        self.screen_info = self._config_get('General', 'Screen_Info')
        self.screen_delay = self._config_get('General', 'Screen_Delay')
        self.screen_ratio = self._config_get('General', 'Screen_Ratio')
        self.screen_rotation = self._config_get('General', 'Screen_Rotation')
        self.screen_align = self._config_get(
            'General', 'Screen_Alignement')

    """
    test the consistency of the configuration file
    """

    def _check_config(self):
        return len(self.screen_list) == self.layout_x*self.layout_y

    """
    build the Gtk window
    """

    def _create_canvas(self):
        if self.opengl_use:
            canvas = gtk.gtkgl.DrawingArea(self.opengl_config)
            canvas.set_size_request(128, 128)
        else:
            canvas = gtk.DrawingArea()
        canvas.modify_bg(gtk.STATE_NORMAL, gtk.gdk.Color("#ffffff"))
        return canvas

    def _prepare_dir(self, dir):
        try:
            os.stat(dir)
            os.system("rm "+dir+"*")
        except:
            os.mkdir(dir)

    def _create_vbox(self):
        return gtk.VBox(spacing=0)

    def _create_hbox(self):
        return gtk.HBox(spacing=0)

    def _build_screen(self, sc, canvas, show_hour=False):
        directory = None
        try:
            isCopy = self._config_get(sc, "CopyOf")
            directory = self.sync_directory+isCopy+"/"
        except:
            directory = self.sync_directory+sc+"/"
            self._prepare_dir(directory)
            try:
                fileList = self._config_get(
                    sc, 'FileList').splitlines()
                for f in fileList:
                    self.sync_services.append(
                        Sync(f, directory, self.sync_delay))
            except:
                pass

        try:
            align = self._config_get(sc, "Alignement")
        except:
            align = self.screen_align

        try:
            ratio = self._config_get(sc, "Ratio")
        except:
            ratio = self.screen_ratio

        try:
            delay = self.configuration.get(sc, "Delay")
        except:
            delay = self.screen_delay

        try:
            rotat = self._config_get(sc, "Rotation")
        except:
            rotat = self.screen_rotation

        screen = Screen(canvas, delay, directory,
                        align, ratio, rotat, show_hour)
        return screen

    def _build(self):
        vBox = self._create_vbox()

        for i in range(self.layout_y):
            hBox = self._create_hbox()
            for j in range(self.layout_x):
                sc = self.screen_list[self.layout_y*i+j]
                canvas = self._create_canvas()
                screen = self._build_screen(sc, canvas)
                self.screen_services.append(screen)
                hBox.add(canvas)
            vBox.add(hBox)
        self.notebook.append_page(vBox)
        self.add(self.notebook)

        canvas = self._create_canvas()
        screen = self._build_screen(self.screen_info, canvas, True)
        self.screen_info_service = screen
        self.notebook.append_page(canvas)
        self.permutation = Permute(self.notebook, self.screen_services, [
                                   self.screen_info_service])
    """
    launch round Robin on screens and file synchronization
    """

    def start(self):

        for s in self.sync_services:
            s.start()

        for s in self.screen_services:
            s.pause()
            s.start()

        self.screen_info_service.pause()
        self.screen_info_service.start()

        self.permutation.start()

    """
    Stop Robin Round on screens and sync
    """

    def stop(self):

        for s in self.screen_services:
            s.stop()
            s.join()
        print "STOP SCREENS"

        self.screen_info_service.stop()
        self.screen_info_service.join()

        print "STOP MAIN SCREEN"

        self.permutation.stop()
        self.permutation.join()
        print "STOP PERMUTATION"

        for s in self.sync_services:
            s.stop()
            s.join()
        print "STOP SYNCS"

    """
    join the threads to wait for their complete stops
    """

    def print_config(self):

        print "CONFIGURATION \t\t:\t\t" + self.filename

        print "OPENGL \t\t\t:\t\t" + str(self.opengl_use)

        print "SCREEN DELAY \t\t:\t\t" + str(self.screen_delay)

        print "SCREEN RATIO \t\t:\t\t" + str(self.screen_ratio)

        print "SCREEN ALIGNEMENT \t\t:\t\t" + str(self.screen_align)

        print "SYNC DELAY \t\t:\t\t" + str(self.sync_delay)

        print "DATA DIR FOR SYNC \t:\t\t" + str(self.sync_directory)

        print "ACTIVATED SCREENS \t:\t\t" + str(self.screen_list)

        print "NB SCREEN PER COL \t:\t\t" + str(self.layout_x)

        print "NB SCREEN PER ROW \t:\t\t" + str(self.layout_y)

    def __init__(self, config):
        gtk.Window.__init__(self)
        self.opengl_config = None
        self.opengl_use = False
        self.sync_services = []
        self.sync_delay = []
        self.screen_services = []
        self.screen_list = None
        self.screen_delay = None
        self.screen_ratio = None
        self.screen_align = None
        self.configuration = None
        self.sync_directory = None
        self.layout_x = None
        self.layout_y = None
        self.filename = config
        self.notebook = None
        self._init_config()

        if self._check_config():
            self.print_config()
            self._prepare()
            self._build()
            self.show_all()
            self.start()

        else:
            raise Exception('The configuration file is invalid')

    def on_key_release(self, widget, ev, data=None):
        if gtk.gdk.keyval_name(ev.keyval) == "Escape":
            gtk.main_quit()


if __name__ == '__main__':
    userConfig = os.getenv("HOME")+"/.xbillboard/xbillboard.conf"
    globalConfig = os.path.abspath("/etc/xbillboard/xbillboard.conf")
    try:
        os.stat(userConfig)
        configFile = userConfig
    except:
        configFile = globalConfig

    mainBoot = Boot(configFile)
    gtk.gdk.threads_enter()
    gtk.main()
    gtk.gdk.threads_leave()
    mainBoot.stop()
