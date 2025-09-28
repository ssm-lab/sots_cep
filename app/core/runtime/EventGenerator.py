from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

"""
EventGenerator: Interface for producing events.
Implemented by streams to define how data is generated.
Coordinator schedules calls to this.
"""

class EventGenerator(ABC):
    @abstractmethod
    def generate_event(self) -> Optional[Dict[str, Any]]:
        """
        Produce the next event payload for this source.
        """
        pass