import zmq
import logging
from ..Server import Server

__author__ = "Feyi Adesanya"
# python -m app.messaging.comm_types.ZMQServer --log debug

from ..ServerRegistry import register_server_type

@register_server_type("zmq")
class ZMQServer(Server):
    def __init__(self, pub_endpoint="tcp://*:5557", pull_endpoint="tcp://*:5558"):
        super().__init__()
        self.ctx = zmq.Context()

        # Publisher: broadcasts to subscribers
        self._publisher = self.ctx.socket(zmq.PUB)
        self._publisher.bind(pub_endpoint)
        self._publisher.setsockopt(zmq.SNDHWM, 1_000_000)
        self._publisher.setsockopt(zmq.LINGER, 0)

        # Collector: receives from publishers
        self._collector = self.ctx.socket(zmq.PULL)
        self._collector.bind(pull_endpoint)
        self._collector.setsockopt(zmq.RCVHWM, 1_000_000)
        self._collector.setsockopt(zmq.LINGER, 0)

        self._poller = zmq.Poller()
        self._poller.register(self._collector, zmq.POLLIN)

        self._running = False
        logging.info(f"[ZMQServer] PUB bound to {pub_endpoint}, PULL bound to {pull_endpoint}")

    def _loop(self):
        """Main relay loop: receives from collector and forwards to publisher."""
        logging.info("[ZMQServer] Server started.")
        self._running = True

        try:
            while self._running:
                try:
                    # Poll every 500 ms to allow graceful shutdown
                    items = dict(self._poller.poll(500))
                except zmq.ContextTerminated:
                    break
                except zmq.ZMQError as e:
                    if not self._running:
                        break
                    logging.error(f"[ZMQServer] Poll error: {e}")
                    continue

                if not self._running:
                    break

                if self._collector in items:
                    try:
                        message = self._collector.recv_multipart(flags=zmq.NOBLOCK)
                    except zmq.Again:
                        continue
                    except zmq.ZMQError as e:
                        if not self._running:
                            break
                        logging.error(f"[ZMQServer] Recv error: {e}")
                        continue

                    # Expect 2-frame messages: [topic, payload]
                    if not message or len(message) < 2:
                        logging.warning(f"[ZMQServer] Malformed message: {message}")
                        continue

                    # Skip ZeroMQ control frames (0x00 or 0x01 at start)
                    first_frame = message[0]
                    if first_frame and first_frame[0] in (0, 1):
                        logging.debug(f"[ZMQServer] Ignored control frame: {message}")
                        continue

                    try:
                        self._publisher.send_multipart(message, flags=zmq.NOBLOCK)
                    except zmq.Again:
                        logging.warning("[ZMQServer] Publisher socket full; dropping message.")
                    except zmq.ZMQError as e:
                        if not self._running:
                            break
                        logging.error(f"[ZMQServer] Send error: {e}")
                        continue

        except Exception as e:
            logging.exception(f"[ZMQServer] Unexpected error in loop: {e}")
        finally:
            logging.info("[ZMQServer] Loop exiting.")
            self._cleanup()


    def stop(self):
        """Signal the server loop to stop and clean up sockets."""
        if not self._running:
            return
        logging.info("[ZMQServer] Stopping server...")
        self._running = False
        # Wake up poll() immediately by terminating context or unblocking collector
        try:
            # Send dummy message to break poller if still blocking
            temp_ctx = zmq.Context.instance()
            temp_socket = temp_ctx.socket(zmq.PUSH)
            temp_socket.connect("tcp://localhost:5558")
            temp_socket.send(b"STOP")
            temp_socket.close(0)
            temp_ctx.term()
        except Exception:
            pass



    def _cleanup(self):
        """Close sockets and terminate context cleanly."""
        logging.info("[ZMQServer] Cleaning up sockets and context.")
        try:
            if not self._publisher.closed:
                self._publisher.close(linger=0)
            if not self._collector.closed:
                self._collector.close(linger=0)

            # Wait a short moment before terminating to ensure closures propagate
            try:
                self.ctx.term()
            except zmq.ZMQError as e:
                logging.warning(f"[ZMQServer] Context termination warning: {e}")
        except Exception as e:
            logging.warning(f"[ZMQServer] Error during cleanup: {e}")

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    server = ZMQServer()

    try:
        server.run(in_thread=False)
    except KeyboardInterrupt:
        logging.info("[ZMQServer] Keyboard interrupt received, shutting down.")
        server.stop()