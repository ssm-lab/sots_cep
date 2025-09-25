import time
from abc import ABC, abstractmethod
from typing import Optional, Any
from app.schema.Event import Event
import time, random

class Stream(ABC):
    def __init__(self, stream_id: str, unit: Optional[str] = None, datatype: str = "float", interval: float = 1, **kwargs):
        self.stream_id = stream_id
        self.unit = unit
        self.datatype = datatype
        self.interval = interval
        self._running = False

    @abstractmethod
    def generate_event(self) -> Event:
        """Generate one event from this stream"""
        pass

    def start(self, event_stream: Any, interval: float = 1.0):
        """Default loop-based start (override if you need custom logic)"""
        self._running = True
        while self._running:
            event = self.generate_event()
            event_stream.add_event(event, "observed", self.stream_id)
            time.sleep(interval)

    def stop(self):
        self._running = False