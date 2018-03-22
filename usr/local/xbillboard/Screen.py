#!/usr/bin/python
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Poppler', '0.18')

from gi.repository import Gtk,Gdk, Poppler, GObject
import os
import sys

import threading
from threading import Thread
import time



class Screen(Thread):

    def __init__(self,parent, canvas, delay, filesFolder):
        Thread.__init__(self)
        self.window = Gtk.OffscreenWindow()
        self._stop = threading.Event()
        self.canvas = canvas
        self.filesFolder = filesFolder
        self.document = None
        self.n_pages = None
        self.pageNumber = 0
        self.current_page = None
        self.parent = parent
        self.delay = float(delay)
        
    def auto_step(self):
        i = 0
        while i < self.n_pages :
            Gdk.threads_enter()
            self.current_page = self.document.get_page(i)
            self.canvas.queue_draw()
            Gdk.threads_leave()
            i += 1
            if not self.stopped():
                time.sleep(self.delay)

    def loadFile(self, file):
        uri = "file://" + file
        self.document = Poppler.Document.new_from_file(uri, None)
        self.n_pages = self.document.get_n_pages()
        self.current_page = self.document.get_page(0)
       

    def run(self):
        while not self.stopped():
            files = sorted([os.path.join(self.filesFolder, file)
                            for file in os.listdir(self.filesFolder)], key=os.path.getctime)
            if len(files) > 0:
                for f in files:
                    self.loadFile(f)
                    self.auto_step()
            else:
                if not self.stopped():
                    time.sleep(self.delay)
        print "Exit"
            

    def stop(self):
        Gdk.threads_leave()
        self._stop.set()

    def stopped(self):
        return self._stop.isSet()


       
    def on_expose(self, widget, surface):
        
        if self.current_page != None:
            p_width, p_height = self.current_page.get_size()
            width = self.canvas.get_allocation().width
            height= self.canvas.get_allocation().height
            scale = min(width/p_width, height/p_height)
            if scale != 1:
                    surface.scale(scale, scale)
            self.current_page.render(surface)


