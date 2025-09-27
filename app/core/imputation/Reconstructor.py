import time
import logging
from ..runtime.EventStream import EventStream
from ..schema.Event import Event
from .predictors.predictorTypes.BasePredictor import BasePredictor
from ..runtime.EventConsumer import EventConsumer


class Reconstructor(EventConsumer):
    """
    Takes an observed event, applies predictor, and returns a new imputed/observed event.
    """
    def __init__(self, stream_id: str, predictor: BasePredictor, event_stream: EventStream):
        self.stream_id = stream_id
        self.predictor = predictor
        self.event_stream = event_stream

    def consume_event(self, event: Event) -> Event:
        logging.debug(f"[RECONSTRUCTOR-{self.stream_id}] Processing event: {event}")
        observed_value = event.get("value")

        try:
            prediction = self.predictor.predict()
        except Exception as e:
            logging.error(f"[RECONSTRUCTOR-{self.stream_id}] Predictor.predict() failed: {e}")
            prediction = None

        if observed_value is not None:
            try:
                prediction = self.predictor.update(observed_value)
            except Exception as e:
                logging.error(f"[RECONSTRUCTOR-{self.stream_id}] Predictor.update() failed: {e}")

        # Step 3: construct the reconstructed event
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

