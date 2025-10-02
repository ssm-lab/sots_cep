import csv
import os
import time
from abc import ABC, abstractmethod

from ...schema.Event import Event
from ...runtime.EventConsumer import EventConsumer

"""
Logger: Event consumer that logs to CSV files.
Subscribes to topics of interest.
"""
class BaseLogger(EventConsumer, ABC):
    def __init__(self, run_dir: str):
        os.makedirs(run_dir, exist_ok=True)
        self.run_dir = run_dir
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
    def __init__(self, run_dir: str):
        super().__init__(run_dir)

        self.filepath = os.path.join(self.run_dir, "events.csv")
        self.csvfile = None
        self.writer = None

        # Schema fields directly from Event definition
        self.base_fields = list(Event.__annotations__.keys())

    def _init_writer(self, event: Event):
        # Add any dynamic fields (extras, reconstruction metadata, etc.)
        extra_fields = set(event.keys()) - set(self.base_fields)
        all_fields = self.base_fields + sorted(extra_fields)

        self.csvfile = open(self.filepath, "w", newline="", encoding="utf-8")
        self.writer = csv.DictWriter(self.csvfile, fieldnames=all_fields)

        self.csvfile.write(f"# Logger: CSVLogger | Started: {time.ctime()}\n")
        self.writer.writeheader()

    def consume_event(self, event: Event):
        if self.writer is None:
            self._init_writer(event)

        row = {field: event.get(field) for field in self.writer.fieldnames}
        self.records.append(row)
        self.writer.writerow(row)
        self.csvfile.flush()

    def close(self):
        if self.csvfile:
            self.csvfile.close()
