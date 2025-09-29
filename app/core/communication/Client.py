from abc import ABC, abstractmethod

class Client(ABC):
    """Abstract base class for a messaging client backend."""

    @abstractmethod
    def publish(self, event, stream_id: str):
        """Publish an event to a given stream."""
        pass

    @abstractmethod
    def subscribe_to(self, stream_id: str, consumer):
        """Subscribe a consumer to a given stream."""
        pass

    @abstractmethod
    def dispatch(self, timeout: int = 1000):
        """Dispatch incoming messages to subscribed consumers."""
        pass

    @abstractmethod
    def close(self):
        """Close sockets, release resources."""
        pass
