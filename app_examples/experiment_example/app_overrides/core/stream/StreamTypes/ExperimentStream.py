import pandas as pd
from app.core.stream.Stream import Stream
from app.core.schema.Event import Event, make_event
from app.core.stream.StreamRegistry import register_stream_type

class EndOfDataset(Exception):
    """Raised when a dataset stream has no more data to emit."""
    pass

@register_stream_type("experiment_stream")
class ExperimentStream:
    def __init__(self, stream_id: str, df: pd.DataFrame, beach: str, col: str, unit=None, datatype="float"):
        """
        Each stream extracts rows for (beach, col).
        df: full dataset with *_groundtruth columns
        """
        self.stream_id = stream_id
        self.df = df[df["Beach"] == beach].reset_index(drop=True)
        self.col = col
        self.col_gt = f"{col}_groundtruth"
        self.unit = unit
        self.datatype = datatype
        self.index = 0

    def generate_event(self, event_time: float):
        if self.index >= len(self.df):
            raise EndOfDataset()

        row = self.df.iloc[self.index]
        self.index += 1

        ts = row["Timestamp"]
        gt_value = row[self.col_gt]
        obs_value = row[self.col]

        # Groundtruth event
        groundtruth = make_event(
            self.stream_id, value=gt_value, unit=self.unit, datatype=self.datatype,
            event_ts=ts, status="groundtruth", source="dataset", origin="groundtruth"
        )

        # Observed event
        observed = None if pd.isna(obs_value) else make_event(
            self.stream_id, value=obs_value, unit=self.unit, datatype=self.datatype,
            event_ts=ts, status="coordinated", source="dataset", origin="source"
        )

        return observed, groundtruth