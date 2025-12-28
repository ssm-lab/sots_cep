import time
import logging

from ..schema.Event import Event, make_event
from ..runtime.EventStream import EventStream
from .predictor_types.BasePredictor import BasePredictor

__author__ = "Feyi Adesanya"


class Reconstructor:
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

    # Reconstruction (called by Coordinator on absence)
    def reconstruct(self, expected_ts: float) -> Event:
        """
        Reconstruct a missing event at the given expected timestamp and publish it to the EventStream.
        """
        prediction = self.predictor.predict()
        confidence = self.predictor.confidence()

        reconstructed = make_event(
            type="simulated",
            src=self.source_id,
            event_status="reconstructed",
            value=prediction,
            event_ts=expected_ts,
            confidence=confidence,
            extras={
                "reconstruction_method": self.predictor.name,
                "reconstruction_time": time.time(),
            },
        )

        self.event_stream.add_event(
            reconstructed,
            partition="reconstructed",
            source_id=self.source_id,
        )

        logging.debug(
            f"[RECONSTRUCTOR-{self.source_id}] Reconstructed event "
            f"at {expected_ts:.3f}"
        )

        return reconstructed