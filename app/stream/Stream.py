import time
import random
from abc import ABC, abstractmethod
from typing import Optional, Any
from app.schema.Event import Event
import time, random

class Stream(ABC):
    def __init__(self, stream_id: str, unit: Optional[str] = None, datatype: str = "float"):
        self.stream_id = stream_id
        self.unit = unit
        self.datatype = datatype
        self._running = False

    @abstractmethod
    def start(self, event_stream: Any, **kwargs):
        pass

    def stop(self):
        self._running = False



class SimulatedStream(Stream):
    def __init__(self, stream_id: str, unit="C", datatype="float", interval=1.0,
                 min_value: float = 15.0, max_value: float = 30.0):
        super().__init__(stream_id, unit, datatype)
        self.interval = interval
        self.min_value = min_value
        self.max_value = max_value

    def generate_event(self) -> Event:
        ground_truth = random.uniform(self.min_value, self.max_value)

        # Apply dropout
        if random.random() < 0.3:
            observed_value = None
        else:
            observed_value = ground_truth

        return {
            "stream_id": self.stream_id,
            "timestamp": time.time(),
            "value": observed_value,          
            "unit": self.unit,
            "datatype": self.datatype,
            "observed_value": observed_value, 
            "extras": {
                "ground_truth": ground_truth
            }
        }

    def start(self, event_stream):
        self._running = True
        while self._running:
            event = self.generate_event()
            event_stream.add_event(event, "observed", self.stream_id)
            time.sleep(self.interval)