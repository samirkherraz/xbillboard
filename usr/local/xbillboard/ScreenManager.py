#!/usr/bin/python

import os
import sys

from Screen import Screen
from SystemCall import SystemCall


class ScreenManager():
    def __init__(self):
        width = SystemCall(
            "xrandr | grep '*' |awk -F '\n' '{print $1}' | awk -F ' ' '{print $1}' |  awk -F 'x' '{print $1}' ", True)
        height = SystemCall(
            "xrandr | grep '*' |awk -F '\n' '{print $1}' | awk -F ' ' '{print $1}' |  awk -F 'x' '{print $2}' ", True)
        self.screenWidth = int(width.getResult())
        self.screenHeight = int(height.getResult())

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
