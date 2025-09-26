import csv
import os
import time
import uuid
from abc import ABC, abstractmethod

from ..schema.Event import Event
from ..runtime.EventConsumer import EventConsumer


class BaseLogger(EventConsumer, ABC):
    def __init__(self, output_dir="data/logs", name="all_partitions"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.name = name
        self.records: list[Event] = []

    @abstractmethod
    def consume_event(self, event: Event):
        pass

    @abstractmethod
    def close(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class CSVLogger(BaseLogger):
    def __init__(self, output_dir="data/logs", name="all_partitions"):
        super().__init__(output_dir, name)

        run_id = uuid.uuid4().hex[:8]
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        filename = f"{self.name}_{timestamp}_{run_id}.csv"

        self.filepath = os.path.join(self.output_dir, filename)
        self.csvfile = None
        self.writer = None

        # Get base schema from Event definition
        self.base_fields = list(Event.__annotations__.keys())
        if "partition" not in self.base_fields:
            self.base_fields.insert(0, "partition")

    def _init_writer(self, event: Event):
        # Add any dynamic fields
        extra_fields = set(event.keys()) - set(self.base_fields)
        all_fields = self.base_fields + sorted(extra_fields)

        self.csvfile = open(self.filepath, "w", newline="", encoding="utf-8")
        self.writer = csv.DictWriter(self.csvfile, fieldnames=all_fields)

        self.csvfile.write(f"# Logger: CSVLogger | Started: {time.ctime()}\n")
        self.writer.writeheader()

    def consume_event(self, event: Event):
        topic = event.get("__topic__", "")
        partition = topic.split(".")[0] if topic else "unknown"
        event_with_partition = {"partition": partition, **event}

        if self.writer is None:
            self._init_writer(event_with_partition)

        row = {field: event_with_partition.get(field) for field in self.writer.fieldnames}
        self.records.append(row)
        self.writer.writerow(row)
        self.csvfile.flush()

    def close(self):
        if self.csvfile:
            self.csvfile.close()
