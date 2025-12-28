import logging
import threading
import time
from typing import Dict
import heapq
from dataclasses import dataclass, field

from ..schema.Event import Event
from ..reconstruction.Reconstructor import Reconstructor
from ..utils.UtilsFuncs import _load_json
from ..runtime.EventConsumer import EventConsumer

__author__ = "Feyi Adesanya"


# Scheduler
class ExpectedSchedule:
    def __init__(
        self,
        interval: float,
        start_ts: float | None = None,
        grace: float = 0.1,
    ):
        now = time.time()
        self.interval = interval
        self.next_ts = start_ts or (now + interval)
        self.grace = grace

    def advance(self):
        self.next_ts += self.interval

    def is_missed(self, now: float) -> bool:
        return now > self.next_ts + self.grace


class Coordinator(EventConsumer):
    """
    Consumes observed events via EventStream callbacks,
    tracks expected schedules per source,
    and triggers reconstruction on absence.
    """

    def __init__(
        self,
        *,
        event_stream,
        sources_config_path: str,
        predictors_config_path: str,
        check_interval: float = 0.05,
    ):
        self.event_stream = event_stream
        self.sources_cfg = _load_json(sources_config_path)
        self.predictors_cfg = _load_json(predictors_config_path)

        self.schedules: Dict[str, ExpectedSchedule] = {}
        self.reconstructors: Dict[str, Reconstructor] = {}

        self._running = False
        self._thread: threading.Thread | None = None
        self.check_interval = check_interval

        self._setup()


    def _setup(self):
        for source_id, cfg in self.sources_cfg.items():
            interval = cfg.get("interval", 1.0)
            grace = cfg.get("grace", 0.1)

            self.schedules[source_id] = ExpectedSchedule(
                interval=interval,
                grace=grace,
            )

            predictor = self._build_predictor(cfg["predictor_template"])
            reconstructor = Reconstructor(
                source_id=source_id,
                predictor=predictor,
                event_stream=self.event_stream,
            )
            self.reconstructors[source_id] = reconstructor

            self.event_stream.subscribe(
                consumer=self,
                partition="observed",
                source_id=source_id,
            )

            logging.info(f"[COORDINATOR] Subscribed to observed.{source_id}")

    def _build_predictor(self, template_name: str):
        from ..reconstruction.PredictorRegistry import get_predictor_class

        cfg = self.predictors_cfg[template_name]
        cls = get_predictor_class(cfg["type"])
        return cls(**cfg.get("params", {}))



    def consume_event(self, event: Event) -> None:
        """
        Observed event advances the expected schedule for its source.
        """
        try:
            source_id = event["src"]
            ts = event.get("event_ts", time.time())
        except Exception:
            logging.warning("[COORDINATOR] Malformed event received")
            return

        schedule = self.schedules.get(source_id)
        if not schedule:
            return

        # Advance schedule until expectation is after the observation
        while ts >= schedule.next_ts:
            schedule.advance()

        # Update predictor state
        reconstructor = self.reconstructors.get(source_id)
        if reconstructor:
            reconstructor.handle_observed(event)

        logging.debug(
            f"[COORDINATOR] Observed event from {source_id} at {ts:.3f}, "
            f"next expected at {schedule.next_ts:.3f}"
        )

    def _monitor_loop(self):
        self._running = True
        logging.info("[COORDINATOR] monitor started")

        while self._running:
            now = time.time()

            for source_id, schedule in self.schedules.items():
                if schedule.is_missed(now):
                    expected_ts = schedule.next_ts

                    logging.debug(
                        f"[COORDINATOR] Missing event from {source_id} "
                        f"(expected at {expected_ts:.3f})"
                    )

                    reconstructor = self.reconstructors.get(source_id)
                    if reconstructor:
                        reconstructor.reconstruct(expected_ts)

                    schedule.advance()

            if not self.schedules:
                time.sleep(0.1)
                continue

            # Sleep until next deadline
            now = time.time()
            next_deadline = min(
                schedule.next_ts + schedule.grace
                for schedule in self.schedules.values()
            )

            sleep_for = max(0.0, next_deadline - now)
            sleep_for = min(sleep_for, 0.5)

            time.sleep(sleep_for)

        logging.info("[COORDINATOR] monitor stopped")


    # Lifecycle
    def start(self):
        if self._running:
            return
        self._thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True,
            name="coordinator-monitor",
        )
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=1.0)
            self._thread = None
        logging.info("[COORDINATOR] Shutting down...")