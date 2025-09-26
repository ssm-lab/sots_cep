import logging
from ..schema.Event import Event
from .EventConsumer import EventConsumer
from ..messaging.Client import Client

class EventStream:
    def __init__(self):
        self.partitions = {
            "observed": Client("observed"),
            "reconstructed": Client("reconstructed"),
            "matched": Client("matched"),
            "late": Client("late"),
            "groundtruth": Client("groundtruth"),
        }
        self._running = False

    def add_event(self, event: Event, partition: str, stream_id: str):
        if partition not in self.partitions:
            raise ValueError(f"Unknown partition: {partition}")
        logging.debug(f"[EVENTSTREAM] Adding event to {partition}.{stream_id}: {event}")
        self.partitions[partition].publish(event, stream_id)

    def subscribe(self, consumer: EventConsumer, partition: str, stream_id: str):
        if partition not in self.partitions:
            raise ValueError(f"Unknown partition: {partition}")
        self.partitions[partition].subscribe_to(stream_id, consumer)

    def dispatch(self, timeout: int = 1000, once: bool = False):
        self._running = True
        while self._running:
            for client in self.partitions.values():
                client.dispatch(timeout=timeout)
            if once:
                break

    def stop(self):
        logging.info("[EVENTSTREAM] Stopping dispatch loop.")
        self._running = False
