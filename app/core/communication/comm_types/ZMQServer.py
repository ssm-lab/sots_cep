import zmq
import logging
from ..Server import Server

__author__ = "Feyi Adesanya"

class ZMQServer(Server):
    def __init__(self, pub_endpoint="tcp://*:5557", pull_endpoint="tcp://*:5558"):
        super().__init__()
        self.ctx = zmq.Context()
        self._publisher = self.ctx.socket(zmq.PUB)
        self._publisher.bind(pub_endpoint)

        self._collector = self.ctx.socket(zmq.PULL)
        self._collector.bind(pull_endpoint)

        self._poller = zmq.Poller()
        self._poller.register(self._collector, zmq.POLLIN)

    def _loop(self):
        logging.info("[ZMQServer] Server started.")
        self._running = True
        try:
            while self._running:
                try:
                    items = dict(self._poller.poll(1000))
                except zmq.ZMQError as e:
                    # If context was terminated during shutdown
                    if not self._running:
                        break
                    logging.error(f"[ZMQServer] Poll error: {e}")
                    break

                if self._collector in items:
                    try:
                        message = self._collector.recv_multipart(flags=zmq.NOBLOCK)
                    except zmq.ZMQError as e:
                        if not self._running:
                            break
                        logging.error(f"[ZMQServer] Recv error: {e}")
                        continue

                    if len(message) < 2:
                        logging.warning(f"[ZMQServer] Malformed message: {message}")
                        continue
                    try:
                        self._publisher.send_multipart(message)
                    except zmq.ZMQError as e:
                        if not self._running:
                            break
                        logging.error(f"[ZMQServer] Send error: {e}")
                        continue
        finally:
            logging.info("[ZMQServer] Loop exiting.")


    def _cleanup(self):
        logging.info("[ZMQServer] Cleaning up sockets and context.")
        try:
            self._publisher.close(0)
            self._collector.close(0)
            self.ctx.term()
        except Exception as e:
            logging.warning(f"[ZMQServer] Error during cleanup: {e}")
