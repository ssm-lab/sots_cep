from abc import ABC, abstractmethod

class Client(ABC):
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
