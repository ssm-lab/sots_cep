from abc import ABC, abstractmethod
from typing import Any, TypedDict, Optional
import uuid
import time
from typing import Optional, Any

class Event(TypedDict):
    stream_id: str
    timestamp: float
    datatype: str
    unit: Optional[str]
    value: Optional[float]

    # Imputation / reliability
    imputed_value: Optional[float]
    imputation_method: Optional[str]          # e.g., "Kalman", "ARIMA"
    confidence: Optional[float]    # 1.0 = observed, <1.0 if estimated
    imputation_flag: Optional[bool]

    # Provenance / metadata
    event_id: Optional[str]
    status: str                    # "observed", "imputed", "missing"
    source: str          # "sensor", "simulator", etc.
    provenance: Optional[dict[str, Any]]

    # Flexible extra fields
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
