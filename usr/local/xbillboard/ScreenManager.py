#!/usr/bin/python

from Screen import Screen

from GtkKeyHandler import Gdk


class ScreenManager():
    def __init__(self):
        sc = Gdk.Screen.get_default()
        self.screenWidth = sc.get_width()
        self.screenHeight = sc.get_height()

    def getLayout(self, x, y):
        r = []
        W = self.screenWidth/x
        H = self.screenHeight/y
        xi = 0
        while xi < x:
            yi = 0
            while yi < y:
                r.append(Screen(W, H, xi*W, yi*H))
                yi += 1
            xi += 1
        return r
