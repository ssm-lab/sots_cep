from abc import ABC, abstractmethod

__author__ = "Istvan David"
__copyright__ = "Copyright 2021, GEODES"
__credits__ = "Eugene Syriani"
__modified__ = "Feyi Adesanya"
__license__ = "GPL-3.0"

class Client(ABC):
    """
    Abstract base for messaging clients.

    Provides publish/subscribe and dispatch of events on a specific partition.
    """
    def __init__(self, partition: str):
        self.partition = partition
        self._running = False

    @abstractmethod
    def publish(self, event: dict, stream_id: str):
        """Publish an event to a specific stream."""
        pass

    @abstractmethod
    def subscribe_to(self, stream_id: str, consumer):
        """Subscribe a consumer to a specific stream or wildcard (*)"""
        pass

    @abstractmethod
    def dispatch(self, timeout: int = 1000):
        """Poll for new events and forward them to consumers."""
        pass

    @abstractmethod
    def close(self):
        pass

    def stop(self):
        if self._running:
            self._running = False
            self.close()
