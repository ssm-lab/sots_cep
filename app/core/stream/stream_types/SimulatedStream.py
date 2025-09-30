import random, time
from ..Stream import Stream
from ..StreamRegistry import register_stream_type

__author__ = "Feyi Adesanya"

@register_stream_type("simulated")
class SimulatedStream(Stream):
    def __init__(self, stream_id: str, unit="C", datatype="float", interval=1.0, params=None):
        super().__init__(stream_id, unit, datatype, interval, params)
        params = params or {}

        self.min_value = params.get("min", 15.0)
        self.max_value = params.get("max", 30.0)
        self.drift = params.get("drift", 0.2)
        self.noise = params.get("noise", 0.5)
        self.drop_chance = params.get("drop_chance", 0.1)

        start_value = params.get("start_value", None)
        if start_value is not None:
            self.current_value = max(self.min_value, min(start_value, self.max_value))
        else:
            self.current_value = random.uniform(self.min_value, self.max_value)

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
