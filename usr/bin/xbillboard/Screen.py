#!/usr/bin/python
__author__ = "Samir KHERRAZ"
__license__ = "GPLv3"
__maintainer__ = "Samir KHERRAZ"
__email__ = "samir.kherraz@outlook.fr"


import os
import sys

import threading
from threading import Thread, RLock
import gtk
import gobject
import poppler

import datetime
"""
FileType class is used to identify what is the type of the file the program is
    going to render, each type has it's own rendering method
"""


class Screen(Thread):

    class FileType:
        PDF = 1
        IMAGE = 2
        GIF = 3
        NONE = 0
        _PDF_LIST = [".PDF"]
        _IMAGE_LIST = [".JPG", ".JPEG", ".PNG", ".SVG"]
        _GIF_LIST = [".GIF"]

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
    LOGO = gtk.gdk.pixbuf_new_from_file(os.path.abspath(
        "/usr/share/backgrounds/xbillboard.svg"))

    def __init__(self, canvas, delay, filesFolder, align, ratio, rotation, draw_hour=False):
        Thread.__init__(self)
        self._pause = threading.Event()
        self._pause.set()
        self._ended = threading.Event()
        self._ended.clear()
        self._stop = threading.Event()
        self._on_expose_ended = threading.Event()
        self._on_expose_ended.set()
        self._on_expose_started = threading.Event()

        self.rotation = int(rotation)
        self.drawing_job = threading.Event()
        self.drawing_hour = draw_hour
        self.canvas = canvas
        self.filesFolder = filesFolder
        self.document = None
        self.n_pages = None
        self.pageNumber = 0
        self.current_doc = None
        self.current_type = Screen.FileType.NONE
        self.delay = float(delay)
        self.align = Screen.Alignement().get(align)
        self.ratio = Screen.Ratio().get(ratio)
        self.canvas.connect("expose-event", self.on_expose)
        self.canvas.connect_after("expose-event", self.on_expose_end)
    """
    loads the file into memory and defines the rendering procedure according to its type.
    """

    def load_file(self, file):
        _, file_extension = os.path.splitext(file)
        ext = file_extension.upper()
        try:
            del self.document
            del self.current_doc
        except:
            pass
        try:
            if ext in Screen.FileType._PDF_LIST:
                self.current_type = Screen.FileType.PDF
                self.document = poppler.document_new_from_file(
                    "file://"+file, None)
                self.n_pages = self.document.get_n_pages()
                self.current_doc = self.document.get_page(0)
            elif ext in Screen.FileType._IMAGE_LIST:
                self.current_type = Screen.FileType.IMAGE
                self.current_doc = gtk.gdk.pixbuf_new_from_file(file)
            elif ext in Screen.FileType._GIF_LIST:
                self.current_type = Screen.FileType.GIF
                self.document = gtk.gdk.PixbufAnimation(file).get_iter()
                self.current_doc = self.document.get_pixbuf()
        except:
            self.current_type = Screen.FileType.IMAGE
            self.current_doc = Screen.LOGO

    """
    prints all pages of the PDF one by one
    """

    def print_pdf(self):
        i = 0
        while i < self.n_pages and not self.stopped():
            self.current_doc = self.document.get_page(i)
            self.query_draw(self.delay, gobject.PRIORITY_LOW)
            i += 1

    """
    show the gif animation
    """

    def print_gif(self):
        end = False
        while not end and not self.stopped():
            if not self.document.advance(current_time=0.0):
                if self.document.on_currently_loading_frame():
                    end = True
                    pass
                else:
                    pass
            self.current_doc = self.document.get_pixbuf()
            if self.document.get_delay_time() != -1:
                end = self.document.on_currently_loading_frame()
                delay = float(self.document.get_delay_time())/1000
            else:
                delay = self.delay
                end = True
            self.query_draw(delay, gobject.PRIORITY_LOW)

    """
    send an exposure signal to the gtk window for display and wait for a delay
    """

    def query_draw(self, delay, priority):
        if not self.stopped():
            self._on_expose_started.set()
            self._on_expose_ended.clear()
            gobject.idle_add(self.canvas.queue_draw, priority=priority)
            self._on_expose_ended.wait()
            self._stop.wait(delay)

    """
    prints the image on the screen
    """

    def print_image(self):
        self.query_draw(self.delay, gobject.PRIORITY_LOW)

    def print_hour(self):
        self.current_type = None
        self.query_draw(self.delay, gobject.PRIORITY_LOW)

    """
    prints the logo on the screen
    """

    def print_logo(self):
        self.current_doc = Screen.LOGO
        self.current_type = Screen.FileType.IMAGE
        self.query_draw(self.delay, gobject.PRIORITY_LOW)

    """
    the main of the thread
    """

    def run(self):
        rotat = 0
        while not self.stopped():
            self._pause.wait()
            files = sorted([os.path.join(self.filesFolder, file)
                            for file in os.listdir(self.filesFolder)], key=os.path.getctime)
            if len(files) > 0:
                for f in files:
                    self.load_file(f)
                    if self.current_type == Screen.FileType.PDF:
                        self.print_pdf()
                    elif self.current_type == Screen.FileType.IMAGE:
                        self.print_image()
                    elif self.current_type == Screen.FileType.GIF:
                        self.print_gif()
                    if self.drawing_hour:
                        self.print_hour()
            else:
                if self.drawing_hour:
                    self.print_hour()
                else:
                    self.print_logo()
            if rotat < self.rotation:
                rotat += 1
            else:
                self._ended.set()
                self.pause()
                rotat = 0

    """
    stop Robin round and leave the thread
    """

    def wait(self):
        self._ended.wait()
        self._ended.clear()

    def stop(self):
        self._stop.set()
        self._ended.set()
        self._on_expose_ended.set()
        self.resume()

    """
    test if a stop is requested
    """

    def stopped(self):
        return self._stop.isSet()

    """
    Allows you to calculate the size of the document to be printed according to the size of the screen
    """

    def translate(self, p_width, p_height):
        ret = {}
        w = self.canvas.allocation.width
        h = self.canvas.allocation.height
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

    """
    How to print an image on the screen
    """

    def draw_image(self):
        translate = self.translate(
            self.current_doc.get_width(), self.current_doc.get_height())
        pixbuf = self.current_doc.scale_simple(
            translate["width"], translate["height"], gtk.gdk.INTERP_BILINEAR)
        self.canvas.window.draw_pixbuf(
            None, pixbuf, 0, 0, translate["translate_x"], translate["translate_y"], translate["width"], translate["height"])

    def draw_hour(self):
        cr = self.canvas.window.cairo_create()
        now = datetime.datetime.now()
        time = now.strftime("%H:%M")

        cr.set_font_size(self.canvas.allocation.height/5)
        (x, y, width, height, dx, dy) = cr.text_extents(time)

        cr.rectangle(self.canvas.allocation.width/2 - width,
                     self.canvas.allocation.height/2 - height, 2*width, 2*height)
        cr.set_source_rgb(0, 0, 0)
        cr.fill()
        cr.move_to(self.canvas.allocation.width/2 - width /
                   2, self.canvas.allocation.height/2 + height/2)
        cr.set_source_rgb(1, 1, 1)
        cr.show_text(time)
    """
    PDF screen printing procedure on screen
    """

    def draw_pdf(self):
        cr = self.canvas.window.cairo_create()

        translate = self.translate(self.current_doc.get_size()[
            0], self.current_doc.get_size()[1])
        cr.translate(translate["translate_x"], translate["translate_y"])
        cr.scale(translate["scale_w"], translate["scale_h"])
        self.current_doc.render(cr)

    """
    a call the correct method depending on the file type
    """

    def on_expose(self, widget, event):
        if self._on_expose_started.isSet():
            self.canvas.window.begin_paint_rect(event.area)
            if self.current_type == Screen.FileType.PDF:
                self.draw_pdf()
            elif self.current_type == Screen.FileType.IMAGE:
                self.draw_image()
            elif self.current_type == Screen.FileType.GIF:
                self.draw_image()
            else:
                self.draw_hour()
            self.canvas.window.end_paint()

    def on_expose_end(self, widget, event):
        if self._on_expose_started.isSet():
            self._on_expose_started.clear()
            self._on_expose_ended.set()

    def pause(self):
        self._pause.clear()

    def resume(self):
        self._pause.set()
