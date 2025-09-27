import random, time
from ..Stream import Stream
from ...schema.Event import Event
from ..StreamRegistry import register_stream_type

@register_stream_type("simulated")
class SimulatedStream(Stream):
    def __init__(self, stream_id: str, unit="C", datatype="float", interval=1.0,
                 min_value: float = 15.0, max_value: float = 30.0, **kwargs):
        super().__init__(stream_id, unit, datatype, interval)
        self.interval = interval
        self.min_value = min_value
        self.max_value = max_value
        self.count = 0

    def generate_event(self) -> Event:
        self.count+=1
        generated_value = random.uniform(self.min_value, self.max_value)

        return {
            "stream_id": self.stream_id,
            "sampled_ts": time.time(),
            "value": generated_value,
            "unit": self.unit,
            "datatype": self.datatype,
            "status": "observed",
            "origin": "source",
            "extras": {"ground_truth": generated_value}
        }