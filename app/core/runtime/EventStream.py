import logging
from typing import Type
from app.core.runtime.EventConsumer import EventConsumer
from app.core.schema.Event import Event
from app.core.communication.Client import Client

__author__ = "Feyi Adesanya"

class EventStream:
    """
    Core event bus for the system.
    Handles publish/subscribe of events across partitions and streams.
    Uses a pluggable MessagingClient backend (e.g., ZMQClient, KafkaClient).
    """

    def __init__(self, client_type: Type[Client]):
        # dict[partition -> dict[stream_id -> Client]]
        self.partitions: dict[str, dict[str, Client]] = {
            "observed": {},
            "reconstructed": {},
        }
        self.client_type = client_type
        self._running = False

    def _get_client(self, partition: str, stream_id: str) -> Client:
        if partition not in self.partitions:
            raise ValueError(f"Unknown partition: {partition}")
        if stream_id not in self.partitions[partition]:
            self.partitions[partition][stream_id] = self.client_type(partition=partition)
        return self.partitions[partition][stream_id]

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
            for partition_clients in self.partitions.values():
                for client in partition_clients.values():
                    client.dispatch(timeout=timeout)
            if once:
                break

    def stop(self):
        logging.info("[EVENTSTREAM] Stopping dispatch loop.")
        self._running = False
