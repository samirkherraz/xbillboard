#!/usr/bin/python2
__author__ = "Samir KHERRAZ"
__license__ = "GPLv3"
__maintainer__ = "Samir KHERRAZ"
__email__ = "samir.kherraz@outlook.fr"

import logging
import os
import sys

import threading
from threading import Thread, Lock
import gi
gi.require_version('Poppler', '0.18')
from gi.repository import Poppler
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GdkPixbuf, GLib
import datetime
import random
"""
FileType class is used to identify what is the type of the file the program is
    going to render, each type has it's own rendering method
"""


class Screen(Thread):

    class FileType:
        PDF = 1
        IMAGE = 2
        GIF = 3
        HOUR = 4
        NONE = 0
        PDF_LIST = [".PDF"]
        IMAGE_LIST = [".JPG", ".JPEG", ".PNG", ".SVG"]
        GIF_LIST = [".GIF"]

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
    LOGO = GdkPixbuf.Pixbuf.new_from_file(os.path.abspath(
        "/usr/share/backgrounds/xbillboard.svg"))

    def __init__(self, cache, canvas, delay, filesFolder, align, ratio, rotation,draw_hour=False):
        Thread.__init__(self)
        self.cache = cache
        self.filename = ""
        self.name = filesFolder.split('/')[::-1][1]
        self.__critical = Lock()
        self.__pause = threading.Event()
        self.__fileready = threading.Event()
        self.__ended = threading.Event()
        self.__stop = threading.Event()
        self.__on_expose_ended = threading.Event()
        self.__on_expose_started = threading.Event()
        self.__drawing_job = threading.Event()
        self.__ended.clear()
        self.__on_expose_ended.set()
        self.__drawing_hour = draw_hour
        self.rotation = int(rotation)
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
        self.canvas.connect("draw", self.on_expose)
        self.canvas.connect_after("draw", self.on_expose_end)

    """
    loads the file into memory and defines the rendering procedure according to its type.
    """

    def load_file(self, file):
        _, file_extension = os.path.splitext(file)
        self.filename = file.split('/')[::-1][0]
        ext = file_extension.upper()
        try:
            if ext in Screen.FileType.PDF_LIST:
                doc = self.cache.get(self.filename, "options")
                if doc != None:
                    logging.info(self.filename+" found in cache")
                    self.current_type = doc["current_type"]
                    self.document = doc["document"]
                    self.n_pages = doc["n_pages"]
                    self.current_doc = doc["current_doc"]
                else:
                    logging.warning(self.filename+" not found in cache")
                    self.current_type = Screen.FileType.PDF
                    self.document = Poppler.Document.new_from_file(
                        "file://"+file, None)
                    self.n_pages = self.document.get_n_pages()
                    self.current_doc = self.document.get_page(0)
                    self.cache.set(
                        self.filename, "options", {
                            "current_doc": self.current_doc,
                            "document": self.document,
                            "current_type": self.current_type,
                            "n_pages": self.n_pages
                        })

            elif ext in Screen.FileType.IMAGE_LIST:
                doc = self.cache.get(self.filename, "options")
                if doc != None:
                    logging.info(self.filename+" found in cache")
                    self.current_type = doc["current_type"]
                    self.current_doc = doc["current_doc"]
                else:
                    logging.warning(self.filename+" not found in cache")
                    self.current_type = Screen.FileType.IMAGE
                    self.current_doc = Gdk.pixbuf_new_from_file(file)
                    self.cache.set(
                        self.filename, "options", {
                            "current_doc": self.current_doc,
                            "current_type": self.current_type
                        })

            elif ext in Screen.FileType.GIF_LIST:
                doc = self.cache.get(self.filename, "options")
                if doc != None:
                    logging.info(self.filename+" found in cache")
                    self.current_type = doc["current_type"]
                    self.document = doc["document"]
                    self.current_doc = doc["current_doc"]
                    self.pageNumber = 0
                else:
                    logging.warning(self.filename+" not found in cache")
                    self.current_type = Screen.FileType.GIF
                    self.document = GdkPixbuf.PixbufAnimation.new_from_file(file)
                    self.current_doc = self.document.get_iter().get_pixbuf()
                    self.pageNumber = 0
                    self.cache.set(
                        self.filename, "options", {
                            "current_doc": self.current_doc,
                            "document": self.document,
                            "current_type": self.current_type
                        })

            else:
                logging.warning(self.filename+" unsuported file type")
                return False
            return True
        except ValueError as e:
            logging.error("Something went wrong while trying to loadfile")
            logging.error(e)
            return False
    """
    prints all pages of the PDF one by one
    """

    def print_pdf(self):
        i = 0
        while i < self.n_pages and not self.stopped():
            self.current_doc = self.document.get_page(i)
            self.pageNumber = i
            self.query_draw(self.delay)
            i += 1
       

    """
    show the gif animation
    """

    def print_gif(self):
        diter = self.document.get_iter()
        end = False
        self.pageNumber = 0
        while not end and not self.stopped():
            if diter.advance():
                self.pageNumber += 1
                obj = self.cache.get(self.filename, "GIF__"+str(self.pageNumber))
                if obj is not None:
                    delay =  obj["delay"]
                    end =  obj["end"]
                else:
                    self.current_doc = diter.get_pixbuf()
                    delay_time = diter.get_delay_time()
                    if delay_time != -1:
                        end = diter.on_currently_loading_frame()
                        delay = float(delay_time)/float(1000)
                    else:
                        delay = self.delay
                        end = True
                    
                    self.cache.set(self.filename, "GIF__"+str(self.pageNumber), {
                        "delay": delay,
                        "end": end
                    })
                    
                if end:
                    self.pageNumber = 0
                    diter = self.document.get_iter()
                
                self.query_draw(delay)

    """
    send an exposure signal to the Gtk window for display and wait for a delay
    """

    def query_draw(self, delay):
        if not self.stopped():
            logging.info("PRINTING")
            with self.__critical:
                self.__on_expose_ended.clear()
                GLib.idle_add(self.canvas.queue_draw)
            self.__on_expose_ended.wait()
            self.__stop.wait(delay)

    """
    prints the image on the screen
    """

    def print_image(self):
        self.current_type = Screen.FileType.IMAGE
        self.query_draw(self.delay)

    def print_hour(self):
        self.current_type = Screen.FileType.HOUR
        self.query_draw(self.delay)

    """
    prints the logo on the screen
    """

    def print_logo(self):
        self.filename = "LOGO"
        self.current_doc = Screen.LOGO
        self.current_type = Screen.FileType.IMAGE
        self.query_draw(self.delay)

    """
    the main of the thread
    """

    def run(self):
        rotat = 0
        while not self.stopped():
            self.__pause.wait()
            try:
                files = sorted([os.path.join(self.filesFolder, file)
                                for file in os.listdir(self.filesFolder)], key=os.path.getctime)
            
                found = False
                for f in files:
                    if "sync_lock" in f:
                        logging.warning(f +" temporary sync files are not handled")
                    elif self.load_file(f):
                        found = True
                        if self.current_type == Screen.FileType.PDF:
                            self.print_pdf()
                        elif self.current_type == Screen.FileType.IMAGE:
                            self.print_image()
                        elif self.current_type == Screen.FileType.GIF:
                            self.print_gif()
                if not found:
                    logging.info("An error occured, drawing default logo")
                    self.print_logo()
                if self.__drawing_hour:
                    logging.info("Need to draw hour")
                    self.print_hour()
            
            except ValueError as e:
                logging.error(
                    "Something went wrong while trying to load file list")
                logging.error(e)
                self.print_logo()
            
            if rotat < self.rotation:
                rotat += 1
            else:
                with self.__critical:
                    self.__ended.set()
                    self.__pause.clear()
                rotat = 0

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

    """
    How to print(an image on the screen
    """


    def draw_image(self, cr):
       
        obj = self.cache.get(self.filename, "PIXBUF__"+str(self.pageNumber))
        if obj is None:
            
            logging.warning(self.filename+"->"+str(self.pageNumber) +" Not found in cache")
            translate = self.translate(
                self.current_doc.get_width(), self.current_doc.get_height())
            pixbuf = self.current_doc.scale_simple(
                translate["width"], translate["height"], 0)
            self.cache.set(self.filename, "PIXBUF__"+str(self.pageNumber), {
                "pixbuf": pixbuf, "translate": translate})
        else:
            logging.info(self.filename+"->"+str(self.pageNumber)+" Found in cache")
            translate = obj["translate"]
            pixbuf = obj["pixbuf"]
        
        Gdk.cairo_set_source_pixbuf(cr, pixbuf, 0, 0)
        cr.translate(translate["translate_x"], translate["translate_y"])
        cr.scale(translate["scale_w"], translate["scale_h"])
        cr.paint()

    def draw_hour(self, cr):
        try:
            now = datetime.datetime.now()
            time = now.strftime("%H:%M")

            cr.set_font_size(self.canvas.get_allocated_height()/5)
            (x, y, width, height, dx, dy) = cr.text_extents(time)

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
            translate = self.translate(self.current_doc.get_size()[
                0], self.current_doc.get_size()[1])
            cr.translate(translate["translate_x"], translate["translate_y"])
            cr.scale(translate["scale_w"], translate["scale_h"])
            self.current_doc.render(cr)
        except ValueError as e:
            logging.warning(self.filename+"->"+str(self.pageNumber) +" has errors")
            logging.error(e)

    """
    a call the correct method depending on the file type
    """

    def on_expose(self, widget, cr):
            self.__on_expose_ended.clear()
            try:
                cr.set_source_rgb(1, 1, 1)
                cr.paint()
                if self.current_type == Screen.FileType.HOUR:
                    self.draw_hour(cr)
                elif self.current_doc != None:
                    if self.current_type == Screen.FileType.PDF:
                        self.draw_pdf(cr)
                    elif self.current_type == Screen.FileType.IMAGE:
                        self.draw_image(cr)
                    elif self.current_type == Screen.FileType.GIF:
                        self.draw_image(cr)
                else:
                    logging.error("Unsupported file type "+ str(self.current_type))

            except ValueError as e:
                logging.error("Something went wrong while trying to draw on screen")                      
                logging.error(e)


    def on_expose_end(self, widget, event):
            with self.__critical:
                self.__on_expose_ended.set()
