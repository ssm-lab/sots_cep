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
        self.count = 0

    def generate_event(self) -> Event:
        self.count+=1
        generated_value = random.uniform(self.min_value, self.max_value)

        return {
            "stream_id": self.stream_id,
            "timestamp": time.time(),
            "value": generated_value,
            "unit": self.unit,
            "datatype": self.datatype,
            "status": "observed",
            "extras": {}
        }



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

    def generate_event(self) -> Event:
        if random.random() < self.drop_chance:
            raise TimeoutError("Simulated dropped")

        value = random.uniform(self.min_value, self.max_value)
        return {
            "stream_id": self.stream_id,
            "timestamp": time.time(),
            "value": value,
            "unit": self.unit,
            "datatype": self.datatype,
            "status": "observed",
            "extras": {}
        }
