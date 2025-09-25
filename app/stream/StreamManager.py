import logging
import threading
import time
from typing import Dict, Any, Optional

from ..stream.StreamTypes import *
from ..stream.StreamRegistry import get_stream_class
from ..schema.Event import Event
from ..helper.Helper import _load_json


class TickScheduler:
    def __init__(self, interval: float, start_epoch: Optional[float] = None, grace: float = 0.1):
        now = time.time()
        self.interval = interval
        self.next_tick = start_epoch or (now + interval)
        self.grace = grace  # leeway in seconds

    def wait_next(self) -> float:
        now = time.time()
        sleep_for = self.next_tick - now
        if sleep_for > 0:
            time.sleep(sleep_for)

        tick_ts = self.next_tick
        self.next_tick += self.interval
        return tick_ts

    def stamp(self, event: Event, scheduled_ts: float) -> Event:
        if isinstance(event, dict):
            event["timestamp"] = scheduled_ts
        else:
            setattr(event, "timestamp", scheduled_ts)
        return event


class StreamManager:
    def __init__(self, event_stream, streams_config_path: str):
        self.event_stream = event_stream
        self.streams_config = _load_json(streams_config_path)

        self.streams: Dict[str, Any] = {}
        self.threads: Dict[str, threading.Thread] = {}
        self.schedulers: Dict[str, TickScheduler] = {}
        self.running = False

    def _create_stream(self, stream_id: str, cfg: dict):
        cls = get_stream_class(cfg.get("type", "simulated"))
        return cls(stream_id=stream_id, **cfg)

    def _publish(self, stream_id: str, event: Event) -> None:
        try:
            event.setdefault("source", self.streams[stream_id].__class__.__name__)
            self.event_stream.add_event(event, "observed", stream_id)
        except Exception as e:
            logging.exception(f"[STREAM-MANAGER] Failed to publish event for {stream_id}: {e}")

    def _make_missing(self, stream_id: str, scheduled_ts: float) -> dict:
        stream = self.streams[stream_id]
        return {
            "stream_id": stream_id,
            "timestamp": scheduled_ts,
            "value": None,
            "unit": getattr(stream, "unit", None),
            "datatype": getattr(stream, "datatype", None),
            "status": "missing",
            "extra": {"ground_truth": getattr(stream, "last_truth", None)},
        }

    def _run_stream(self, stream_id: str, scheduler: TickScheduler, stream) -> None:
        """Main loop for one stream: publish real or missing events each tick."""
        while self.running:
            scheduled_ts = scheduler.wait_next()
            try:
                event = stream.generate_event()
            except TimeoutError:
                missing_event = self._make_missing(stream_id, scheduled_ts)
                self._publish(stream_id, missing_event)
            except Exception as e:
                logging.exception(f"[STREAM-MANAGER] Error in stream {stream_id}: {e}")
            else:
                stamped_event = scheduler.stamp(event, scheduled_ts)
                self._publish(stream_id, stamped_event)



    def start(self) -> None:
        if self.running:
            logging.info("[STREAM-MANAGER] Already running")
            return
        self.running = True

        for stream_id, cfg in self.streams_config.items():
            stream = self._create_stream(stream_id, cfg)
            interval = getattr(stream, "interval", None) or cfg.get("interval", 1.0)

            scheduler = TickScheduler(interval)
            self.streams[stream_id] = stream
            self.schedulers[stream_id] = scheduler

            t = threading.Thread(
                target=self._run_stream,
                args=(stream_id, scheduler, stream),
                daemon=True,
                name=f"stream-{stream_id}",
            )
            self.threads[stream_id] = t
            t.start()
            logging.info(f"[STREAM-MANAGER] Started {stream_id} interval={interval:.1f}s")

    def stop(self, join_timeout: float = 2.0) -> None:
        if not self.running:
            return
        self.running = False

        for sid, t in self.threads.items():
            try:
                t.join(timeout=join_timeout)
            except Exception:
                logging.exception(f"[STREAM-MANAGER] Failed to join {sid}")

        for s in self.streams.values():
            try:
                if hasattr(s, "close"):
                    s.close()
            except Exception:
                logging.exception("[STREAM-MANAGER] Error closing stream")

        logging.info("[STREAM-MANAGER] All streams stopped")
