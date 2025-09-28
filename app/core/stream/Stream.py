from typing import Optional

from ..runtime.EventGenerator import EventGenerator

"""
Stream: Base class for event sources.
Implements generate_event() for data-producing logic.
Extended by simulated or real sensor streams.
"""

class Stream(EventGenerator):
    def __init__(self, stream_id: str, unit: Optional[str] = None, datatype: str = "float", interval: float = 1.0, **kwargs):
        self.stream_id = stream_id
        self.unit = unit
        self.datatype = datatype
        self.interval = interval