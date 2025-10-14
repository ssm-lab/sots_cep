# import zmq
# import logging
# from app.core.utils.UtilsFuncs import _deserialize_event, _serialize_event
# from ..Client import Client

# __author__ = "Feyi Adesanya"

# class ZMQClient(Client):
#     def __init__(self, partition: str, pub_endpoint="tcp://localhost:5558", sub_endpoint="tcp://localhost:5557"):
#         self.partition = partition
#         self.ctx = zmq.Context()

#         # Publisher (PUSH)
#         self.publisher = self.ctx.socket(zmq.PUSH)
#         self.publisher.connect(pub_endpoint)

#         # Subscriber (SUB)
#         self.subscriber = self.ctx.socket(zmq.SUB)
#         self.subscriber.connect(sub_endpoint)

#         # Registered consumers: topic → [consumers]
#         self.consumers: dict[str, list] = {}

#     def publish(self, event, stream_id: str):
#         topic = f"{self.partition}.{stream_id}".encode()
#         payload = _serialize_event(event)
#         logging.debug(f"[ZMQClient] Publishing {topic}")
#         self.publisher.send_multipart([topic, payload])

#     def subscribe_to(self, stream_id: str, consumer):
#         if stream_id == "*":
#             # wildcard subscription
#             prefix = f"{self.partition}.".encode()
#             self.subscriber.setsockopt(zmq.SUBSCRIBE, prefix)
#             topic = f"{self.partition}.*"
#         else:
#             topic = f"{self.partition}.{stream_id}"
#             self.subscriber.setsockopt(zmq.SUBSCRIBE, topic.encode())

#         self.consumers.setdefault(topic, []).append(consumer)
#         logging.info(f"[ZMQClient-{self.partition}] Subscribed to {topic}")

#     def dispatch(self, timeout: int = 2):
#         poller = zmq.Poller()
#         poller.register(self.subscriber, zmq.POLLIN)

#         events = dict(poller.poll(timeout))
#         if self.subscriber in events:
#             msg = self.subscriber.recv_multipart()
#             if len(msg) != 2:
#                 logging.warning(f"[ZMQClient] Malformed message: {msg}")
#                 return

#             topic, payload = msg
#             topic = topic.decode("utf-8")
#             payload = _deserialize_event(payload)

#             # Exact match
#             if topic in self.consumers:
#                 for consumer in self.consumers[topic]:
#                     consumer.consume_event(payload)

#             # Wildcard
#             wildcard = f"{self.partition}.*"
#             if wildcard in self.consumers:
#                 for consumer in self.consumers[wildcard]:
#                     consumer.consume_event(payload)

#     def close(self):
#         self.publisher.close()
#         self.subscriber.close()
#         self.ctx.term()


import zmq
import logging
from app.core.utils.UtilsFuncs import _deserialize_event, _serialize_event
from ..Client import Client

class ZMQClient(Client):
    def __init__(self, partition: str, pub_endpoint="tcp://localhost:5558", sub_endpoint="tcp://localhost:5557"):
        self.partition = partition
        self.ctx = zmq.Context()

        # Publisher (PUSH)
        self.publisher = self.ctx.socket(zmq.PUSH)
        self.publisher.connect(pub_endpoint)
        self.publisher.setsockopt(zmq.SNDHWM, 100000)

        # Subscriber (SUB)
        self.subscriber = self.ctx.socket(zmq.SUB)
        self.subscriber.connect(sub_endpoint)
        self.subscriber.setsockopt(zmq.RCVHWM, 100000)
        self.subscriber.setsockopt(zmq.CONFLATE, 0)
        self.subscriber.setsockopt(zmq.RCVTIMEO, 0)

        self.poller = zmq.Poller()
        self.poller.register(self.subscriber, zmq.POLLIN)

        self.consumers: dict[str, list] = {}

    def publish(self, event, stream_id: str):
        topic = f"{self.partition}.{stream_id}".encode()
        payload = _serialize_event(event)
        self.publisher.send_multipart([topic, payload], zmq.NOBLOCK)

    def subscribe_to(self, stream_id: str, consumer):
        if stream_id == "*":
            prefix = f"{self.partition}.".encode()
            self.subscriber.setsockopt(zmq.SUBSCRIBE, prefix)
            topic = f"{self.partition}.*"
        else:
            topic = f"{self.partition}.{stream_id}"
            self.subscriber.setsockopt(zmq.SUBSCRIBE, topic.encode())

        self.consumers.setdefault(topic, []).append(consumer)
        logging.info(f"[ZMQClient-{self.partition}] Subscribed to {topic}")

    def poll_once(self, timeout: int = 0):
        """Handle one or more incoming messages without blocking."""
        events = dict(self.poller.poll(timeout))
        if self.subscriber not in events:
            return  # nothing ready

        while True:
            try:
                msg = self.subscriber.recv_multipart(zmq.NOBLOCK)
            except zmq.Again:
                break  # drained the socket

            if len(msg) != 2:
                continue

            topic, payload = msg
            topic = topic.decode("utf-8")
            payload = _deserialize_event(payload)

            for key in (topic, f"{self.partition}.*"):
                for consumer in self.consumers.get(key, []):
                    consumer.consume_event(payload)

    def close(self):
        self.publisher.close()
        self.subscriber.close()
        self.ctx.term()
