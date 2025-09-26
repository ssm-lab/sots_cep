from abc import ABC, abstractmethod
from ..schema.Event import Event

class EventConsumer(ABC):
    @abstractmethod
    def consume_event(self, event: Event):
        """
        Handle an incoming event.
        """
        pass
