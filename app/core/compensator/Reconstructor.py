import threading
import time
import logging
from collections import deque

from ..schema.EventConsumer import EventConsumer
from ..schema.EventGenerator import EventGenerator
from ..schema.Event import make_event
from ..utils.UtilsFuncs import _as_observer

class Reconstructor(EventConsumer, EventGenerator):

    """
    Reconstructor service responsible for compensating missing
    events using a predictor (e.g., Kalman filter).
    """

    def __init__(
        self,
        *,
        source_id,
        predictor,
        event_stream,
        lifecycle,
        schedule
    ):

        self.source_id = source_id
        self.predictor = predictor
        self.stream = event_stream
        self.lifecycle = lifecycle
        self.schedule = schedule

        self._running = False

        self.allow_observe = False
        self.allow_reconstruct = False

        self.stream.subscribe(self, "observed.*", self.source_id)

        self.confidence_threshold = 0.45
        self.conf_window = deque(maxlen=5)

    
    def connect(self):
        runtime = self.lifecycle.get_runtime(self.source_id)
        if runtime is None:
            raise ValueError(f"[RECONSTRUCTOR-{self.source_id}] runtime not found")
        runtime.emit_observed.subscribe(
            _as_observer(self._on_observe_changed)
        )
        runtime.enable_compensation.subscribe(
            _as_observer(self._on_reconstruct_changed)
        )
        logging.info(f"[RECONSTRUCTOR-{self.source_id}] connected to signals")

    def _on_observe_changed(self, value: bool):
        self.allow_observe = value

    def _on_reconstruct_changed(self, value: bool):
        self.allow_reconstruct = value

    def get_avg_confidence(self):
        return sum(self.conf_window) / len(self.conf_window) if self.conf_window else 1.0


    def generate_event(self, event_params):

        return make_event(
            type="simulated",
            src=self.source_id,
            event_status="reconstructed",
            value=event_params["prediction"],
            event_ts=event_params["expected_ts"],
            confidence=event_params["confidence"],
            extras={
                "interval": self.schedule.interval,
                "reconstruction_method": getattr(self.predictor, "name", "predictor"),
                "reconstruction_time": time.time()
            }
        )

    # --------------------------------

    def emit_event(self, event_params):

        event = self.generate_event(event_params)

        event["partition"] = "reconstructed"

        self.stream.add_event(
            event,
            "reconstructed",
            self.source_id
        )

        return event


    def consume_event(self, event):
        ts = event.get("event_ts", time.time())
        value = event["value"]

        logging.debug(
            f"[RECONSTRUCTOR-{self.source_id}] "
            f"value={value} "
            f"observe={self.allow_observe}"
        )
        
        if self.allow_observe:
            prediction = self.predictor.predict()
            confidence = self.predictor.confidence(observed_value=value)
            self.conf_window.append(confidence)
            logging.debug(f"{self.source_id} Confidence: {confidence} update with observed value {value} and estimate {self.predictor.kf.x[0, 0]}")
            self.predictor.update(value)
            
            


        while ts >= self.schedule.next_ts:
            self.schedule.advance()


    def start(self):

        if self._running:
            return

        self._running = True

        threading.Thread(
            target=self._monitor_loop,
            daemon=True,
            name=f"reconstructor-{self.source_id}"
        ).start()


    def _monitor_loop(self):

        while self._running:

            while self.schedule.is_missed(time.time()):

                logging.debug(
                    f"[RECONSTRUCTOR-{self.source_id}] "
                    f"missed event | reconstruct={self.allow_reconstruct}"
                )

                if self.allow_reconstruct:
                    self.reconstruct(self.schedule.next_ts)

                self.schedule.advance()

            time.sleep(0.05)


    def reconstruct(self, expected_ts):
        prediction = self.predictor.predict()
        confidence = self.predictor.confidence()
        self.conf_window.append(confidence)

        if self.get_avg_confidence() < self.confidence_threshold:
            logging.info(f"Running average confidence has exceeded limit: {confidence}")
            runtime = self.lifecycle.get_runtime(self.source_id)
            runtime.uncertainty_threshold_exceeded()
            logging.info("[RECONSTRUCTOR]-Uncertainty Threhold exceeded")
            return

        self.emit_event({
            "prediction": prediction,
            "expected_ts": expected_ts,
            "confidence": confidence
        })

        logging.info(
            f"[RECONSTRUCTION] {self.source_id} "
            f"prediction={prediction:.3f} "
            f"confidence={confidence:.3f} "
            f"at {expected_ts}"
        )