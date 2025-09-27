import random, time
from ...stream.Stream import Stream
from ...schema.Event import Event
from ...stream.StreamRegistry import register_stream_type

@register_stream_type("simulated_dropping_stream")
class SimulatedDroppingStream(Stream):
    def __init__(self, stream_id: str, unit="C", datatype="float", interval=1.0,
                 min_value: float = 15.0, max_value: float = 30.0,
                 drop_chance: float = 0.25,  
                 **kwargs):
        super().__init__(stream_id, unit, datatype, interval)
        self.min_value = min_value
        self.max_value = max_value
        self.drop_chance = drop_chance
        self.last_truth = None

    def generate_event(self) -> Event:
        value = random.uniform(self.min_value, self.max_value)
        self.last_truth = value
        if random.random() < self.drop_chance:
            raise TimeoutError("Simulated dropped")
        
        return {
            "stream_id": self.stream_id,
            "sampled_ts": time.time(),
            "value": value,
            "unit": self.unit,
            "datatype": self.datatype,
            "status": "observed",
            "origin": "source",
            "extras": {"ground_truth": value}
        }
