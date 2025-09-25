import logging
import threading
import time
from app.stream.StreamRegistry import get_stream_class
from app.schema.Event import Event
from app.helper.Helper import _load_json

class StreamManager:
    def __init__(self, event_stream, streams_config_path: str):
        self.event_stream = event_stream
        self.streams_config = _load_json(streams_config_path)
        self.streams = {}
        self.threads = {}
        self.running = False

    def _create_stream(self, stream_id: str, cfg: dict):
        stream_type = cfg.get("type", "simulated")
        cls = get_stream_class(stream_type)
        return cls(stream_id=stream_id, **cfg)

    def _run_stream(self, stream_id: str, interval: float):
        stream = self.streams[stream_id]
        while self.running:
            event: Event = stream.generate_event()
            logging.debug(f"[STREAM-MANAGER] Generated event from {stream_id}: {event}")
            self.event_stream.add_event(event, "observed", stream_id)
            time.sleep(interval)

    def start(self):
        self.running = True
        for stream_id, cfg in self.streams_config.items():
            stream = self._create_stream(stream_id, cfg)
            self.streams[stream_id] = stream
            interval = cfg.get("interval", 1.0)
            thread = threading.Thread(
                target=self._run_stream, args=(stream_id, interval), daemon=True
            )
            self.threads[stream_id] = thread
            thread.start()
            logging.info(f"[STREAM-MANAGER] Started {stream_id} with interval={interval}s")

    def stop(self):
        self.running = False
        for t in self.threads.values():
            t.join()
        logging.info("[STREAM-MANAGER] All streams stopped")
