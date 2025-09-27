import csv
import random, time
from app.core.stream.Stream import Stream
from app.core.schema.Event import Event
from app.core.stream.StreamRegistry import register_stream_type

@register_stream_type("experiment_stream", experimental=True)
class ExperimentStream(Stream):
    """
    Stream that replays rows from a dataset for a specific Beach × Field.
    Missing values are handled via `missing_strategy`.
    """

    def __init__(self, stream_id: str, dataset_path: str, beach: str, field: str,
                 unit: str = "", datatype: str = "float", interval: float = 1.0,
                 missing_strategy: str = "mark-missing", **kwargs):
        super().__init__(stream_id, unit, datatype, interval)
        self.dataset_path = dataset_path
        self.beach = beach
        self.field = field
        self.missing_strategy = missing_strategy

        with open(dataset_path, newline="") as f:
            reader = csv.DictReader(f)
            # Filter only relevant rows
            self.rows = [row for row in reader if row["Beach Name"] == beach]

        self.index = 0

    def generate_event(self) -> Event:
        if self.index >= len(self.rows):
            raise StopIteration(f"No more rows for {self.beach}-{self.field}")

        row = self.rows[self.index]
        self.index += 1

        raw_val = row[self.field]
        try:
            value = float(raw_val.replace(",", "")) if raw_val not in ("", "-100000", "-100,000") else None
        except Exception:
            value = None

        status = "observed"
        if value is None:
            if self.missing_strategy == "mark-missing":
                status = "missing"
            elif self.missing_strategy == "skip":
                raise TimeoutError("Skipped missing value")

        return {
            "stream_id": self.stream_id,
            "sampled_ts": time.time(),
            "value": value,
            "unit": self.unit,
            "datatype": self.datatype,
            "status": status,
            "source": f"DatasetStream-{self.beach}",
            "extras": {"ground_truth": value}
        }