import logging
import threading
import time
from typing import Dict, List

from ..schema.Event import make_event
from ..stream.StreamRegistry import get_stream_class
from ..reconstruction.PredictorRegistry import get_predictor_class
from ..reconstruction.Reconstructor import Reconstructor
from ..utils.UtilsFuncs import _load_json

# Auto load registries
from ..reconstruction.predictor_types import *
from ..stream.stream_types import *

__author__ = "Feyi Adesanya"

class TickScheduler:
    def __init__(self, interval: float, start_epoch: float = None, grace: float = 0.1):
        now = time.time()
        self.interval = interval
        self.next_tick = start_epoch or (now + interval)
        self.grace = grace

    def wait_next(self) -> float:
        now = time.time()
        sleep_for = self.next_tick - now
        if sleep_for > 0:
            time.sleep(sleep_for)

        event_time = self.next_tick
        self.next_tick += self.interval
        return event_time


class Coordinator:
    """
    Central manager for streams and reconstructors.
    Builds components from configuration files.
    Manages scheduling and lifecycles of components.

    Parameters
    ----------
    event_stream : EventStream
        Shared event bus instance.
    streams_config_path : str
        Path to streams configuration JSON.
    predictors_config_path : str
        Path to filter configuration JSON.
    loggers : list, optional
        List of logger consumers to attach.
    """

    def __init__(self, event_stream, streams_config_path: str, predictors_config_path: str, loggers: List[object] = None):
        self.event_stream = event_stream
        self.streams_cfg = _load_json(streams_config_path)
        self.predictors_cfg = _load_json(predictors_config_path)

        self.streams: Dict[str, object] = {}
        self.schedulers: Dict[str, TickScheduler] = {}
        self.threads: Dict[str, threading.Thread] = {}
        self.reconstructors: Dict[str, Reconstructor] = {}

        self.loggers = loggers or []
        self.running = False

    # Build phase -----------------------
    def _build_stream(self, stream_id: str, cfg: dict):
        """Instantiate a stream from config with params support."""
        cls = get_stream_class(cfg.get("type", "simulated"))
        params = cfg.get("params", {})

        return cls(
            stream_id=stream_id,
            unit=cfg.get("unit"),
            datatype=cfg.get("datatype", "float"),
            interval=cfg.get("interval", 1.0),
            params = params
        )

    def _build_predictor(self, predictor_template: str):
        cfg = self.predictors_cfg.get(predictor_template)
        if cfg is None:
            raise ValueError(f"[COORDINATOR] Missing filter template '{predictor_template}'")
        cls = get_predictor_class(cfg["type"])
        return cls(**cfg.get("params", {}))

    def _build_reconstructor(self, stream_id: str, predictor):
        return Reconstructor(stream_id=stream_id, predictor=predictor, event_stream=self.event_stream)

    # Stream loop -----------------------
    def _run_stream(self, stream_id: str, scheduler: TickScheduler, stream):
        while self.running:
            event_time = scheduler.wait_next()
            try:
                raw = stream.generate_event()

                event = make_event(
                    stream_id,
                    value=raw.get("value"),
                    unit=getattr(stream, "unit", None),
                    datatype=getattr(stream, "datatype", None),
                    sampled_ts=raw.get("sampled_ts", event_time),
                    status="coordinated",
                    source=stream.__class__.__name__,
                    origin="source",
                    extras=raw.get("extras", {}),
                )
                self.event_stream.add_event(event, "observed", stream_id)

            # Fill in missing event
            except TimeoutError:
                logging.debug(f"[COORDINATOR] Timeout in {stream_id} at {event_time:.3f}")
                reconstructor = self.reconstructors.get(stream_id)
                if reconstructor:
                    missing_event = make_event(
                        stream_id,
                        value=None,
                        unit=getattr(stream, "unit", None),
                        datatype=getattr(stream, "datatype", None),
                        event_ts=event_time,
                        status="coordinated",
                        source=stream.__class__.__name__,
                        origin="missing",
                        extras={}
                    )
                    reconstructor.handle_timeout(missing_event)
                continue
            except Exception as e:
                logging.exception(f"[COORDINATOR] Error in {stream_id}: {e}")


    # Lifecycle -----------------------
    def start(self):
        """Start all streams and reconstructors."""
        if self.running:
            return
        self.running = True

        # Attach loggers
        for logger in self.loggers:
            for partition in list(self.event_stream.partitions.keys()):
                self.event_stream.subscribe(logger, partition, "*")
            logging.debug(f"[COORDINATOR] Subscribed logger {logger.__class__.__name__}")

        # Build streams + reconstructors
        for stream_id, cfg in self.streams_cfg.items():
            stream = self._build_stream(stream_id, cfg)
            interval = getattr(stream, "interval", None) or cfg.get("interval", 1.0)
            scheduler = TickScheduler(interval)

            self.streams[stream_id] = stream
            self.schedulers[stream_id] = scheduler

            predictor = self._build_predictor(cfg.get("predictor_template"))
            reconstructor = self._build_reconstructor(stream_id, predictor)
            self.reconstructors[stream_id] = reconstructor

            self.event_stream.subscribe(reconstructor, "observed", stream_id)

            t = threading.Thread(
                target=self._run_stream,
                args=(stream_id, scheduler, stream),
                daemon=True,
                name=f"stream-{stream_id}",
            )
            self.threads[stream_id] = t
            t.start()

            logging.debug(f"[COORDINATOR] Started {stream_id} interval={interval:.1f}s")

    def stop(self, join_timeout: float = 2.0):
        """Stop all streams and clean up resources."""
        self.running = False

        for sid, t in self.threads.items():
            try:
                t.join(timeout=join_timeout)
            except Exception:
                logging.exception(f"[COORDINATOR] Failed to join {sid}")

        for s in self.streams.values():
            if hasattr(s, "close"):
                try:
                    s.close()
                except Exception:
                    logging.exception("[COORDINATOR] Error closing stream")

        logging.info("[COORDINATOR] All stopped")
