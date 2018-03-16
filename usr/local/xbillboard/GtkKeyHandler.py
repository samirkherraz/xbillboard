import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk

class GtkKeyHandler(Gtk.Window):

    def __init__(self):
        Gtk.Window.__init__(self, title="Keyboard Handler")
        self.move(0,0)
        self.set_decorated(False)       
        self.set_keep_above(True)
        self.set_default_size(0,0)
        self.connect("key-press-event", self.on_key_release)          
        self.connect("delete_event", Gtk.main_quit)
        self.connect("focus-out-event", self.bring_to_front)
        self.connect("focus-in-event", self.bring_to_front)
        self.connect("leave-notify-event", self.bring_to_front)
        self.connect("window_state_event", self.bring_to_front)
        self.stick()
        self.present()

    def on_key_release(self, widget, ev, data=None):
        print ev.keyval
        if ev.keyval == Gdk.KEY_Escape: #If Escape pressed, reset text
             Gtk.main_quit()

    def bring_to_front(self,widget, event):
        self.present()


