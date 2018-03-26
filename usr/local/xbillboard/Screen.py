#!/usr/bin/python

__author__ = "Samir KHERRAZ"
__license__ = "GPLv3"
__version__ = "0.0.3"
__maintainer__ = "Samir KHERRAZ"
__email__ = "samir.kherraz@outlook.fr"
__status__ = "Testing"


import os
import sys

import threading
from threading import Thread
import gtk
import gobject
import poppler


class FileType:
    PDF = 1
    IMAGE = 2
    GIF = 3
    NONE = 0
    _PDF_LIST = [".PDF"]
    _IMAGE_LIST = [".JPG", ".JPEG", ".PNG", ".SVG"]
    _GIF_LIST = [".GIF"]


class Screen(Thread):
    LOGO = gtk.gdk.pixbuf_new_from_file(
            os.path.dirname(os.path.realpath(__file__))+"/logo.svg")

    def __init__(self, parent, canvas, delay, filesFolder):
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
        self.logo = gtk.gdk.pixbuf_new_from_file(
            os.path.dirname(os.path.realpath(__file__))+"/logo.svg")

    def loadFile(self, file):
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

    def print_pdf(self):
        i = 0
        while i < self.n_pages and not self.stopped():
            self.current_page = self.document.get_page(i)
            self.query_draw(self.delay, gobject.PRIORITY_LOW)
            i += 1

    def print_gif(self):
        end = False
        while not end and not self.stopped():
            if not self.document.advance(current_time=0.0):
                if  self.document.on_currently_loading_frame():
                    end = True
                    pass
                else:
                    pass
            self.current_page = self.document.get_pixbuf()
            if self.document.get_delay_time() != -1:
                end = self.document.on_currently_loading_frame()
                delay = float(self.document.get_delay_time())/100
            else:
                delay = self.delay
                end = True
            self.query_draw(delay, gobject.PRIORITY_HIGH)

    def query_draw(self, delay, priority):
        gobject.idle_add(self.canvas.queue_draw, priority=priority)
        self._stop.wait(delay)

    def print_image(self):
        self.query_draw(self.delay, gobject.PRIORITY_LOW)

    def print_logo(self):
        self.current_page = Screen.LOGO
        self.current_type = FileType.IMAGE
        self.query_draw(self.delay, gobject.PRIORITY_LOW)
   
    def run(self):
        while not self.stopped():
            files = sorted([os.path.join(self.filesFolder, file)
                            for file in os.listdir(self.filesFolder)], key=os.path.getctime)
            if len(files) > 0:
                for f in files:
                    self.loadFile(f)
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

    def stop(self):
        self._stop.set()

    def stopped(self):
        return self._stop.isSet()

    def draw_image(self, area):
        pixbuf = self.current_page.scale_simple(
            area.width, area.height, gtk.gdk.INTERP_NEAREST)
        
        self.canvas.window.draw_pixbuf(
            None, pixbuf, 0, 0, 0, 0, area.width, area.height)

    def draw_pdf(self, area):       
        cr = self.canvas.window.cairo_create()
        p_width, p_height = self.current_page.get_size()
        cr.scale(area.width/p_width, area.height/p_height)
        self.current_page.render(cr)


    def draw_white(self):
        al = self.canvas.get_allocation()
        cr = self.canvas.window.cairo_create()
        cr.set_source_rgb(1, 1, 1)
        cr.rectangle(0, 0, al[0], al[1])
        cr.fill()
        
    def on_expose(self, widget, event):
        self.canvas.window.begin_paint_rect(event.area)
        if self.current_type == FileType.PDF:
            self.draw_pdf(event.area)
        elif self.current_type == FileType.IMAGE:
            self.draw_image(event.area)
        elif self.current_type == FileType.GIF:
            self.draw_image(event.area)
        else:
            self.print_logo()
        self.canvas.window.end_paint()
