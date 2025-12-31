import pandas as pd
from app.core.schema.Event import make_event
from app.core.stream.StreamRegistry import register_stream_type

class EndOfDataset(Exception):
    """Raised when no more rows are available in the dataset stream."""
    pass

@register_stream_type("experiment_stream")
class ExperimentStream:
    """
    Stream that replays observed values from a dataset.
    Structural gaps (rows with structural_gap == 1) advance time but do not emit events.
    """

    def __init__(self, stream_id: str, df: pd.DataFrame, beach: str, col: str, unit=None, datatype="float"):
        self.stream_id = stream_id
        self.df = df[df["Beach"] == beach].reset_index(drop=True)
        self.col = col
        self.unit = unit
        self.datatype = datatype
        self.index = 0

    def generate_event(self, event_time: float):
        """Emit next observed event or indicate structural gap."""
        if self.index >= len(self.df):
            raise EndOfDataset()

        row = self.df.iloc[self.index]
        self.index += 1

        ts = row["Timestamp"]
        obs_value = row[self.col]
        structural_gap = int(row.get("structural_gap", 0))

        # Structural gap → advance predictor only, no event emitted
        if structural_gap == 1:
            return None, True

        # Missing or observed
        if pd.isna(obs_value):
            return None, False

        event = make_event(
            self.stream_id,
            value=obs_value,
            unit=self.unit,
            datatype=self.datatype,
            event_ts=ts,
            status="observed",
            source="dataset",
            origin="source",
        )
        return event, False
