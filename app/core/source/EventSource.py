from abc import ABC
import time
from typing import Any, Optional

from ..runtime.EventGenerator import EventGenerator
from ..runtime.EventStream import EventStream
from ..schema.Event import Event, make_event

__author__ = "Feyi Adesanya"

class EventSource(EventGenerator):
    """
    Base class for event sources.
    """

    def __init__(
        self,
        *,
        id: str,
        type: str,
        stream: EventStream,
    ):
        self.id = id
        self.type = type
        self.stream = stream


    def generate_event(self, event_params: dict[str, Any] | None = None) -> Event:
        event_params = event_params or {}
        if "value" not in event_params:
            raise ValueError("requires 'value' in event_params")

        event = make_event(
            type=self.type,
            src=self.id,
            event_status="observed",
            value=event_params["value"],
            event_ts=event_params.get("event_ts", time.time()),
            value_datatype=event_params.get("value_datatype", "unknown"),
            value_unit=event_params.get("value_unit"),
            confidence = event_params.get("confidence"),
            extras=event_params.get("extras"),
        )
        return event 
    
    def emit_event(self, event_params: dict[str, Any] | None = None):
        event = self.generate_event(event_params)
        self.stream.add_event(event, "observed", self.id)
        return event
