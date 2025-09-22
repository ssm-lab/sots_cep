import json
import logging
import threading
import time
from app.schema.Event import Event
from app.stream.Stream import SimulatedStream


class StreamManager:
    def __init__(self, event_stream, streams_config_path: str):
        self.event_stream = event_stream
        self.streams_config = self._load_json(streams_config_path)
        self.streams = {}
        self.threads = {}
        self.running = False

    def _load_json(self, path: str) -> dict:
        with open(path, "r") as f:
            return json.load(f)

    def _create_stream(self, stream_id: str, cfg: dict):
        return SimulatedStream(
            stream_id=stream_id,
            unit=cfg.get("unit", "unknown"),
            datatype=cfg.get("datatype", "float"),
            min_value=cfg.get("min", 0.0),
            max_value=cfg.get("max", 100.0),
        )

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
