class SimulationClock:
    def __init__(self, start=0, step=1):
        self.step = step
        self.tick_count = 0
        self.time = start

    def now(self):
        return self.time

    def tick(self):
        self.tick_count += 1
        self.time += self.step