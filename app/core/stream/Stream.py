from typing import Optional

from ..runtime.EventGenerator import EventGenerator

__author__ = "Feyi Adesanya"

class Stream(EventGenerator):
    """
    Abstract base for for event sources.
    """
    def __init__(self, stream_id: str, unit: Optional[str] = None, datatype: str = "float", interval: float = 1.0, params: Optional[dict] = None):
        self.stream_id = stream_id
        self.unit = unit
        self.datatype = datatype
        self.interval = interval
        self.params = params or {}