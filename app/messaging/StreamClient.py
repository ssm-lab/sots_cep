import logging
import json
import zmq
from app.messaging.Client import Client
from app.schema.Event import Event, EventConsumer


class StreamClient:
    def __init__(self, prefix: str):
        self.client = Client()
        self.prefix = prefix
        self.subscribers: dict[str, list[EventConsumer]] = {}

    def publish(self, event: Event, stream_id: str):
        topic = f"{self.prefix}.{stream_id}"
        event["__topic__"] = topic
        payload = json.dumps(event).encode("utf-8")
        self.client._publisher.send_multipart([topic.encode("utf-8"), payload])
        logging.debug(f"[{self.prefix.upper()}-CLIENT] Published event to {topic}: {event}")


    def subscribe_to(self, stream_id: str, consumer: EventConsumer):
        if stream_id == "*":
            # Subscribe to all topics under this partition
            prefix = f"{self.prefix}."
            self.client._subscriber.setsockopt_string(zmq.SUBSCRIBE, prefix)
            topic = f"{self.prefix}.*"
        else:
            topic = f"{self.prefix}.{stream_id}"
            self.client._subscriber.setsockopt_string(zmq.SUBSCRIBE, topic)

        # Register consumer under this topic or wildcard
        self.subscribers.setdefault(topic, []).append(consumer)
        logging.info(f"[{self.prefix.upper()}-CLIENT] Subscribed {consumer.__class__.__name__} to {topic}")


    def dispatch_once(self, timeout: int = 1000):
        try:
            items = dict(self.client._poller.poll(timeout))
        except Exception as e:
            logging.error(f"[{self.prefix.upper()}-CLIENT] Polling error: {e}")
            return

        if self.client._subscriber in items:
            try:
                topic, payload = self.client._subscriber.recv_multipart()
                topic = topic.decode("utf-8")
                event = json.loads(payload.decode("utf-8"))

                event["__topic__"] = topic

                # Exact match
                if topic in self.subscribers:
                    for consumer in self.subscribers[topic]:
                        consumer.consume_event(event)

                # All
                wildcard = f"{self.prefix}.*"
                if wildcard in self.subscribers:
                    for consumer in self.subscribers[wildcard]:
                        consumer.consume_event(event)

            except Exception as e:
                logging.error(f"[{self.prefix.upper()}-CLIENT] Failed to process message: {e}")
