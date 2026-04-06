from abc import ABC, abstractmethod
from typing import Optional
from .Event import Event

__author__ = "Feyi Adesanya"

class EventConsumer(ABC):
    """
    Abstract interface for consuming events.
    Any component can implement this to react to events.
    """
    @abstractmethod
    def consume_event(self, event: Event, partition: str, stream_id: Optional[str] = None):
        """
        Handle an incoming event from the EventStream.
        """
        pass