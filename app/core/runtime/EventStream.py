import logging
from ..schema.Event import Event
from .EventConsumer import EventConsumer
from ..communication.Client import Client

"""
EventStream: Core event bus for the system.
Handles publish/subscribe of events across partitions and streams.
Partitions are explicitly declared; each (partition, stream_id) gets its own Client.
"""

class EventStream:
    def __init__(self, valid_partitions=("observed", "reconstructed")):
        # dict[partition -> dict[stream_id -> Client]]
        self.partitions: dict[str, dict[str, Client]] = {
            "observed": {}, 
            "reconstructed": {},
        }
        self._running = False

    def _get_client(self, partition: str, stream_id: str) -> Client:
        if partition not in self.partitions:
            raise ValueError(f"[EVENTSTREAM] Invalid partition: {partition}")
        streams = self.partitions[partition]
        if stream_id not in streams:
            streams[stream_id] = Client(partition)
            logging.debug(f"[EVENTSTREAM] Created new client for {partition}.{stream_id}")
        return streams[stream_id]

    def add_event(self, event: Event, partition: str, stream_id: str):
        client = self._get_client(partition, stream_id)
        logging.debug(f"[EVENTSTREAM] Adding event to {partition}.{stream_id}: {event}")
        client.publish(event, stream_id)

    def subscribe(self, consumer: EventConsumer, partition: str, stream_id: str):
        client = self._get_client(partition, stream_id)
        client.subscribe_to(stream_id, consumer)

    def dispatch(self, timeout: int = 1000, once: bool = False):
        self._running = True
        while self._running:
            for streams in self.partitions.values():
                for client in streams.values():
                    client.dispatch(timeout=timeout)
            if once:
                break

    def stop(self):
        logging.info("[EVENTSTREAM] Stopping dispatch loop.")
        self._running = False
