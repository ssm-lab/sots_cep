import logging
import json
import threading
import zmq
from ..schema.Event import Event
from ..runtime.EventConsumer import EventConsumer

"""
Generic stream client component.
"""

class Client:
    def __init__(self, prefix: str):
        self.prefix = prefix
        self._ctx = zmq.Context.instance()
        self._subscriber = self._ctx.socket(zmq.SUB)
        self._publisher = self._ctx.socket(zmq.PUSH)

        self._subscriber.linger = 0
        self._subscriber.connect("tcp://localhost:5557")
        self._publisher.linger = 0
        self._publisher.connect("tcp://localhost:5558")

        self._poller = zmq.Poller()
        self._poller.register(self._subscriber, zmq.POLLIN)

        self.subscribers: dict[str, list[EventConsumer]] = {}
        # self._lock = threading.Lock()

    def publish(self, event: Event, stream_id: str):
        topic = f"{self.prefix}.{stream_id}"
        event["__topic__"] = topic
        payload = json.dumps(event).encode("utf-8")
        self._publisher.send_multipart([topic.encode("utf-8"), payload])

    def subscribe_to(self, stream_id: str, consumer: EventConsumer):
        if stream_id == "*":
            prefix = f"{self.prefix}."
            self._subscriber.setsockopt_string(zmq.SUBSCRIBE, prefix)
            topic = f"{self.prefix}.*"
        else:
            topic = f"{self.prefix}.{stream_id}"
            self._subscriber.setsockopt_string(zmq.SUBSCRIBE, topic)

        self.subscribers.setdefault(topic, []).append(consumer)

    def dispatch(self, timeout: int = 1000):
        items = dict(self._poller.poll(timeout))
        if self._subscriber in items:
            topic, payload = self._subscriber.recv_multipart()
            topic = topic.decode("utf-8")
            event = json.loads(payload.decode("utf-8"))
            event["__topic__"] = topic

            # Exact match
            if topic in self.subscribers:
                for consumer in self.subscribers[topic]:
                    consumer.consume_event(event)

            # Wildcard
            wildcard = f"{self.prefix}.*"
            if wildcard in self.subscribers:
                for consumer in self.subscribers[wildcard]:
                    consumer.consume_event(event)
