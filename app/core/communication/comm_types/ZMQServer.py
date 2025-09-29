import zmq
import logging
from ..Server import Server

class ZMQServer(Server):
    def __init__(self, pub_endpoint="tcp://*:5557", pull_endpoint="tcp://*:5558"):
        self.ctx = zmq.Context()
        
        # Publisher side (PUB for subscribers to connect)
        self._publisher = self.ctx.socket(zmq.PUB)
        self._publisher.bind(pub_endpoint)

        # Collector side (PULL for clients to push into)
        self._collector = self.ctx.socket(zmq.PULL)
        self._collector.bind(pull_endpoint)

        # Poller for non-blocking wait
        self._poller = zmq.Poller()
        self._poller.register(self._collector, zmq.POLLIN)

        self._running = False

    def run(self):
        logging.info("[ZMQServer] Running.")
        self._running = True
        try:
            while self._running:
                items = dict(self._poller.poll(1000))
                if self._collector in items:
                    message = self._collector.recv_multipart()
                    if len(message) < 2:
                        logging.warning(f"[ZMQServer] Malformed message: {message}")
                        continue
                    self._publisher.send_multipart(message)
        except KeyboardInterrupt:
            logging.info("[ZMQServer] Interrupted by user.")
        finally:
            self.stop()

    def stop(self):
        logging.info("[ZMQServer] Shutting down.")
        self._running = False
        self._publisher.close()
        self._collector.close()
        self.ctx.term()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("-log", "--log", default="info")
    args = parser.parse_args()

    logging.basicConfig(format="[%(levelname)s] %(message)s", level=getattr(logging, args.log.upper()))

    server = ZMQServer()
    server.run()
