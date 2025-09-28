from abc import ABC, abstractmethod
from typing import Optional
from ..schema.Event import Event

"""
EventConsumer: Interface for handling incoming events.
Any component can implement this to react to events.
"""

class EventConsumer(ABC):
    @abstractmethod
    def consume_event(self, event: Event, partition: str, stream_id: Optional[str] = None):
        """
        Handle an incoming event from the EventStream.
        """
        pass