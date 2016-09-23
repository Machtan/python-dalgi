import time

class FramerateLimiter:
    """A simple timer which can ensure that something runs at a fixed rate"""
    def __init__(self, max_fps):
        self.period = 1.0/max_fps
        self.prev = time.perf_counter()
        self.times = []

    def tick(self):
        """Advances the timer by one frame, potentially sleeping until it is time for the next"""
        now = time.perf_counter()
        delta = now - self.prev
        self.times.append(delta)
        if delta < self.period:
            time.sleep(self.period - delta)
        self.prev = time.perf_counter()

    def reset(self):
        """Resets the elapsed period of the timer"""
        self.prev = time.perf_counter()