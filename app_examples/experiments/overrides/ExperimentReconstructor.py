import time

from app.core.compensator.Reconstructor import Reconstructor
from app.core.schema.Event import make_event


class ExperimentalExpectedSchedule:

    def __init__(self, interval, clock=None, grace=0.1):
        self.interval = interval
        self.clock = clock
        self.grace = grace

        now = self.clock.now() if self.clock else time.time()
        self.next_ts = now + interval

    def advance(self):
        self.next_ts += self.interval

    def is_missed(self, now):
        return now > self.next_ts + self.grace


class ExperimentReconstructor(Reconstructor):

    def __init__(self, *, clock=None, schedule=None, **kwargs):

        # Replace schedule with experimental version
        if schedule is not None:
            schedule = ExperimentalExpectedSchedule(
                interval=schedule.interval,
                clock=clock,
                grace=schedule.grace if hasattr(schedule, "grace") else 0.1
            )

        super().__init__(schedule=schedule, **kwargs)

        self.clock = clock
        self.last_observed_ts = None
        self._running = False

        try:
            self._last_prediction = float(self.predictor.kf.x[0, 0])
        except Exception:
            self._last_prediction = None

    # ----------------------------------------

    def start(self):
        pass

    # ----------------------------------------

    def step(self):
        now = self.clock.now() if self.clock else time.time()

        while self.schedule.is_missed(now):
            expected_ts = int(self.schedule.next_ts)

            self._last_prediction = self.predictor.predict()

            if self.last_observed_ts is None:
                self.schedule.advance()
                continue

            if self.last_observed_ts >= expected_ts:
                self.schedule.advance()
                continue

            if self.allow_reconstruct and self._last_prediction is not None:
                self.reconstruct(expected_ts)

            self.schedule.advance()

    # ----------------------------------------

    def consume_event(self, event):

        ts = event.get(
            "event_ts",
            self.clock.now() if self.clock else time.time()
        )

        self.last_observed_ts = ts
        value = event["value"]

        if self.allow_observe:
            confidence = self.predictor.confidence(observed_value=value)
            self.predictor.update(value)

    # ----------------------------------------

    def reconstruct(self, expected_ts):
        confidence = self.predictor.confidence()

        self.emit_event({
            "prediction": self._last_prediction,
            "expected_ts": expected_ts,
            "confidence": confidence
        })

    # ----------------------------------------

    def generate_event(self, event_params):

        return make_event(
            type="simulated",
            src=self.source_id,
            event_status="reconstructed",
            value=event_params["prediction"],
            event_ts=event_params["expected_ts"],
            confidence=event_params["confidence"],
            extras={
                "reconstruction_method": getattr(self.predictor, "name", "predictor"),
                "reconstruction_time": self.clock.now() if self.clock else time.time()
            }
        )