from abc import ABC, abstractmethod
from ..schema.Event import Event

class EventGenerator(ABC):
    @abstractmethod
    def generate_event(self) -> Event:
        """
        Produce a new event
        """
        pass
