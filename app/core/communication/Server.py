#!/usr/bin/env python
import argparse
import logging
import zmq

"""
Server component, responsible for:
- pulling client updates (via PULL);
- distributing client updates (via PUB).

Run with 'python -m app.core.communication.Server --log debug'
"""

class Server:
    def __init__(self):
        self._ctx = zmq.Context()

        # Publisher side (for subscribers to connect to)
        self._publisher = self._ctx.socket(zmq.PUB)
        self._publisher.bind("tcp://*:5557")

        # Collector side (for clients to PUSH into)
        self._collector = self._ctx.socket(zmq.PULL)
        self._collector.bind("tcp://*:5558")

        self._poller = zmq.Poller()
        self._poller.register(self._collector, zmq.POLLIN)

    def run(self):
        logging.debug("Server running.")
        try:
            while True:
                items = dict(self._poller.poll(1000))

                if self._collector in items:
                    message = self._collector.recv_multipart()

                    if len(message) < 2:
                        logging.warning("Malformed message: %s", message)
                        continue

                    self._publisher.send_multipart(message)

        except KeyboardInterrupt:
            logging.info("KeyboardInterrupt received. Shutting down...")
        finally:
            self.close()

    def close(self):
        logging.debug("Closing sockets and terminating context.")
        try:
            self._publisher.close(0)
            self._collector.close(0)
            self._ctx.term()
        except Exception as e:
            logging.error("Error during cleanup: %s", e)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-log",
        "--log",
        default="warning",
        help=("Provide logging level. "
              "Example '--log debug', default='warning'.")
    )

    options = parser.parse_args()
    levels = {
        "critical": logging.CRITICAL,
        "error": logging.ERROR,
        "warn": logging.WARNING,
        "warning": logging.WARNING,
        "info": logging.INFO,
        "debug": logging.DEBUG,
    }
    level = levels.get(options.log.lower())
    if level is None:
        raise ValueError(
            f"log level given: {options.log} "
            f"-- must be one of: {' | '.join(levels.keys())}"
        )
    logging.basicConfig(format="[%(levelname)s] %(message)s", level=level)

    server = Server()
    server.run()
