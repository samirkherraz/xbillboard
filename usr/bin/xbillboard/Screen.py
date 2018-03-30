#!/usr/bin/python
__author__ = "Samir KHERRAZ"
__license__ = "GPLv3"
__maintainer__ = "Samir KHERRAZ"
__email__ = "samir.kherraz@outlook.fr"


import os
import sys

import threading
from threading import Thread
import gtk
import gobject
import poppler

"""
FileType class is used to identify what is the type of the file the program is
    going to render, each type has it's own rendering method
"""


class FileType:
    PDF = 1
    IMAGE = 2
    GIF = 3
    NONE = 0
    _PDF_LIST = [".PDF"]
    _IMAGE_LIST = [".JPG", ".JPEG", ".PNG", ".SVG"]
    _GIF_LIST = [".GIF"]


class Screen(Thread):
    """
    Loading the logo pixel buffer once for optimization
    it is showed if errors occured
    """
    LOGO = gtk.gdk.pixbuf_new_from_file(os.path.abspath(
        "/usr/share/backgrounds/xbillboard.svg"))

    def __init__(self, canvas, delay, filesFolder):
        Thread.__init__(self)
        self._stop = threading.Event()
        self.canvas = canvas
        self.filesFolder = filesFolder
        self.document = None
        self.n_pages = None
        self.pageNumber = 0
        self.current_page = None
        self.current_type = FileType.NONE
        self.delay = float(delay)

    """
    loads the file into memory and defines the rendering procedure according to its type.
    """

    def load_file(self, file):
        _, file_extension = os.path.splitext(file)
        ext = file_extension.upper()
        try:
            del self.document
            del self.current_page
        except:
            pass
        try:
            if ext in FileType._PDF_LIST:
                self.current_type = FileType.PDF
                self.document = poppler.document_new_from_file(
                    "file://"+file, None)
                self.n_pages = self.document.get_n_pages()
                self.current_page = self.document.get_page(0)
            elif ext in FileType._IMAGE_LIST:
                self.current_type = FileType.IMAGE
                self.current_page = gtk.gdk.pixbuf_new_from_file(file)
            elif ext in FileType._GIF_LIST:
                self.current_type = FileType.GIF
                self.document = gtk.gdk.PixbufAnimation(file).get_iter()
                self.current_page = self.document.get_pixbuf()
        except:
            self.current_type = FileType.IMAGE
            self.current_page = self.logo

    """
    prints all pages of the PDF one by one
    """

    def print_pdf(self):
        i = 0
        while i < self.n_pages and not self.stopped():
            self.current_page = self.document.get_page(i)
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
            self.current_page = self.document.get_pixbuf()
            if self.document.get_delay_time() != -1:
                end = self.document.on_currently_loading_frame()
                delay = float(self.document.get_delay_time())/1000
            else:
                delay = self.delay
                end = True
            self.query_draw(delay, gobject.PRIORITY_HIGH)

    """
    send an exposure signal to the gtk window for display and wait for a delay
    """

    def query_draw(self, delay, priority):
        gobject.idle_add(self.canvas.queue_draw, priority=priority)
        self._stop.wait(delay)

    """
    prints the image on the screen
    """

    def print_image(self):
        self.query_draw(self.delay, gobject.PRIORITY_LOW)

    """
    prints the logo on the screen
    """

    def print_logo(self):
        self.current_page = Screen.LOGO
        self.current_type = FileType.IMAGE
        self.query_draw(self.delay, gobject.PRIORITY_LOW)

    """
    the main of the thread
    """

    def run(self):
        while not self.stopped():
            files = sorted([os.path.join(self.filesFolder, file)
                            for file in os.listdir(self.filesFolder)], key=os.path.getctime)
            if len(files) > 0:
                for f in files:
                    self.load_file(f)
                    if self.current_type == FileType.PDF:
                        self.print_pdf()
                    elif self.current_type == FileType.IMAGE:
                        self.print_image()
                    elif self.current_type == FileType.GIF:
                        self.print_gif()
                    else:
                        self.print_logo()

            else:
                self.print_logo()

    """
    stop Robin round and leave the thread
    """

    def stop(self):
        self._stop.set()

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
        ret["scale"] = (min(scale_h, scale_w))
        ret["width"] = int(p_width*ret["scale"])
        ret["height"] = int(p_height*ret["scale"])
        ret["translate_x"] = int(w/2-ret["width"]/2)
        ret["translate_y"] = int(h/2-ret["height"]/2)

        return ret

    """
    How to print an image on the screen
    """

    def draw_image(self, area):
        translate = self.translate(
            self.current_page.get_width(), self.current_page.get_height())
        pixbuf = self.current_page.scale_simple(
            translate["width"], translate["height"], gtk.gdk.INTERP_NEAREST)
        self.canvas.window.draw_pixbuf(
            None, pixbuf, 0, 0, translate["translate_x"], translate["translate_y"], translate["width"], translate["height"])

    """
    PDF screen printing procedure on screen
    """

    def draw_pdf(self):
        cr = self.canvas.window.cairo_create()
        translate = self.translate(self.current_page.get_size()[
            0], self.current_page.get_size()[1])
        cr.translate(translate["translate_x"], translate["translate_y"])
        cr.scale(translate["scale"], translate["scale"])
        self.current_page.render(cr)

    """
    a call the correct method depending on the file type
    """

    def on_expose(self, widget, event):
        self.canvas.window.begin_paint_rect(event.area)
        if self.current_type == FileType.PDF:
            self.draw_pdf()
        elif self.current_type == FileType.IMAGE:
            self.draw_image(event.area)
        elif self.current_type == FileType.GIF:
            self.draw_image(event.area)
        else:
            self.print_logo()
        self.canvas.window.end_paint()
