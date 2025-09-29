import random, time
from ..Stream import Stream
from ...schema.Event import Event
from ..StreamRegistry import register_stream_type

@register_stream_type("simulated")
class SimulatedStream(Stream):
    def __init__(self, stream_id: str, unit="C", datatype="float", interval=1.0,
                 min_value: float = 15.0, max_value: float = 30.0,
                 start_value: float = None,
                 drop_chance: float = 0.1,
                 drift: float = 0.2,
                 noise: float = 0.5,
                 **kwargs):
        super().__init__(stream_id, unit, datatype, interval)
        self.min_value = min_value
        self.max_value = max_value
        self.drop_chance = drop_chance
        self.drift = drift
        self.noise = noise

        if start_value is not None:
            self.current_value = max(self.min_value, min(start_value, self.max_value))
        else:
            self.current_value = random.uniform(min_value, max_value)

    def generate_event(self):
        drift_step = random.uniform(-self.drift, self.drift)
        noise_step = random.gauss(0, self.noise)

        self.current_value += drift_step + noise_step
        self.current_value = max(self.min_value, min(self.current_value, self.max_value))

        if random.random() < self.drop_chance:
            raise TimeoutError("Simulated dropped")

        return {
            "stream_id": self.stream_id,
            "sampled_ts": time.time(),
            "value": self.current_value,
            "unit": self.unit,
            "datatype": self.datatype,
            "extras": {}
        }