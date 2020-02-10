#  https://lubosz.wordpress.com/2014/05/27/gstreamer-overlay-opengl-sink-example-in-python-3/
__author__ = "Samir KHERRAZ"
__license__ = "GPLv3"
__maintainer__ = "Samir KHERRAZ"
__email__ = "samir.kherraz@outlook.fr"


from gi.repository import Gdk, GdkPixbuf, GLib, Gtk, Poppler, GdkX11, GObject
import vlc
import numpy as np
from threading import Lock, Thread
import threading
import sys
import random
import os
import logging
import time
import datetime
import gi
gi.require_version('Poppler', '0.18')
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
"""
FileType class is used to identify what is the type of the file the program is
    going to render, each type has it's own rendering method
"""


class Screen(Thread, Gtk.Window):

    class LockEventValue():
        def __init__(self):
            self.event = threading.Event()
            self.lock = threading.Lock()
            self.value = None

        def wait(self):
            self.event.wait()

        def timeout(self, delay=0):
            self.event.wait(delay)

        def set(self):
            with self.lock:
                self.event.set()

        def isSet(self):
            with self.lock:
                return self.event.isSet()

        def clear(self):
            with self.lock:
                self.event.clear()

        def set_value(self, value):
            with self.lock:
                self.value = value

        def get_value(self):
            with self.lock:
                return self.value

        def acquire(self):
            self.lock.acquire()

        def release(self):
            self.lock.release()

    class Modes:
        FRAME = 0
        HOUR = 1
        VIDEO = 3
        PDFPAGE = 4

    class FileType:
        PDF = 1
        IMAGE = 2
        VIDEO = 4
        HOUR = 5
        NONE = 0
        PDF_LIST = [".PDF"]
        IMAGE_LIST = [".JPG", ".JPEG", ".PNG", ".SVG"]
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
    VLC = None
    VLC_LOCK = None

    def __init__(self, canvas, delay, files_basepath, align, ratio, rotation, draw_hour=False):
        Gtk.Window.__init__(self)
        Thread.__init__(self)
        self.player_lock = threading.Lock()
        self.mode = Screen.LockEventValue()
        self.mode.set_value(Screen.Modes.HOUR)
        self.loop_pause = Screen.LockEventValue()
        self.loop_end = Screen.LockEventValue()
        self.loop_stop = Screen.LockEventValue()
        self.loop_end.clear()

        self.draw_end = Screen.LockEventValue()
        self.draw_end.set()

        self.player = Screen.LockEventValue()
        self.player_video_end = Screen.LockEventValue()
        self.player_video_end.set()

        self.draw_hour = draw_hour

        self.pdf_page_number = 0
        self.frame = Screen.LockEventValue()
        self.rotation = int(rotation)
        self.canvas = canvas
        self.files_basepath = files_basepath
        self.delay = float(delay)
        self.align = Screen.Alignement().get(align)
        self.ratio = Screen.Ratio().get(ratio)
        self.canvas.connect("draw", self.on_expose)
        self.canvas.connect_after("draw", self.on_expose_end)
        self.create_player()
        self.canvas.connect("realize", self.realize)

    def realize(self, o):
        self.player.get_value().set_xwindow(self.canvas.get_window().get_xid())

    """
    prints all pages of the PDF one by one
    """

    def create_player(self):
        self.player.set_value(Screen.VLC.media_player_new())
        self.player_events = self.player.get_value().event_manager()
        self.player_events.event_attach(
            vlc.EventType.MediaPlayerEndReached, self.play_video_ended)
        self.player.get_value().audio_set_mute(True)

    def destroy_player(self):
        if self.player.get_value() is not None:
            self.player.get_value().stop()
            self.player.get_value().release()
            self.player.set_value(None)
            self.player_video_end.set()

    def play_video_ended(self, o):
        self.player_video_end.set()

    def play_hour(self):
        self.mode.set_value(Screen.Modes.HOUR)
        self.query_draw()
        self.query_wait()

    def play_pdf(self, file_path):
        try:
            self.mode.set_value(Screen.Modes.PDFPAGE)
            document = Poppler.Document.new_from_file(
                "file://"+file_path, None)
            logging.info("file loaded")
            n_pages = document.get_n_pages()
            i = 0
            while i < n_pages and not self.stopped():
                self.pdf_page_number = i
                self.frame.set_value(document.get_page(i))
                self.frame_size_scale = self.translate(self.frame.get_value().get_size()[
                    0], self.frame.get_value().get_size()[1])

                self.query_draw()
                self.query_wait()
                i += 1
            return True
        except Exception as e:
            logging.error(e)
            return False

    def play_image(self, file_path):
        try:
            self.mode.set_value(Screen.Modes.FRAME)
            self.frame.set_value(GdkPixbuf.Pixbuf.new_from_file(file_path))
            self.frame_size_scale = self.translate(
                self.frame.get_value().get_width(),
                self.frame.get_value().get_height()
            )
            self.frame.set_value(self.frame.get_value().scale_simple(
                self.frame_size_scale["width"], self.frame_size_scale["height"], 0))
            self.query_draw()
            self.query_wait()
            return True
        except Exception as e:
            logging.error(e)
            return False

    def play_video(self, file_path):
        try:
            self.mode.set_value(Screen.Modes.VIDEO)
            self.query_draw()
            with self.canvas.freeze_notify():
                self.player_video_end.clear()
                self.player.get_value().set_mrl(file_path)
                self.player.get_value().play()
                self.player_video_end.wait()
                self.player.get_value().stop()
            return True

        except Exception as e:
            logging.error(e)
            return False
    """
    send an exposure signal to the Gtk window for display and wait for a delay
    """

    def query_wait(self):
        if not self.stopped():
            self.loop_stop.timeout(self.delay)

    def query_draw(self):
        if not self.stopped():
            self.draw_end.clear()
            GLib.idle_add(self.canvas.queue_draw)
            self.draw_end.wait()

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
                self.loop_pause.wait()
                files = self.list_dir()
                found = False
                for f in files:
                    self.frame.set_value(None)
                    if getattr(self, f.method)(f.path):
                        logging.info("file play ended")
                        found = True
                if len(files) < 1 or not found:
                    logging.info("No files")
                    getattr(self, Screen.LOGO.method)(Screen.LOGO.path)
                if self.draw_hour:
                    logging.info("Need to draw hour")
                    self.play_hour()
                if rotat < self.rotation:
                    rotat += 1
                else:
                    self.loop_end.set()
                    self.loop_pause.clear()
                    rotat = 0
            except Exception as e:
                logging.error(e)
        self.destroy_player()

    """
    stop Robin round and leave the thread
    """

    def wait(self):
        self.loop_end.wait()
        self.loop_end.clear()

    def reset(self):
        self.player_video_end.set()
        self.loop_end.clear()
        self.loop_pause.set()
        self.draw_end.set()

    def stop(self):
        self.player_video_end.set()
        self.loop_stop.set()
        self.loop_end.set()
        self.draw_end.set()
        self.loop_pause.set()

    """
    test if a stop is requested
    """

    def stopped(self):
        return self.loop_stop.isSet()

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
            if not self.draw_end.isSet():
                if self.mode.get_value() == Screen.Modes.PDFPAGE and self.frame.get_value() is not None:
                    cr.set_source_rgb(1, 1, 1)
                    cr.paint()
                    cr.translate(self.frame_size_scale["translate_x"],
                                 self.frame_size_scale["translate_y"])
                    cr.scale(self.frame_size_scale["scale_w"],
                             self.frame_size_scale["scale_h"])
                    self.frame.get_value().render(cr)
                    return True
                if self.mode.get_value() == Screen.Modes.FRAME and self.frame.get_value() is not None:
                    cr.set_source_rgb(1, 1, 1)
                    cr.paint()
                    Gdk.cairo_set_source_pixbuf(
                        cr, self.frame.get_value(), self.frame_size_scale["translate_x"], self.frame_size_scale["translate_y"])
                    cr.scale(self.frame_size_scale["scale_w"],
                             self.frame_size_scale["scale_h"])
                    cr.paint()
                    return True
                elif self.mode.get_value() == Screen.Modes.HOUR:
                    cr.set_source_rgb(1, 1, 1)
                    cr.paint()
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
                    return True
                elif self.mode.get_value() == Screen.Modes.VIDEO and self.player.get_value() is not None:
                    cr.set_source_rgb(0, 0, 0)
                    cr.paint()
                    return True
            return False
        except Exception as e:
            logging.error(e)
            return False

    def on_expose(self, widget, cr):
        try:
            self.draw_end.clear()
            with self.canvas.freeze_notify():
                self.draw(cr)
        except Exception as e:
            logging.error(e)

    def on_expose_end(self, widget, event):
        try:
            self.draw_end.set()
        except Exception as e:
            logging.error(e)
