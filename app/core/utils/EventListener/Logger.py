from abc import abstractmethod
import threading, queue, csv, os, time
import logging
import csv
import json

from ...schema.Event import Event
from ...schema.EventConsumer import EventConsumer
LOG = logging.getLogger(__name__)


class BaseLogger(EventConsumer):
    """
    Event consumer that logs all events on the event stream to a CSV file
    """
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
    def __init__(self, run_dir, flush_every=5000, flush_interval=0.05):
        super().__init__(run_dir)
        os.makedirs(run_dir, exist_ok=True)
        self.filepath = os.path.join(run_dir, "events.csv")
        self.csvfile = open(self.filepath, "w", newline="", buffering=1024 * 1024)
        self._queue = queue.Queue(maxsize=100_000)
        self.flush_every = flush_every
        self.flush_interval = flush_interval
        self._last_flush = time.time()
        self._stop_event = threading.Event()
        self._initialized = False
        self.fields = []

        self.thread = threading.Thread(target=self._writer_loop, name="CSVLoggerThread", daemon=False)
        self.thread.start()

    def _init_writer(self, event):
        from ...schema.Event import Event
        base_fields = list(Event.__annotations__.keys())
        extra_fields = set(event.keys()) - set(base_fields)
        self.fields = base_fields + sorted(extra_fields)

        self.writer = csv.DictWriter(
            self.csvfile,
            fieldnames=self.fields,
            quoting=csv.QUOTE_MINIMAL
        )
        self.csvfile.write(f"# Started {time.ctime()}\n")
        self.writer.writeheader()

        self._initialized = True

    def consume_event(self, event):
        if not self._initialized:
            self._init_writer(event)
        try:
            self._queue.put(event, block=False)
        except queue.Full:
            # Optional: log a warning or drop silently
            logging.warning("logger queue full")
            pass

    def _writer_loop(self):
        batch = []
        while not (self._stop_event.is_set() and self._queue.empty()):
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
        # Final flush after loop exits
        if batch:
            self._flush_batch(batch)
        self.csvfile.flush()

    def _flush_batch(self, batch):
        for e in batch:
            row = e.copy()
            if "extras" in row and isinstance(row["extras"], dict):
                row["extras"] = json.dumps(row["extras"])

            self.writer.writerow(row)

        if time.time() - self._last_flush > 5.0:
            self.csvfile.flush()
            self._last_flush = time.time()

    def close(self, timeout=None):
        """Signal stop and wait until all queued events are written."""
        self._stop_event.set()
        self.thread.join(timeout=timeout)
        if self.thread.is_alive():
            print("[WARN] Logger thread did not finish before timeout.")
        self.csvfile.flush()
        self.csvfile.close()
        logging.info("[LOGGER] Shutting down...")


class LifecycleLogger(BaseLogger):
    def __init__(self, run_dir: str):
        super().__init__(run_dir)

        self.filepath = os.path.join(run_dir, "lifecycle.csv")
        self.file = open(self.filepath, "w", newline="")

        self.writer = None
        self.fields = None

        LOG.info(f"[LIFECYCLE LOGGER] Writing to {self.filepath}")

    def consume_event(self, event: dict):
        """
        Expects event as dict (not Event object)
        """
        # Initialize header on first event
        if self.writer is None:
            self.fields = list(event.keys())
            self.writer = csv.DictWriter(self.file, fieldnames=self.fields)

            self.file.write(f"# Started {time.ctime()}\n")
            self.writer.writeheader()

        self.writer.writerow(event)
        self.file.flush()

    def close(self):
        if self.file:
            self.file.flush()
            self.file.close()
            LOG.info("[LIFECYCLE LOGGER] Shutting down...")

