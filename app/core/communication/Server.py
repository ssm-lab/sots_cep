from abc import ABC, abstractmethod

class Server(ABC):
    """Abstract base class for a messaging server backend."""

    @abstractmethod
    def run(self):
        """Main loop for receiving and redistributing messages."""
        pass

    @abstractmethod
    def stop(self):
        """Stop the server gracefully and clean up resources."""
        pass
