from collections import deque
from datetime import datetime


class Timer(object):
    def __init__(self):
        self.pendingTags = deque()
        self.log = []

    @staticmethod
    def now():
        return datetime.utcnow()

    def begin(self, tag):
        self.pendingTags.append((tag, self.now()))

    def end(self, tag):
        tag, startTime = self.pendingTags.pop()
        endTime = self.now()
        delta = endTime - startTime
        self.log.append((endTime.isoformat(), tag, delta))

    def exceptioned(self, exception):
        endTime = self.now()
        endTimeFormatted = endTime.isoformat()
        while len(self.pendingTags) > 0:
            tag, startTime = self.pendingTags.pop()
            self.log.append((endTimeFormatted, tag + ' *** failed: {}'.format(exception.status), 0.0))

    def __iter__(self):
        return iter(self.log)

    def __len__(self):
        return len(self.log)
