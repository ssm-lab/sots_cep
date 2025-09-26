import logging
import threading
import time
from typing import Dict, Any, Optional

from ..stream.StreamTypes import *
from ..stream.StreamRegistry import get_stream_class
from ..schema.Event import Event, make_event
from ..helper.Helper import _load_json


class TickScheduler:
    def __init__(self, interval: float, start_epoch: Optional[float] = None, grace: float = 0.1):
        now = time.time()
        self.interval = interval
        self.next_tick = start_epoch or (now + interval)
        self.grace = grace  # seconds of leeway

    def wait_next(self) -> tuple[float, str]:
        now = time.time()
        sleep_for = self.next_tick - now
        if sleep_for > 0:
            time.sleep(sleep_for)

        event_time = self.next_tick
        self.next_tick += self.interval
        return event_time


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

    def _publish(self, stream_id: str, event: Event, partition: str = "observed") -> None:
        try:
            self.event_stream.add_event(event, partition, stream_id)
        except Exception as e:
            logging.exception(f"[STREAM-MANAGER] Failed to publish {partition} event for {stream_id}: {e}")

    def _run_stream(self, stream_id: str, scheduler: TickScheduler, stream) -> None:
        """Main loop for one stream: publish observed/missing/late all normalized to tick slots."""
        while self.running:
            event_time = scheduler.wait_next()

            try:
                raw = stream.generate_event()  # user-defined source
                value = raw.get("value", None)
                sampled_ts = raw.get("sampled_ts", event_time)
                extras = raw.get("extras", {})  # always forward
            except TimeoutError:
                # Missing event (still attach any extras the stream may have)
                event = make_event(
                    stream_id,
                    value=None,
                    unit=getattr(stream, "unit", None),
                    datatype=getattr(stream, "datatype", None),
                    sampled_ts=event_time,
                    status="missing",
                    source=stream.__class__.__name__,
                    extras= {},
                )
                self._publish(stream_id, event, partition="observed")
                continue
            except Exception as e:
                logging.exception(f"[STREAM-MANAGER] Error in stream {stream_id}: {e}")
                continue

            # Observed event
            event = make_event(
                stream_id,
                value=value,
                unit=getattr(stream, "unit", None),
                datatype=getattr(stream, "datatype", None),
                sampled_ts=sampled_ts,
                status="observed",
                source=stream.__class__.__name__,
                extras=extras,
            )

            # Late detection - future work could be re-intializing predictor using recent history to help align it when events come late
            is_late = abs(sampled_ts - event_time) > scheduler.grace
            if is_late:
                self._publish(stream_id, event, partition="late")
                logging.warning(
                    f"[STREAM-MANAGER] Late event for {stream_id} sampled={sampled_ts:.3f} tick={event_time:.3f}"
                )
            else:
                self._publish(stream_id, event, partition="observed")


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