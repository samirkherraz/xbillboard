#!/usr/bin/python
import sys
import time
import gi
from ThLoop import ThLoop
gi.require_version('Gtk', '3.0')
gi.require_version('Poppler', '0.18')
from gi.repository import Gtk,Poppler, Gdk, GObject


class PreviewWindow(Gtk.ApplicationWindow):
    def __init__(self,w,h,x,y, filename):
        Gtk.ApplicationWindow.__init__(self, title="Pdf Viewer")
        self.move(x,y)
        self.set_default_size(w,h)
        self.set_decorated(False)       
        self.set_keep_above(False)
        self.unstick()
        self.previewDrawingArea = Gtk.DrawingArea()
        self.add(self.previewDrawingArea)
        self.previewDrawingArea.connect("draw", self.__on_expose)
        self.connect("delete_event", self.close)   
        uri = "file://" + filename

        self.document = Poppler.Document.new_from_file(uri, None)
        self.n_pages = self.document.get_n_pages()
        self.pageNumber = 0
        self.current_page = self.document.get_page(self.pageNumber)

        p_width, p_height = self.current_page.get_size()
        self.scale = min(  w/p_width, h/p_height )



    def __refresh(self):

        self.current_page = self.document.get_page(min(self.pageNumber, self.n_pages-1))
        self.previewDrawingArea.queue_draw()

    def __on_expose(self, widget, surface):
        surface.set_source_rgb(1, 1, 1)

        if self.scale != 1:
            surface.scale(self.scale, self.scale)

        surface.rectangle(0, 0, 50, 50)
        surface.fill()
        self.current_page.render(surface)

    def next(self):
        self.__refresh()
        self.pageNumber += 1
        print self.pageNumber


    def close(self, widget, other = None):
        Gtk.main_quit()
    
    
    def quit(self):
        Gtk.main_quit()
    
    def end(self):
        return self.pageNumber >= self.n_pages




class Auto(ThLoop):

    def __init__(self, window, delay):
        ThLoop.__init__(self, float(delay))
        self.window = window

    def loopjob(self):
        if not self.window.end():
            self.window.next()
            return False
        else:
            self.window.quit()
            return True
    




class GtkPdfViewer:
    def __init__(self, w,h,x,y,d,f):
        previewWindow = PreviewWindow(w,h,x,y,f)
        previewWindow.show_all()
        auto = Auto(previewWindow, d)
        auto.start()
        Gtk.main()
        auto.stop()


if __name__ == '__main__':

    print "Width: "+sys.argv[1]
    w = int(sys.argv[1])
    print "Height: "+sys.argv[2]
    h = int(sys.argv[2])
    print "Position X: "+sys.argv[3]
    x = int(sys.argv[3])
    print "Position Y: "+sys.argv[4]
    y = int(sys.argv[4])
    print "Delay: "+sys.argv[5]
    delay = float(sys.argv[5])
    print "File: "+sys.argv[6]
    file = str(sys.argv[6])

    

    GtkPdfViewer(w,h,x,y,delay, file)

