import time
import logging
from ..messaging.EventStream import EventStream
from ..schema.Event import Event
from ..imputation.predictors.predictorTypes.BasePredictor import BasePredictor


class Imputer:
    """
    Takes an observed event, applies predictor, and returns a new imputed/observed event.
    """
    def __init__(self, stream_id: str, predictor: BasePredictor, event_stream: EventStream):
        self.stream_id = stream_id
        self.predictor = predictor
        self.event_stream = event_stream

    def consume_event(self, event: Event) -> Event:
        logging.debug(f"[IMPUTER-{self.stream_id}] Processing event: {event}")
        observed_value = event.get("value")
        prediction = None

        try:
            if observed_value is None:
                prediction = self.predictor.predict()
            else:
                prediction = self.predictor.update(observed_value)
        except Exception as e:
            logging.error(f"[IMPUTER-{self.stream_id}] Predictor failed: {e}")

        processed: Event = {**event}
        processed.update({
            "value": prediction if observed_value is None else observed_value,
            "imputation_flag": observed_value is None,
            "status": "imputed" if event.get("status") == "missing" else "observed",
            "imputation_method": self.predictor.name if observed_value is None else "observed",
            "confidence": (
                self.predictor.confidence() if observed_value is None else 1.0
            ),
            "imputation_time": time.time(),
        })

        self.event_stream.add_event(processed, "imputed", self.stream_id)
