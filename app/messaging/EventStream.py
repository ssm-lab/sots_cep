import logging
from app.schema.Event import Event, EventConsumer
from app.messaging.StreamClient import StreamClient


class EventStream:
    def __init__(self):
        self.partitions = {
            "observed": StreamClient("observed"),
            "imputed": StreamClient("imputed"),
            "matched": StreamClient("matched"),
        }

    def add_event(self, event: Event, partition: str, stream_id: str):
        if partition not in self.partitions:
            raise ValueError(f"Unknown partition: {partition}")
        logging.debug(f"[EVENTSTREAM] Adding event to partition={partition}, stream_id={stream_id}: {event}")
        self.partitions[partition].publish(event, stream_id)

    def subscribe(self, consumer: EventConsumer, partition: str, stream_id: str):
        if partition not in self.partitions:
            raise ValueError(f"Unknown partition: {partition}")
        self.partitions[partition].subscribe_to(stream_id, consumer)

    def dispatch_once(self, timeout: int = 1000):
        if not self._running:
            return False

        for client in self.partitions.values():
            client.dispatch_once(timeout=timeout)
        return True

    def dispatch_forever(self, timeout: int = 1000):
        self._running = True
        while self._running:
            self.dispatch_once(timeout=timeout)

    def stop(self):
        logging.info("[EVENTSTREAM] Shutting down.")
        self._running = False