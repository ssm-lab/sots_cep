import time
import logging
from app.schema.Event import Event, EventConsumer
from app.imputation.predictors.Predictor import BasePredictor


class Imputer(EventConsumer):
    """
    Consumes observed events, predicts and updates, and immediately publishes
    events to the EventStream.
    """
    def __init__(self, stream_id: str, predictor: BasePredictor, event_stream=None):
        self.stream_id = stream_id
        self.predictor = predictor
        self.current_prediction = None
        self.event_stream = event_stream

    def consume_event(self, event: Event):
        logging.debug(f"[IMPUTER-{self.stream_id}] Consuming event: {event}")
        observed_value = event.get("value")

        try:
            self.current_prediction = self.predictor.predict()
        except Exception as e:
            logging.error(f"[IMPUTER-{self.stream_id}] Predictor.predict() failed: {e}")
            self.current_prediction = None

        # If we got a real observation, update predictor
        if observed_value is not None:
            try:
                self.current_prediction = self.predictor.update(observed_value)
            except Exception as e:
                logging.error(f"[IMPUTER-{self.stream_id}] Predictor.update() failed: {e}")

        # Build an event passed with data from the predictor
        processed: Event = dict(event)
        processed["observed_value"] = observed_value

        if observed_value is None:
            processed["imputed_value"] = self.current_prediction
            processed["value"] = self.current_prediction
            processed["confidence"] = (
                self.predictor.confidence() if hasattr(self.predictor, "confidence") else 0.5
            )
            processed["method"] = self.predictor.name
        else:
            processed["imputed_value"] = None
            processed["value"] = observed_value
            processed["confidence"] = 1.0
            processed["method"] = "observed"
            processed["imputation_flag"] = False

        processed["extras"] = event.get("extras", {})
        processed["imputation_time"] = time.time()

        logging.debug(f"[IMPUTER-{self.stream_id}] Publishing processed event: {processed}")

        # immediately publish to eventstream
        if self.event_stream:
            self.event_stream.add_event(processed, "imputed", self.stream_id)
