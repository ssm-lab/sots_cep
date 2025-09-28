import time
import logging
from ..runtime.EventStream import EventStream
from ..schema.Event import Event
from .predictor_types.BasePredictor import BasePredictor
from ..runtime.EventConsumer import EventConsumer

"""
Reconstructor: Wraps a predictor for imputing missing data.
Subscribes to observed events for one stream.
Publishes reconstructed events back to the EventStream.
"""

class Reconstructor(EventConsumer):
    def __init__(self, stream_id: str, predictor: BasePredictor, event_stream: EventStream):
        self.stream_id = stream_id
        self.predictor = predictor
        self.event_stream = event_stream

    def consume_event(self, event: Event):
        logging.debug(f"[RECONSTRUCTOR-{self.stream_id}] Processing event: {event}")
        observed_value = event.get("value")

        prediction = self.predictor.predict()
        if observed_value is not None:
            prediction = self.predictor.update(observed_value)

        processed: Event = {**event}
        processed.update({
            "value": observed_value if observed_value is not None else prediction,
            "reconstructed_value": prediction,
            "reconstruction_flag": observed_value is None,
            "origin": "reconstructed",
            "status": "reconstructed" if event.get("status") == "missing" else "observed",
            "reconstruction_method": (
                self.predictor.name if observed_value is None else "observed"
            ),
            "confidence": (
                self.predictor.confidence() if observed_value is None else 1.0
            ),
            "reconstruction_time": time.time(),
        })

        self.event_stream.add_event(processed, "reconstructed", self.stream_id)
        return processed
    
    def handle_timeout(self, event: Event):
        logging.debug(f"[RECONSTRUCTOR-{self.stream_id}] handling timeout, reconstructing missing event")
        prediction = self.predictor.predict()

        processed: Event = {**event}
        processed.update({
            "value": prediction,
            "reconstructed_value": prediction,
            "reconstruction_flag": True,
            "origin": "reconstructed",
            "status": "reconstructed",
            "reconstruction_method": (
                self.predictor.name
            ),
            "confidence": (
                self.predictor.confidence()
            ),
            "reconstruction_time": time.time(),
        })

        self.event_stream.add_event(processed, "reconstructed", self.stream_id)


