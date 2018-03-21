#!/usr/bin/python

import os
import sys
from SystemCall import SystemCall
from ThLoop import ThLoop


class Sync(ThLoop):
    def __init__(self, url, localdir, delay):
        ThLoop.__init__(self, delay)
        self.url = url
        self.localdir = localdir
        self.delay = float(delay)
        self.cmd = "wget -N "+self.url+" -P "+self.localdir

    def loopjob(self):
        SystemCall(self.cmd)
        return False

    def cleanUp(self):
        SystemCall("rm -vf "+self.localdir+"*")
