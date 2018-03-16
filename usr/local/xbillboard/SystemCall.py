#!/usr/bin/python

import os

class SystemCall():

    def __init__(self, com, read=False):
        print "EXE:::"+com+"\n\n"
        if read:
            self.result = os.popen(com).read()
        else:
            i = 0
            while os.WEXITSTATUS(os.system(com)) != 0:
                i += 1
                if i > 5:
                    break

    def getResult(self):
        return self.result
