from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from ..schema.Event import Event

__author__ = "Feyi Adesanya"

class EventGenerator(ABC):
    """
    Abstract interface for generating events from data sources.
    """
    @abstractmethod
    def generate_event(self) -> Event:
        """
        Produce the next event payload for this source.
        """
        pass