from threading import Lock, Event
import logging

USER_CACHE = True


class Cache:
    def __init__(self):
        self.store = dict()
        self.__lock = Lock()
        self.__write = Event()
        self.__write.set()
        self.data = None

    def set(self, filename, part, data):
        with self.__lock:
            self.__write.clear()
            if filename not in self.store:
                self.store[filename] = dict()
            self.store[filename][part] = data
            logging.info(str(filename) + "->" + str(part) + " Cached")
            self.__write.set()

    def clear(self, filename):
        with self.__lock:
            self.__write.clear()
            if filename in self.store:
                del self.store[filename]
                logging.info(filename + " Cache cleared")
            else:
                logging.warning(filename + " not found in cache")

            self.__write.set()

    def get(self, filename, part):
        self.__write.wait()
        if filename not in self.store:
            logging.warning(filename + " not found in cache")
            return None
        if part not in self.store[filename]:
            logging.warning(filename + "::"+str(part) +
                            " not found in cache")
            return None
        return self.store[filename][part]
