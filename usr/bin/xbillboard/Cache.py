from threading import Lock, Event


class Cache:
    def __init__(self):
        self.store = dict()
        self._lock = Lock()
        self._write = Event()

    def register(self, filename, part, data):
        with self._lock:
            self._write.clear()
            if filename not in self.store:
                self.store[filename] = dict()
            self.store[filename][part] = data
            self._write.set()

    def clear(self, filename):
        with self._lock:
            self._write.clear()
            if filename in self.store:
                del self.store[filename]
            self._write.set()

    def get(self, filename, part):
        self._write.wait()
        if filename not in self.store:
            return None
        if part not in self.store[filename]:
            return None
        return self.store[filename][part]