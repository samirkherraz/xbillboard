from threading import Lock, Event
import logging


class Cache:
    def __init__(self):
        self.store = dict()
        self._lock = Lock()
        self._write = Event()

    def set(self, filename, part, data):
        with self._lock:
            self._write.clear()
            if filename not in self.store:
                self.store[filename] = dict()
            self.store[filename][part] = data
            logging.info(str(filename) + "->" + str(part) + " Cached")
            self._write.set()

    def clear(self, filename):
        with self._lock:

            self._write.clear()
            if filename in self.store:
                del self.store[filename]
                logging.info(filename + " Cache cleared")
            else:
                logging.warning(filename + " not found in cache")

            self._write.set()

    def get(self, filename, part):
        self._write.wait()
        if filename not in self.store:
            logging.warning(filename + " not found in cache")
            return None
        if part not in self.store[filename]:
            logging.warning(filename + "::"+str(part)+" not found in cache")
            return None
        return self.store[filename][part]
