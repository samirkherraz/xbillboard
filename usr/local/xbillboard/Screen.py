#!/usr/bin/python

import os
import sys

import threading
from threading import Thread
import gtk
import gobject
import poppler


class Screen(Thread):

    def __init__(self, parent, canvas, delay, filesFolder):
        Thread.__init__(self)
        self._stop = threading.Event()
        self.canvas = canvas
        self.filesFolder = filesFolder
        self.document = None
        self.n_pages = None
        self.pageNumber = 0
        self.current_page = None
        self.delay = float(delay)

    def auto_step(self):
        i = 0
        while i < self.n_pages:
            self.current_page = self.document.get_page(i)
            i += 1
            gobject.idle_add(self.canvas.queue_draw)
            self._stop.wait(self.delay)

    def loadFile(self, file):
        try:
            self.document = poppler.document_new_from_file(
                "file://"+file, None)
            self.n_pages = self.document.get_n_pages()
            self.current_page = self.document.get_page(0)
            return True
        except:
            return False

    def run(self):
        while not self.stopped():
            files = sorted([os.path.join(self.filesFolder, file)
                            for file in os.listdir(self.filesFolder)], key=os.path.getctime)
            if len(files) > 0:
                for f in files:
                    if self.loadFile(f):
                        self.auto_step()
            else:
                if self.loadFile("/usr/local/xbillboard/logo.pdf"):
                    self.auto_step()
                else:
                    self._stop.wait(self.delay)

    def stop(self):
        # gtk.gdk.threads_leave()
        self._stop.set()

    def stopped(self):
        return self._stop.isSet()

    def on_expose(self, widget, surface):

        if self.current_page != None:
            cr = widget.window.cairo_create()
            p_width, p_height = self.current_page.get_size()
            width = self.canvas.get_allocation().width
            height = self.canvas.get_allocation().height
            scale = min(width/p_width, height/p_height)
            if scale != 1:
                cr.scale(scale, scale)
            self.current_page.render(cr)
