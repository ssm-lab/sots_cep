import logging
import time
from typing import Any

from ..schema.Event import Event, make_event
from ..schema.EventGenerator import EventGenerator
from ..utils.UtilsFuncs import _as_observer


class EventSource(EventGenerator):
    """
    Base class for all event sources.

    Routes events to partitions depending on the
    lifecycle state of the constituent.
    """
    def __init__(
        self,
        *,
        id: str,
        type: str,
        stream,
        lifecycle
    ):
        self.id = id
        self.type = type
        self.stream = stream

        self.lifecycle = lifecycle

        self.allow_observed = False
        self.allow_validated = False



    def connect(self):
        runtime = self.lifecycle.get_runtime(self.id)

        runtime.emit_observed.subscribe(
            _as_observer(self._on_observed_changed)
        )

        runtime.emit_validated.subscribe(
            _as_observer(self._on_validated_changed)
        )

    def _on_observed_changed(self, value: bool):
        self.allow_observed = value

    def _on_validated_changed(self, value: bool):
        self.allow_validated = value

    def generate_event(self, params: dict[str, Any]) -> Event:

        return make_event(
            type=self.type,
            src=self.id,
            event_status="observed",
            value=params["value"],
            event_ts=params.get("event_ts", time.time()),
            value_datatype=params.get("value_datatype"),
            value_unit=params.get("value_unit"),
            confidence=params.get("confidence"),
            extras=params.get("extras"),
        )


    def emit_event(self, params):
        if not self.allow_observed:
            logging.debug(f"[SOURCE {self.id}] blocked → no emission")
            return None

        event = self.generate_event(params)

        state = self.lifecycle.get_state(self.id)

        if state:
            event["extras"] = {
                "health": state["health_main"],
                "belonging_main": state["belonging_main"],
                "belonging_sub": state["belonging_sub"]
            }

        if self.allow_validated:
            partition = "observed.validated"
            event["event_status"] = "validated"
        else:
            partition = "observed"
            event["event_status"] = "observed"

        event["partition"] = partition

        self.stream.add_event(event, partition, self.id)

        logging.debug(
            f"[SOURCE {self.id}] → {partition} "
            f"(obs={self.allow_observed}, val={self.allow_validated})"
        )

        return event