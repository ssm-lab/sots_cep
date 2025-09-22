import csv
import os
from app.schema.Event import Event, EventConsumer


class Logger(EventConsumer):
    def __init__(self, output_dir="app/data/logs", name="test"):
        filename = f"{name}.csv"

        self.records: list[Event] = []
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.filepath = os.path.join(self.output_dir, filename)

        # get base fields from Event
        self.base_fields = list(Event.__annotations__.keys())

        if "partition" not in self.base_fields:
            self.base_fields.insert(0, "partition")

        self.csvfile = None
        self.writer = None


    def _init_writer(self, event: Event):
        """
        Initialize CSV writer using Event schema + any extra fields discovered.
        """
        # capture additional dynamic fields (like __topic__)
        extra_fields = set(event.keys()) - set(self.base_fields)
        all_fields = self.base_fields + sorted(extra_fields)

        self.csvfile = open(self.filepath, "w", newline="", encoding="utf-8")
        self.writer = csv.DictWriter(self.csvfile, fieldnames=all_fields)
        self.writer.writeheader()

    def consume_event(self, event: Event):
        """
        Called by EventStream when subscribed. Logs the event to CSV.
        """
        topic = event.get("__topic__", "")
        partition = topic.split(".")[0] if topic else "unknown"

        event_with_partition = {"partition": partition, **event}

        # lazily init writer from the first event
        if self.writer is None:
            self._init_writer(event_with_partition)

        row = {field: event_with_partition.get(field) for field in self.writer.fieldnames}

        self.records.append(row)
        self.writer.writerow(row)
        self.csvfile.flush()

    def close(self):
        if self.csvfile:
            self.csvfile.close()
