#!/usr/bin/python

import os


class SystemCall():

    def __init__(self, com, read=False):
        print "EXE:::"+com+"\n\n"
        if read:
            self.result = os.popen(com).read()
        else:
            os.system(com)

    def getResult(self):
        return self.result
