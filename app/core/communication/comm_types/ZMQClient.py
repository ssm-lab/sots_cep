import zmq
import logging
from app.core.utils.util_funcs import _deserialize_event, _serialize_event
from ..Client import Client

class ZMQClient(Client):
    def __init__(self, partition: str, pub_endpoint="tcp://localhost:5558", sub_endpoint="tcp://localhost:5557"):
        self.partition = partition
        self.ctx = zmq.Context()

        # Publisher (PUSH)
        self.publisher = self.ctx.socket(zmq.PUSH)
        self.publisher.connect(pub_endpoint)

        # Subscriber (SUB)
        self.subscriber = self.ctx.socket(zmq.SUB)
        self.subscriber.connect(sub_endpoint)

        # Registered consumers: topic → [consumers]
        self.consumers: dict[str, list] = {}

    def publish(self, event, stream_id: str):
        topic = f"{self.partition}.{stream_id}".encode()
        payload = _serialize_event(event)
        logging.debug(f"[ZMQClient] Publishing {topic}")
        self.publisher.send_multipart([topic, payload])

    def subscribe_to(self, stream_id: str, consumer):
        if stream_id == "*":
            # wildcard subscription
            prefix = f"{self.partition}.".encode()
            self.subscriber.setsockopt(zmq.SUBSCRIBE, prefix)
            topic = f"{self.partition}.*"
        else:
            topic = f"{self.partition}.{stream_id}"
            self.subscriber.setsockopt(zmq.SUBSCRIBE, topic.encode())

        self.consumers.setdefault(topic, []).append(consumer)
        logging.info(f"[ZMQClient-{self.partition}] Subscribed to {topic}")

    def dispatch(self, timeout: int = 1000):
        poller = zmq.Poller()
        poller.register(self.subscriber, zmq.POLLIN)

        events = dict(poller.poll(timeout))
        if self.subscriber in events:
            msg = self.subscriber.recv_multipart()
            if len(msg) != 2:
                logging.warning(f"[ZMQClient] Malformed message: {msg}")
                return

            topic, payload = msg
            topic = topic.decode("utf-8")
            payload = _deserialize_event(payload)

            # Exact match
            if topic in self.consumers:
                for consumer in self.consumers[topic]:
                    consumer.consume_event(payload)

            # Wildcard
            wildcard = f"{self.partition}.*"
            if wildcard in self.consumers:
                for consumer in self.consumers[wildcard]:
                    consumer.consume_event(payload)

    def close(self):
        self.publisher.close()
        self.subscriber.close()
        self.ctx.term()
