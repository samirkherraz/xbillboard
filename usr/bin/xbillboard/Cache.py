from threading import Lock, Event
import logging

USER_CACHE = False


class Cache:
    def __init__(self):
        self.store = dict()
        self.__lock = Lock()
        self.__write = Event()

    def set(self, filename, part, data):
        if USER_CACHE:
            with self.__lock:
                self.__write.clear()
                if filename not in self.store:
                    self.store[filename] = dict()
                self.store[filename][part] = data
                logging.info(str(filename) + "->" + str(part) + " Cached")
                self.__write.set()

    def clear(self, filename):
        if USER_CACHE:
            with self.__lock:

                self.__write.clear()
                if filename in self.store:
                    del self.store[filename]
                    logging.info(filename + " Cache cleared")
                else:
                    logging.warning(filename + " not found in cache")

                self.__write.set()

    def get(self, filename, part):
        if USER_CACHE:
            self.__write.wait()
            if filename not in self.store:
                logging.warning(filename + " not found in cache")
                return None
            if part not in self.store[filename]:
                logging.warning(filename + "::"+str(part) +
                                " not found in cache")
                return None
            return self.store[filename][part]
        else:
            return None
