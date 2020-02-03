
__author__ = "Samir KHERRAZ"
__license__ = "GPLv3"
__maintainer__ = "Samir KHERRAZ"
__email__ = "samir.kherraz@outlook.fr"

from Cache import Cache
import cv2
from gi.repository import Gdk, GdkPixbuf, GLib, Gtk, Poppler
import datetime
import time
import logging
import os
import random
import sys
import threading
from threading import Lock, Thread
import numpy as np
from gi.repository import Gtk, Gst, GdkX11, GstVideo
Gst.init(None)
"""
FileType class is used to identify what is the type of the file the program is
    going to render, each type has it's own rendering method
"""


class Screen(Thread):

    class FileType:
        PDF = 1
        IMAGE = 2
        GIF = 3
        VIDEO = 4
        HOUR = 5
        NONE = 0
        PDF_LIST = [".PDF"]
        IMAGE_LIST = [".JPG", ".JPEG", ".PNG", ".SVG"]
        GIF_LIST = []
        VIDEO_LIST = [".GIF", ".MP4"]

    class Ratio:
        STRETCH = 1
        FIT = 2

        def get(self, str):
            str = str.upper()
            if str == "STRETCH":
                return self.STRETCH
            else:
                return self.FIT

    class Alignement:
        LEFT = 1
        RIGHT = 2
        TOP = 3
        DOWN = 4
        CENTER = 5

        def get(self, str):
            r = {}
            str = str.upper().split("::")
            if str[1] == "LEFT":
                r["Horizental"] = self.LEFT
            elif str[1] == "RIGHT":
                r["Horizental"] = self.RIGHT
            else:
                r["Horizental"] = self.CENTER
            if str[0] == "TOP":
                r["Vertical"] = self.TOP
            elif str[0] == "DOWN":
                r["Vertical"] = self.DOWN
            else:
                r["Vertical"] = self.CENTER

            return r

    """
    Loading the logo pixel buffer once for optimization
    it is showed if errors occured
    """
    LOGO = "/usr/share/backgrounds/xbillboard.svg"

    def __init__(self, canvas, delay, files_basepath, align, ratio, rotation, draw_hour=False):
        Thread.__init__(self)
        self.__current_file = {}
        self.name = files_basepath.split('/')[::-1][1]
        self.__critical = Lock()
        self.__pause = threading.Event()
        self.__fileready = threading.Event()
        self.__videoplay = threading.Event()
        self.__ended = threading.Event()
        self.__stop = threading.Event()
        self.__on_expose_ended = threading.Event()
        self.__on_expose_started = threading.Event()
        self.__drawing_job = threading.Event()
        self.__ended.clear()
        self.__on_expose_ended.set()
        self.__drawing_hour = draw_hour
        self.__counter = 0
        self.__current_doc = None
        self.enabled = True
        self.rotation = int(rotation)
        self.canvas = canvas
        self.files_basepath = files_basepath
        self.delay = float(delay)
        self.align = Screen.Alignement().get(align)
        self.ratio = Screen.Ratio().get(ratio)
        self.canvas.connect("draw", self.on_expose)
        self.canvas.connect_after("draw", self.on_expose_end)
        self.player = Gst.ElementFactory.make("playbin", "player")
        bus = self.player.get_bus()
        bus.add_signal_watch()
        bus.enable_sync_message_emission()
        bus.connect("sync-message::element", self.on_sync_message)
        bus.connect("message", self.on_message)

    """
    loads the file into memory and defines the rendering procedure according to its type.
    """

    def play_file(self, f):
        try:
            self.__current_file = f
            logging.info(self.__current_file)
            if self.__current_file["ext"] in Screen.FileType.PDF_LIST:
                self.__current_file["type"] = Screen.FileType.PDF
                return self.play_pdf(self.delay, f["path"])
            elif self.__current_file["ext"] in Screen.FileType.IMAGE_LIST:
                self.__current_file["type"] = Screen.FileType.IMAGE
                return self.play_image(self.delay, f["path"])
            elif self.__current_file["ext"] in Screen.FileType.VIDEO_LIST:
                self.__current_file["type"] = Screen.FileType.VIDEO
                return self.play_video(f["path"])
            else:
                logging.warning(
                    self.__current_file["name"]+" unsuported file type")
                return False
            logging.info(self.__current_file)
            return True
        except ValueError as e:
            logging.error(e)
            return False
    """
    prints all pages of the PDF one by one
    """

    def play_pdf(self, delay=1, file=None):
        if file is None:
            file = self.__current_file["path"]
        try:
            document = Poppler.Document.new_from_file(
                "file://"+file, None)
            logging.info("file loaded")
            n_pages = document.get_n_pages()
            i = 0
            while i < n_pages and not self.stopped():
                self.__counter = i
                logging.info("page "+str(i)+" saved to cache")
                self.__current_doc = document.get_page(i)
                self.__translate = self.translate(self.__current_doc.get_size()[
                    0], self.__current_doc.get_size()[1])

                self.query_draw(delay)
                i += 1
            return True
        except ValueError as e:
            logging.error(e)
            return False

    def play_image(self, delay=1, file=""):
        self.__current_doc = GdkPixbuf.Pixbuf.new_from_file(file)
        self.__translate = self.translate(
                    self.__current_doc.get_width(), 
                    self.__current_doc.get_height()
                    )
        self.__current_doc = self.__current_doc.scale_simple(
                self.__translate["width"], self.__translate["height"], 0)
        
        self.query_draw(delay)

    def play_video(self, file=""):
        try:
            self.player.set_property("uri", "file://" + file)
            self.__videoplay.clear()
            self.player.set_state(Gst.State.PLAYING)
            self.__videoplay.wait()
        except ValueError as e:
            logging.error(e)
            return False
    """
    send an exposure signal to the Gtk window for display and wait for a delay
    """

    def on_message(self, bus, message):
        t = message.type
        if t == Gst.MessageType.EOS:
            self.__videoplay.set()
        elif t == Gst.MessageType.ERROR:
            self.__videoplay.set()

    def on_sync_message(self, bus, message):
        if message.get_structure().get_name() == 'prepare-window-handle':
            self.__videoplay.clear()
            imagesink = message.src
            imagesink.set_property("force-aspect-ratio", True)
            imagesink.set_window_handle(self.canvas.get_window().get_xid())

    def query_draw(self, delay=0.05):
        if not self.stopped():
            with self.__critical:
                self.__on_expose_ended.clear()
                GLib.idle_add(self.canvas.queue_draw)
            self.__on_expose_ended.wait()
            self.__stop.wait(delay)

    """
    prints the image on the screen
    """

    def play_hour(self):
        self.__current_file = {
            "name": "___HOUR___",
            "ext": None,
            "path": None,
            "type": Screen.FileType.HOUR
        }
        self.query_draw(self.delay)

    """
    prints the logo on the screen
    """

    def play_logo(self):
        _, ext = os.path.splitext(Screen.LOGO)
        self.__current_file = {
            "name": Screen.LOGO.split('/')[::-1][0],
            "ext": ext.upper(),
            "path": Screen.LOGO,
            "type": Screen.FileType.IMAGE
        }

        self.play_image(self.delay, Screen.LOGO)
    """
    the main of the thread
    """

    def list_dir(self):
        try:
            ret = []
            files = [os.path.join(self.files_basepath, file)
                     for file in os.listdir(self.files_basepath)]
            for f in files:
                if str(f + ".sync_lock") not in files and "sync_lock" not in f:
                    _, ext = os.path.splitext(f)
                    ret.append({
                        "name": f.split('/')[::-1][0],
                        "ext": ext.upper(),
                        "path": f
                    })
            return ret
        except ValueError as e:
            logging.error(e)

    def run(self):
        rotat = 0
        while not self.stopped():
            try:
                self.__pause.wait()
                files = self.list_dir()
                found = False
                for f in files:
                    if self.play_file(f):
                        logging.info("file play ended")
                        found = True
                if len(files) < 1 or not found:
                    logging.info("No files")
                    self.play_logo()
                if self.__drawing_hour:
                    logging.info("Need to draw hour")
                    self.play_hour()

                if rotat < self.rotation:
                    rotat += 1
                else:
                    with self.__critical:
                        self.__ended.set()
                        self.__pause.clear()
                    rotat = 0
            except ValueError as e:
                logging.error(e)

    """
    stop Robin round and leave the thread
    """

    def wait(self):
        self.__ended.wait()
        with self.__critical:
            self.__ended.clear()

    def reset(self):
        with self.__critical:
            self.__ended.clear()
            self.__pause.set()
            self.__on_expose_ended.set()

    def stop(self):
        with self.__critical:
            self.__stop.set()
            self.__ended.set()
            self.__on_expose_ended.set()
            self.__pause.set()

    """
    test if a stop is requested
    """

    def stopped(self):
        return self.__stop.isSet()

    """
    Allows you to calculate the size of the document to be printed according to the size of the screen
    """

    def translate(self, p_width, p_height):
        try:
            ret = {}
            w = self.canvas.get_allocated_width()
            h = self.canvas.get_allocated_height()
            scale_w = float(w)/float(p_width)
            scale_h = float(h)/float(p_height)

            if self.ratio == Screen.Ratio.STRETCH:
                ret["scale_w"] = scale_w
                ret["scale_h"] = scale_h
            else:
                ret["scale_w"] = (min(scale_h, scale_w))
                ret["scale_h"] = (min(scale_h, scale_w))

            ret["width"] = int(p_width*ret["scale_w"])
            ret["height"] = int(p_height*ret["scale_h"])

            if self.align["Horizental"] == Screen.Alignement.RIGHT:
                ret["translate_x"] = int(w-ret["width"])
            elif self.align["Horizental"] == Screen.Alignement.LEFT:
                ret["translate_x"] = 0
            else:
                ret["translate_x"] = int(w/2-ret["width"]/2)
            if self.align["Vertical"] == Screen.Alignement.TOP:
                ret["translate_y"] = 0
            elif self.align["Vertical"] == Screen.Alignement.DOWN:
                ret["translate_y"] = int(h-ret["height"])
            else:
                ret["translate_y"] = int(h/2-ret["height"]/2)

            return ret
        except ValueError as e:
            logging.error(e)

    """
    How to print(an image on the screen
    """

    def draw_frame(self, cr):
        logging.info("asked to drawing frame")
        try:
            if self.__current_doc is not None:
                Gdk.cairo_set_source_pixbuf(
                    cr, self.__current_doc, 0, 0)
                cr.translate(self.__translate["translate_x"],
                             self.__translate["translate_y"])
                cr.paint()
        except ValueError as e:
            logging.error(e)

    def draw_hour(self, cr):
        try:
            now = datetime.datetime.now()
            time = now.strftime("%H:%M")

            cr.set_font_size(self.canvas.get_allocated_height()/5)
            (_, _, width, height, _, _) = cr.text_extents(time)

            cr.rectangle(self.canvas.get_allocated_width()/2 - width,
                         self.canvas.get_allocated_height()/2 - height, 2*width, 2*height)
            cr.set_source_rgb(0.2, 0.2, 0.2)
            cr.fill()
            cr.move_to(self.canvas.get_allocated_width()/2 - width /
                       2, self.canvas.get_allocated_height()/2 + height/2)
            cr.set_source_rgb(1, 1, 1)
            cr.show_text(time)
        except ValueError as e:
            logging.error(e)
    """
    PDF screen printing procedure on screen
    """

    def draw_pdf(self, cr):
        try:
            if self.__current_doc is not None:
                cr.translate(self.__translate["translate_x"],
                             self.__translate["translate_y"])
                cr.scale(self.__translate["scale_w"],
                         self.__translate["scale_h"])
                self.__current_doc.render(cr)
        except ValueError as e:
            logging.error(e)
    """
    a call the correct method depending on the file type
    """

    def draw(self, cr):
        try:
            cr.set_source_rgb(1, 1, 1)
            cr.paint()
            logging.info("asked to draw")
            if "type" in self.__current_file:
                if self.__current_file["type"] == Screen.FileType.HOUR:
                    self.draw_hour(cr)
                elif self.__current_file["type"] == Screen.FileType.PDF:
                    self.draw_pdf(cr)
                elif self.__current_file["type"] == Screen.FileType.IMAGE:
                    self.draw_frame(cr)
                elif self.__current_file["type"] == Screen.FileType.VIDEO:
                    pass
                    # self.draw_frame(cr)
                else:
                    logging.error("Unsupported file type " +
                                  str(self.__current_file["type"]))
        except ValueError as e:
            logging.error(e)

    def on_expose(self, widget, cr):
        if self.enabled:
            try:
                self.__on_expose_ended.clear()
                with self.__critical:
                    self.draw(cr)
            except ValueError as e:
                logging.error(e)

    def on_expose_end(self, widget, event):
        try:
            with self.__critical:
                self.__on_expose_ended.set()
        except ValueError as e:
            logging.error(e)
