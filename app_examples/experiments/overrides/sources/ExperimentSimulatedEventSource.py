import logging
import random
import numpy as np

from app.core.source.EventSourceRegistry import register_source_type
from app_examples.experiments.overrides.ExperimentEventSource import ExperimentEventSource

@register_source_type("simulated_experiment")
class SimulatedEventSource(ExperimentEventSource):

    def __init__(
        self,
        *,
        id,
        type,
        stream,
        lifecycle,
        value_unit=None,
        value_datatype="scalar",
        interval=1.0,
        min_value=0.0,
        max_value=100.0,
        drift=0.05,
        noise=0.5,
        start_value=None,
        seed=42,
    ):
        super().__init__(id=id, type=type, stream=stream, lifecycle=lifecycle)

        self.interval = interval
        self.min_value = min_value
        self.max_value = max_value
        self.drift = drift
        self.noise = noise

        self.value_unit = value_unit
        self.value_datatype = value_datatype

        self.rng = np.random.default_rng(seed)

        self.current_value = (
            start_value if start_value is not None
            else random.uniform(min_value, max_value)
        )

        self.signal = self._generate_signal(length=500)
        self.scenario = None
        self.clock = None

    def override_observation(self, scenario, clock):
        self.scenario = scenario
        self.clock = clock
        
    def _generate_signal(self, length=500):
        signal = np.zeros(length)
        signal[0] = self.current_value

        for t in range(1, length):
            step = self.rng.normal(0, self.noise)
            signal[t] = signal[t-1] + step
            signal[t] = np.clip(signal[t], self.min_value, self.max_value)

        return signal
    
    def step(self, now):
        if now >= len(self.signal):
            return None

        true_value = float(self.signal[int(now)])

        # Ground truth (always emitted)
        self.emit_ground_truth({
            "value": true_value,
            "event_ts": now,
            "value_unit": self.value_unit,
            "confidence": 1.0,
            "value_datatype": self.value_datatype,
            "extras": {}
        })

        if now % self.interval != 0:
            return None

        observed_value = true_value

        if self.scenario:
            observed_value = self.scenario.get_observation(
                now, true_value, self.id
            )

        if observed_value is None:
            logging.debug(f"[SOURCE {self.id}] DROPPED at t={now}")
            return None

        logging.debug(f"[SOURCE {self.id}] Observed emit at t={now}")

        return self.emit_event({
            "value": observed_value,
            "event_ts": now,
            "confidence": 1.0,
            "value_unit": self.value_unit,
            "value_datatype": self.value_datatype,
            "extras": {}
        })