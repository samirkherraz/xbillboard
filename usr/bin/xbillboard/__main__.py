#!/usr/bin/python2

__author__ = "Samir KHERRAZ"
__license__ = "GPLv3"
__maintainer__ = "Samir KHERRAZ"
__email__ = "samir.kherraz@outlook.fr"


import threading
from threading import Thread, Lock
import time
from Sync import Sync
from Screen import Screen
from Cache import Cache
import signal
from gi.repository import Gtk, Gdk, GObject
import configparser
import os
import sys
import logging
LOGFORMAT = "%(asctime)s [%(levelname)s] %(threadName)s::%(module)s \n %(message)s"
logging.basicConfig(
    stream=sys.stdout, level=logging.DEBUG, format=LOGFORMAT)
Gdk.threads_init()
signal.signal(signal.SIGINT, signal.SIG_DFL)


class Permute(Thread):
    def __init__(self, container, main, secondary=[]):
        Thread.__init__(self)
        self._critical = Lock()
        self._stop = threading.Event()
        self.active = main
        self.inactive = secondary
        self.permutable = len(secondary) > 0
        self.current = 0
        self.container = container
        self.container.connect_after("switch-page", self.on_expose_end)
        self._on_expose_ended = threading.Event()
        self._on_expose_started = threading.Event()
        self._on_expose_ended.set()

    def permute(self):
        tmp = self.active
        self.active = self.inactive
        self.inactive = tmp
        self.current = (self.current + 1) % 2

    def reset(self):
        for s in self.active:
            s.reset()

    def run(self):
        while not self.stopped():
            if self.permutable:
                self.permute()
                with self._critical:
                    self._on_expose_started.set()
                    self._on_expose_ended.clear()
                GObject.idle_add(self.container.show_all,
                                 priority=GObject.PRIORITY_HIGH)
                GObject.idle_add(self.container.set_current_page,
                                 self.current, priority=GObject.PRIORITY_LOW)
                self._on_expose_ended.wait()

            self.reset()
            self.wait()

    def wait(self):
        for s in self.active:
            s.wait()

    def stopped(self):
        return self._stop.isSet()

    def stop(self):
        with self._critical:
            self._stop.set()
            self._on_expose_started.clear()
            self._on_expose_ended.set()

    def on_expose_end(self, notebook, page, page_num):
        if self._on_expose_started.isSet():
            with self._critical:
                self._on_expose_started.clear()
                self._on_expose_ended.set()


class Boot(Gtk.Window):

    def _prepare(self):
        self.set_title("XBillBoard")
        self.move(0, 0)
        self.set_default_size(self.get_screen().get_width(),
                              self.get_screen().get_height())
        self.set_decorated(False)
        self.connect("delete_event", Gtk.main_quit)
        self.connect("key-press-event", self.on_key_release)
        self.notebook = Gtk.Notebook()
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
            self.configuration = configparser.RawConfigParser()
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
        self.screen_info = self._config_get('General', 'Screen_Main')
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
        canvas = Gtk.DrawingArea()
        canvas.modify_bg(Gtk.StateType.NORMAL, Gdk.Color(0, 0, 0))
        return canvas

    def _prepare_dir(self, dir):
        try:
            os.stat(dir)
            os.system("rm "+dir+"*")
        except:
            os.mkdir(dir)

    def _create_vbox(self):
        return Gtk.VBox(spacing=0)

    def _create_hbox(self):
        return Gtk.HBox(spacing=0)

    def _build_screen(self,  sc, canvas, show_hour=False):
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
                    if f not in self.files_list:
                        self.files_list.append(f)
                        self.sync_services.append(
                            Sync(self.caches, f, directory, self.sync_delay))
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

        c = Cache()
        self.caches.append(c)
        screen = Screen(c, canvas, delay, directory,
                        align, ratio, rotat, show_hour)
        return screen

    def _build(self):
        vBox = self._create_vbox()

        for i in range(self.layout_y):
            hBox = self._create_hbox()
            for j in range(self.layout_x):
                sc = self.screen_list[self.layout_x*i+j]
                canvas = self._create_canvas()
                screen = self._build_screen(sc, canvas)
                self.screen_services.append(screen)
                hBox.add(canvas)
            vBox.add(hBox)
        self.notebook.append_page(vBox)
        self.add(self.notebook)

        if self.screen_info != "None":
            canvas = self._create_canvas()
            screen = self._build_screen(self.screen_info, canvas, True)
            self.screen_info_service = screen
            self.notebook.append_page(canvas)
            self.permutation = Permute(self.notebook, self.screen_services, [
                self.screen_info_service])
        else:
            self.permutation = Permute(self.notebook, self.screen_services)
    """
    launch round Robin on screens and file synchronization
    """

    def start(self):

        for s in self.sync_services:
            s.start()

        for s in self.screen_services:
            s.start()

        if self.screen_info != "None":
            self.screen_info_service.start()

        self.permutation.start()

    """
    Stop Robin Round on screens and sync
    """

    def stop(self):

        for s in self.screen_services:
            s.stop()
            s.join()
        print("STOP SCREENS")
        if self.screen_info != "None":
            self.screen_info_service.stop()
            self.screen_info_service.join()

        print("STOP MAIN SCREEN")

        self.permutation.stop()
        self.permutation.join()
        print("STOP PERMUTATION")

        for s in self.sync_services:
            s.stop()
            s.join()
        print("STOP SYNCS")

    """
    join the threads to wait for their complete stops
    """

    def print_config(self):

        print("CONFIGURATION \t\t:\t\t" + self.filename)

        print("OPENGL \t\t\t:\t\t" + str(self.opengl_use))

        print("SCREEN DELAY \t\t:\t\t" + str(self.screen_delay))

        print("SCREEN RATIO \t\t:\t\t" + str(self.screen_ratio))

        print("SCREEN ALIGNEMENT \t\t:\t\t" + str(self.screen_align))

        print("SYNC DELAY \t\t:\t\t" + str(self.sync_delay))

        print("DATA DIR FOR SYNC \t:\t\t" + str(self.sync_directory))

        print("ACTIVATED SCREENS \t:\t\t" + str(self.screen_list))

        print("NB SCREEN PER COL \t:\t\t" + str(self.layout_x))

        print("NB SCREEN PER ROW \t:\t\t" + str(self.layout_y))

    def __init__(self, config):
        Gtk.Window.__init__(self)
        self.caches = []
        self.opengl_config = None
        self.opengl_use = False
        self.sync_services = []
        self.sync_delay = []
        self.screen_services = []
        self.screen_list = None
        self.files_list = []
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
        if Gdk.keyval_name(ev.keyval) == "Escape":
            Gtk.main_quit()


if __name__ == '__main__':
    userConfig = os.getenv("HOME")+"/.xbillboard/xbillboard.conf"
    globalConfig = os.path.abspath("/etc/xbillboard/xbillboard.conf")
    try:
        os.stat(userConfig)
        configFile = userConfig
    except:
        configFile = globalConfig

    mainBoot = Boot(configFile)

    Gtk.main()

    mainBoot.stop()
