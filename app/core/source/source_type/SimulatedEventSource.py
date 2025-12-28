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
    """
    Simulated sensor producing drifting noisy values with optional drops.
    """

    def __init__(
        self,
        *,
        id: str,
        type: str,
        stream: EventStream,

        value_unit: Optional[str] = None,
        value_datatype: str = "scalar",

        interval: float = 1.0,
        min_value: float = 15.0,
        max_value: float = 30.0,
        drift: float = 0.2,
        noise: float = 0.5,
        drop_chance: float = 0.1,
        mandatory_count: int = 3,
        start_value: Optional[float] = None,
    ):
        super().__init__(id=id, type=type, stream=stream)

        self.interval = interval
        self.min_value = min_value
        self.max_value = max_value
        self.drift = drift
        self.noise = noise
        self.drop_chance = drop_chance
        self.mandatory_count = mandatory_count

        self.value_unit = value_unit
        self.value_datatype = value_datatype

        self.current_value = (
            max(min_value, min(start_value, max_value))
            if start_value is not None
            else random.uniform(min_value, max_value)
        )

        self.generated_count = 0

        self._running = False
        self._thread: Optional[threading.Thread] = None


    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._thread:
            self._thread.join(timeout=1.0)
            self._thread = None
        logging.info("[EVENT SOURCE] Shutting down...")


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
        drift_step = random.uniform(-self.drift, self.drift)
        noise_step = random.gauss(0, self.noise)

        self.current_value += drift_step + noise_step
        self.current_value = max(
            self.min_value, min(self.current_value, self.max_value)
        )

        self.generated_count += 1

        # simulate dropouts (absence, not malformed events)
        if self.generated_count > self.mandatory_count:
            if random.random() < self.drop_chance:
                logging.debug(f"[EVENT SOURCE-{self.id}] SKIPPING EVENT for {now}")
                return None

        return self.emit({
            "value": self.current_value,
            "event_ts": now,
            "confidence": 1,
            "value_unit": self.value_unit,
            "value_datatype": self.value_datatype,
            "extras": {
                "drift": drift_step,
                "noise": noise_step,
            },
        })