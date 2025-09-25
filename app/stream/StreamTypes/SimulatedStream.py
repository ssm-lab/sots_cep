import random, time
from app.stream.Stream import Stream
from app.schema.Event import Event
from app.stream.StreamRegistry import register_stream_type

@register_stream_type("simulated")
class SimulatedStream(Stream):
    def __init__(self, stream_id: str, unit="C", datatype="float", interval=1.0,
                 min_value: float = 15.0, max_value: float = 30.0, **kwargs):
        super().__init__(stream_id, unit, datatype, interval)
        self.interval = interval
        self.min_value = min_value
        self.max_value = max_value

    def generate_event(self) -> Event:
        ground_truth = random.uniform(self.min_value, self.max_value)
        observed_value = ground_truth if random.random() > 0.3 else None

        return {
            "stream_id": self.stream_id,
            "timestamp": time.time(),
            "value": observed_value,
            "unit": self.unit,
            "datatype": self.datatype,
            "observed_value": observed_value,
            "extras": {"ground_truth": ground_truth}
        }
