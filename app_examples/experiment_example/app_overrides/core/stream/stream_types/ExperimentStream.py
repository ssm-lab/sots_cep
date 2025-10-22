import pandas as pd
import os
from app.core.schema.Event import make_event
# from app.core.stream.StreamRegistry import register_stream_type

class EndOfDataset(Exception):
    """Raised when no more rows are available in the dataset stream."""
    pass


# @register_stream_type("experiment_stream")
class ExperimentStream:
    """
    Stream that replays observed values from a dataset file.
    Structural gaps (rows with structural_gap == 1) advance time but do not emit events.
    """

    def __init__(self, stream_id: str, unit=None, datatype="float", interval: float = 1.0, params=None):
        self.stream_id = stream_id
        self.file = params.get("file", None)
        self.beach = params.get("beach", "Calumet Beach")
        self.col = params.get("col", "Turbidity")
        self.unit = unit
        self.interval = interval
        self.datatype = datatype
        self.index = 0

        if not os.path.exists(self.file):
            raise FileNotFoundError(f"Dataset file not found: {self.file}")

        df = pd.read_csv(self.file)

        required = ["Beach Name", "Measurement Timestamp"]
        for colname in required:
            if colname not in df.columns:
                raise ValueError(f"Missing required column '{colname}' in dataset {self.file}")

        # Filter for this beach only
        self.df = df[df["Beach Name"] == self.beach].reset_index(drop=True)

        if self.col not in self.df.columns:
            raise ValueError(f"Column '{self.col}' not found for beach '{self.beach}' in {self.file}")

    def generate_event(self):
        """Emit next observed event or indicate structural gap."""
        if self.index >= len(self.df):
            raise EndOfDataset()

        row = self.df.iloc[self.index]
        self.index += 1

        ts = row["Measurement Timestamp"]
        obs_value = row[self.col]
        obs_value_groundtruth = row[f"{self.col}_groundtruth"]
        structural_gap = int(row.get("structural_gap", 0))
        event_id = row.get("Measurement ID", self.index)

        # Structural gap = advance predictor only, no event emitted
        if structural_gap == 1:
            return None, True, event_id, None

        # Missing or observed
        if pd.isna(obs_value):
            return None, False, event_id, obs_value_groundtruth

        event = make_event(
            self.stream_id,
            event_id=event_id,
            value=obs_value,
            unit=self.unit,
            datatype=self.datatype,
            event_ts=ts,
            status="observed",
            source="dataset",
            origin="source",
            extras= {"ground_truth": obs_value_groundtruth}
        )
        return event, False, event_id, obs_value_groundtruth
