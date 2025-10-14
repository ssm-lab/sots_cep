from abc import ABC, abstractmethod
import threading, queue, csv, os, time

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
        # self.csvfile.flush()
        # Flush every 100 events
        if len(self.records) % 1000 == 0:
            self.csvfile.flush()

    def close(self):
        if self.csvfile:
            self.csvfile.close()


class AsyncCSVLogger:
    def __init__(self, run_dir, flush_every=5000, flush_interval=0.05):
        os.makedirs(run_dir, exist_ok=True)
        self.filepath = os.path.join(run_dir, "events.csv")
        self.csvfile = open(self.filepath, "w", buffering=1024*1024)  # 1MB buffer
        self._queue = queue.Queue(maxsize=100_000)
        self.flush_every = flush_every
        self.flush_interval = flush_interval
        self._last_flush = time.time()
        self._stop = False
        self._initialized = False   # <-- track header init
        self.fields = []

        self.thread = threading.Thread(target=self._writer_loop, daemon=True)
        self.thread.start()

    def _init_writer(self, event):
        from ...schema.Event import Event
        base_fields = list(Event.__annotations__.keys())
        extra_fields = set(event.keys()) - set(base_fields)
        self.fields = base_fields + sorted(extra_fields)
        header = ",".join(self.fields)
        self.csvfile.write(f"# Started {time.ctime()}\n{header}\n")
        self._initialized = True  # <-- mark it done

    def consume_event(self, event):
        if not self._initialized:  # <-- only once
            self._init_writer(event)
        try:
            self._queue.put_nowait(event)
        except queue.Full:
            # Optional: handle dropped events (monitor)
            pass

    def _writer_loop(self):
        batch = []
        while not self._stop or not self._queue.empty():
            try:
                event = self._queue.get(timeout=self.flush_interval)
                batch.append(event)
                if len(batch) >= self.flush_every:
                    self._flush_batch(batch)
                    batch.clear()
            except queue.Empty:
                if batch:
                    self._flush_batch(batch)
                    batch.clear()

    def _flush_batch(self, batch):
        lines = []
        for e in batch:
            line = ",".join(str(e.get(f, "")) for f in self.fields)
            lines.append(line)
        self.csvfile.write("\n".join(lines) + "\n")

        # Controlled flush frequency
        if time.time() - self._last_flush > 10.0:
            self.csvfile.flush()
            self._last_flush = time.time()

    def close(self):
        self._stop = True
        self.thread.join()
        self.csvfile.flush()
        self.csvfile.close()

