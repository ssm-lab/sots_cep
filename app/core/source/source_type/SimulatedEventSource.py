import logging
import random
import time
import threading
from typing import Any, Optional

from ..EventSourceRegistry import register_source_type
from ..EventSource import EventSource
from ...runtime.EventStream import EventStream

__author__ = "Feyi Adesanya"


@register_source_type("simulated")
class SimulatedEventSource(EventSource):
    def __init__(
        self,
        *,
        id: str,
        type: str,
        stream: EventStream,
        lifecycle,

        value_unit: Optional[str] = None,
        value_datatype: str = "scalar",

        interval: float = 1.0,
        min_value: float = 15.0,
        max_value: float = 30.0,
        noise: float = 0.5,
        drop_chance: float = 0.1,
        mandatory_count: int = 1,
    ):
        super().__init__(id=id, type=type, stream=stream, lifecycle=lifecycle)

        self.interval = interval
        self.min_value = min_value
        self.max_value = max_value
        self.noise = noise
        self.drop_chance = drop_chance
        self.mandatory_count = mandatory_count

        self.value_unit = value_unit
        self.value_datatype = value_datatype

        self.baseline = (min_value + max_value) / 2

        self.generated_count = 0

        self._running = False
        self._thread: Optional[threading.Thread] = None


    def start(self) -> None:
        if self._running:
            return

        self._running = True

        self._thread = threading.Thread(
            target=self._run_loop,
            daemon=True
        )

        self._thread.start()

    def stop(self) -> None:
        self._running = False

        if self._thread:
            self._thread.join(timeout=1.0)
            self._thread = None

        logging.info(f"[EVENT SOURCE-{self.id}] stopped")

    def _run_loop(self) -> None:
        next_ts = time.time()

        while self._running:
            now = time.time()

            if now < next_ts:
                time.sleep(next_ts - now)
                continue

            next_ts += self.interval
            self._step(now)

    def _step(self, now: float) -> Optional[Any]:
        value = random.gauss(self.baseline, self.noise)

        value = max(self.min_value, min(value, self.max_value))

        self.generated_count += 1

        if self.generated_count > self.mandatory_count:
            if random.random() < self.drop_chance:
                logging.debug(
                    f"[EVENT SOURCE-{self.id}] skipping event at {now}"
                )
                return None

        return self.emit_event({
            "value": value,
            "event_ts": now,
            "confidence": 1.0,
            "value_unit": self.value_unit,
            "value_datatype": self.value_datatype,
            "extras": {
                "noise": value - self.baseline,
            },
        })