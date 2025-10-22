import copy
import time
import logging
from ..runtime.EventStream import EventStream
from ..schema.Event import Event
from .predictor_types.BasePredictor import BasePredictor
from ..runtime.EventConsumer import EventConsumer

__author__ = "Feyi Adesanya"

class Reconstructor(EventConsumer):
    """
    Wraps a predictor to impute missing data.
    Subscribes to observed events for a stream and publishes
    reconstructed events back on the EventStream.
    """
    
    def __init__(self, stream_id: str, predictor: BasePredictor, event_stream: EventStream):
        self.stream_id = stream_id
        self.predictor = predictor
        self.event_stream = event_stream

    def consume_event(self, event: Event):
        """Consume an observed event and appends data on imputation."""
        logging.debug(f"[RECONSTRUCTOR-{self.stream_id}] Processing event: {event}")
        observed_value = event.get("value")

        prediction = self.predictor.predict()
        prediction = self.predictor.update(observed_value)

        processed: Event = copy.deepcopy(event)
        processed.update({
            "value": observed_value,
            "confidence": 1.0,
            "status": "reconstructed",
            "reconstructed_value": prediction,
            "reconstructed_confidence": self.predictor.confidence(observed_value=observed_value),
            "reconstruction_flag": False,
            "reconstruction_method": self.predictor.name,
            "reconstruction_time": time.time(),
            })

        self.event_stream.add_event(processed, "reconstructed", self.stream_id)
        return processed
    
    def handle_timeout(self, event: Event):
        """Reconstruct an event when a timeout (gap) occurs."""
        logging.debug(f"[RECONSTRUCTOR-{self.stream_id}] handling timeout, reconstructing missing event")
        prediction = self.predictor.predict()

        processed: Event = copy.deepcopy(event)
        processed.update({
            "value": prediction,
            "confidence": self.predictor.confidence(),
            "status": "reconstructed",
            "reconstructed_value": prediction,
            "reconstructed_confidence": self.predictor.confidence(),
            "reconstruction_flag": True,
            "reconstruction_method": self.predictor.name,
            "reconstruction_time": time.time(),
        })

        self.event_stream.add_event(processed, "reconstructed", self.stream_id)


    def advance_without_event(self):
        self.predictor.predict()