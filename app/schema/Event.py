from abc import ABC, abstractmethod
from typing import Any, TypedDict, Optional

class Event(TypedDict, total=False):
    stream_id: str          # ID of the source stream
    timestamp: float        # When the value was observed or imputed
    datatype: str          
    unit: Optional[str]   


    value: float

    # Imputation fields
    observed_value: Optional[float]   
    imputed_value: Optional[float]    
    method: str                       # type of predictor used, like Kalman
    confidence: Optional[float]       # 1.0 for observed, <1.0 if imputed
    imputation_flag: Optional[bool]

    # Optional extra data to pass through
    extras: Optional[dict[str, Any]]



class EventConsumer(ABC):
    @abstractmethod
    def consume_event(self, event: Event):
        """
        Handle an incoming event.
        """
        pass


class EventGenerator(ABC):
    @abstractmethod
    def generate_event(self) -> Event:
        """
        Produce a new event
        """
        pass
