import time
import logging
from typing import Any

from ..schema.Event import Event, make_event
from ..runtime.EventStream import EventStream
from ..runtime.EventGenerator import EventGenerator
from .predictor_types.BasePredictor import BasePredictor

__author__ = "Feyi Adesanya"


class Reconstructor(EventGenerator):
    """
    Applies a predictor to reconstruct missing events.
    """
    def __init__(
        self,
        *,
        source_id: str,
        predictor: BasePredictor,
        event_stream: EventStream,
    ):
        self.source_id = source_id
        self.predictor = predictor
        self.event_stream = event_stream


    def handle_observed(self, event: Event) -> None:
        """
        Update predictor state using an observed event.
        """
        value = event.get("value")
        if value is None:
            return

        self.predictor.update(value)

        logging.debug(
            f"[RECONSTRUCTOR-{self.source_id}] Predictor updated with observed value: {value}"
        )



    def generate_event(self, event_params: dict[str, Any] | None = None) -> Event:
        event_params = event_params or {}
        if "prediction" not in event_params:
            raise ValueError("requires 'prediction' in event_params")
        if "expected_ts" not in event_params:
            raise ValueError("requires 'expected_ts' in event_params")
        
        event = make_event(
            type="simulated",
            src=self.source_id,
            event_status="reconstructed",
            value=event_params["prediction"],
            event_ts=event_params["expected_ts"],
            confidence=event_params["confidence"],
            extras={
                "reconstruction_method": self.predictor.name,
                "reconstruction_time": time.time(),
            },
        )
        return event


    def emit_event(self, reconstrcuted_event):
        self.event_stream.add_event(
            reconstrcuted_event,
            partition="reconstructed",
            source_id=self.source_id,
        )


    # Reconstruction (called by Coordinator on absence)
    def reconstruct(self, expected_ts: float) -> Event:
        """
        Reconstruct a missing event at the given expected timestamp and publish it to the EventStream.
        """
        event_params = {
            "confidence": self.predictor.confidence(),
            "prediction":self.predictor.predict(),
            "expected_ts": expected_ts
        }
        reconstrcuted_event = self.generate_event(event_params)
        self.emit_event(reconstrcuted_event)

        logging.debug(
            f"[RECONSTRUCTOR-{self.source_id}] Reconstructed event "
            f"at {expected_ts:.3f}"
        )