import collections
import mutagen

from exceptions import QueueMaxLengthError

class Voices:
    def __init__(self):
        self.queue = collections.deque(maxlen=10)

    def get(self):
        if len(self.queue) == 0:
            return None
        else:
            return self.queue.popleft()

    def append(self, obj):
        if len(self.queue) >= 10:
            raise QueueMaxLengthError

        if len(self.queue) == 0:
            self.queue.appendleft(obj)
        else:
            self.queue.append(obj)

    def is_empty(self):
        if len(self.queue) == 0:
            return True
        else:
            return False

    def left_durations(self, divider=0):
        t = 0.0
        for v in self.queue:
            try:
                f = mutagen.File(v)
                t += f.info.length
            except Exception:
                t += 0.0
        if divider == 0:
            return t
        else:
            return t / divider
