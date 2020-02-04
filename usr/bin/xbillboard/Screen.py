## https://lubosz.wordpress.com/2014/05/27/gstreamer-overlay-opengl-sink-example-in-python-3/
__author__ = "Samir KHERRAZ"
__license__ = "GPLv3"
__maintainer__ = "Samir KHERRAZ"
__email__ = "samir.kherraz@outlook.fr"


import gi
gi.require_version('Poppler', '0.18')
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
gi.require_version('Gst', '1.0')
gi.require_version('GstVideo', '1.0')
from gi.repository import Gdk, GdkPixbuf, GLib, Gtk, Poppler, GdkX11, GstVideo, Gst, GObject
import datetime
import time
import logging
import os
import random
import sys
import threading
from threading import Lock, Thread
import numpy as np

"""
FileType class is used to identify what is the type of the file the program is
    going to render, each type has it's own rendering method
"""


class Screen(Thread):

    class Modes:
        FRAME = 0
        HOUR = 1
        VIDEO = 3
        PDFPAGE = 4

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

    class File:
        def __init__(self, f):
            _, ext = os.path.splitext(f)
            self.name = f.split('/')[::-1][0]
            self.ext = ext.upper()
            self.path = f
            if self.ext in Screen.FileType.PDF_LIST:
                self.type = Screen.FileType.PDF
                self.method = "play_pdf"
            elif self.ext in Screen.FileType.IMAGE_LIST:
                self.type = Screen.FileType.IMAGE
                self.method = "play_image"
            elif self.ext in Screen.FileType.VIDEO_LIST:
                self.type = Screen.FileType.VIDEO
                self.method = "play_video"
            else:
                self.type = Screen.FileType.NONE
                self.method = "play_none"

    """
    Loading the logo pixel buffer once for optimization
    it is showed if errors occured
    """
    LOGO = None

    def __init__(self, canvas, delay, files_basepath, align, ratio, rotation, draw_hour=False):
        Thread.__init__(self)
        self.__current_file = {}
        self.__hidden = Gtk.DrawingArea()
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
        self.__frame = None
        self.__mode = Screen.Modes.HOUR
        self.enabled = True
        self.rotation = int(rotation)
        self.canvas = canvas
        self.files_basepath = files_basepath
        self.delay = float(delay)
        self.align = Screen.Alignement().get(align)
        self.ratio = Screen.Ratio().get(ratio)
        self.canvas.connect("draw", self.on_expose)
        self.canvas.connect_after("draw", self.on_expose_end)
        self.canvas.connect("realize", self.on_realize)
        self.player = Gst.ElementFactory.make("playbin", None)
        bus =  self.player.get_bus()
        bus.add_signal_watch()
        bus.enable_sync_message_emission()
        bus.connect("message", self.on_message)

    """
    prints all pages of the PDF one by one
    """

    def on_realize(self, widget):
        window = widget.get_window()
        window_handle = window.get_xid()
        self.player.set_window_handle(window_handle)


    def play_hour(self):
        self.__mode = Screen.Modes.HOUR
        self.query_draw(self.delay)

    def play_pdf(self, file_path):
        try:
            self.__mode = Screen.Modes.PDFPAGE
            document = Poppler.Document.new_from_file(
                "file://"+file_path, None)
            logging.info("file loaded")
            n_pages = document.get_n_pages()
            i = 0
            while i < n_pages and not self.stopped():
                self.__counter = i
                self.__frame = document.get_page(i)
                self.__translate = self.translate(self.__frame.get_size()[
                    0], self.__frame.get_size()[1])

                self.query_draw(self.delay)
                i += 1
            return True
        except Exception as e:
            logging.error(e)
            return False

    def play_image(self, file_path):
        try:
            self.__mode = Screen.Modes.FRAME
            self.__frame = GdkPixbuf.Pixbuf.new_from_file(file_path)
            self.__translate = self.translate(
                self.__frame.get_width(),
                self.__frame.get_height()
            )
            self.__frame = self.__frame.scale_simple(
                self.__translate["width"], self.__translate["height"], 0)
            self.query_draw(self.delay)
            return True
        except Exception as e:
            logging.error(e)
            return False

    def play_video(self, file_path):
        try:
            self.__mode = Screen.Modes.VIDEO
            self.player.set_property("uri", "file://" + file_path)
            with self.__critical:
                self.__on_expose_ended.clear()
                self.player.set_state(Gst.State.PLAYING)
            self.__on_expose_ended.wait()
            self.player.set_state(Gst.State.READY)
            return True
        except Exception as e:
            logging.error(e)
            return False
    """
    send an exposure signal to the Gtk window for display and wait for a delay
    """

    def on_message(self, bus, message):
        t = message.type
        if t == Gst.MessageType.EOS or t == Gst.MessageType.ERROR:
            with self.__critical:
                self.__on_expose_ended.set()
            
    def query_draw(self, delay=0.05):
        if not self.stopped():
            with self.__critical:
                self.__on_expose_ended.clear()
                GLib.idle_add(self.canvas.queue_draw)
            self.__on_expose_ended.wait()
            self.__stop.wait(delay)

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
                    ret.append(Screen.File(f))
            return ret
        except Exception as e:
            logging.error(e)

    def run(self):
        rotat = 0
        while not self.stopped():
            try:
                self.__pause.wait()
                files = self.list_dir()
                found = False
                for f in files:
                    self.__frame = None
                    if getattr(self, f.method)(f.path):
                        logging.info("file play ended")
                        found = True
                if len(files) < 1 or not found:
                    logging.info("No files")
                    getattr(self, Screen.LOGO.method)(Screen.LOGO.path)
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
            except Exception as e:
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
            self.player.set_state(Gst.State.READY)
            self.__ended.clear()
            self.__pause.set()
            self.__on_expose_ended.set()

    def stop(self):
        with self.__critical:
            self.player.set_state(Gst.State.READY)
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
        except Exception as e:
            logging.error(e)

    """
    a call the correct method depending on the file type
    """

    def draw(self, cr):
        try:
            cr.set_source_rgb(1, 1, 1)
            cr.paint()
            if self.__mode == Screen.Modes.PDFPAGE and self.__frame is not None:
                cr.translate(self.__translate["translate_x"],
                             self.__translate["translate_y"])
                cr.scale(self.__translate["scale_w"],
                         self.__translate["scale_h"])
                self.__frame.render(cr)
            if self.__mode == Screen.Modes.FRAME and self.__frame is not None:
                Gdk.cairo_set_source_pixbuf(
                    cr, self.__frame, self.__translate["translate_x"], self.__translate["translate_y"])
                cr.scale(self.__translate["scale_w"],
                         self.__translate["scale_h"])
                cr.paint()
            elif self.__mode == Screen.Modes.HOUR:
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
            else:
                pass
        except Exception as e:
            logging.error(e)

    def on_expose(self, widget, cr):
        try:
            self.__on_expose_ended.clear()
            with self.__critical:
                self.draw(cr)
        except Exception as e:
            logging.error(e)

    def on_expose_end(self, widget, event):
        try:
            with self.__critical:
                self.__on_expose_ended.set()
        except Exception as e:
            logging.error(e)
