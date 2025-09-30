import logging
import threading
from abc import ABC, abstractmethod

__author__ = "Istvan David"
__copyright__ = "Copyright 2021, GEODES"
__credits__ = "Eugene Syriani"
__modified__ = "Feyi Adesanya"
__license__ = "GPL-3.0"

class Server(ABC):
    """
    Abstract base for messaging servers.

    Runs a loop to collect and publish messages between clients.
    """
     
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
        """Main server loop."""
        pass

    def stop(self):
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
        """Cleanup resources used."""
        pass

    def close(self):
        self.stop()