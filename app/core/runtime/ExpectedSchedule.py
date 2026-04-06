import time

class ExpectedSchedule:
    def __init__(self, interval, grace=0.1):
        self.interval = interval
        self.grace = grace
        self.next_ts = time.time() + interval

    def advance(self):
        self.next_ts += self.interval

    def is_missed(self, now):
        return now > self.next_ts + self.grace

