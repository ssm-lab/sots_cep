import logging
import threading
from abc import ABC, abstractmethod


class Server(ABC):
    def __init__(self):
        self._running = False
        self._thread: threading.Thread | None = None
        self._closed = False

    def run(self, in_thread=False):
        """Start the server loop, optionally in a background thread."""
        if in_thread:
            self._thread = threading.Thread(target=self._loop, daemon=True)
            self._thread.start()
        else:
            self._loop()

    @abstractmethod
    def _loop(self):
        """Main server loop. Must be implemented by subclasses."""
        pass

    def stop(self):
        """Stop the server gracefully. Idempotent."""
        if self._closed:
            return
        self._closed = True

        if self._running:
            self._running = False

        try:
            self._cleanup()
        except Exception as e:
            logging.error(f"[{self.__class__.__name__}] Error during cleanup: {e}")

        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1)

    @abstractmethod
    def _cleanup(self):
        """Cleanup resources like sockets, contexts, etc."""
        pass

    def close(self):
        self.stop()