import logging
import time
import os
import pandas as pd
from tqdm import tqdm
from app.core.schema.Event import make_event
from app.core.reconstruction.PredictorRegistry import get_predictor_class
from app.core.reconstruction.Reconstructor import Reconstructor
from app.core.utils.UtilsFuncs import _load_json

LOG = logging.getLogger(__name__)

class ExperimentCoordinator:
    def __init__(self,
                 event_stream,
                 streams_config_path,
                 predictors_config_path,
                 on_complete=None,
                 interval=0.1):
        self.event_stream = event_stream
        self.streams_cfg = _load_json(streams_config_path)
        self.predictors_cfg = _load_json(predictors_config_path)
        self.interval = interval
        self.on_complete = on_complete

        self.reconstructors = {}
        self.running = False
        self.df = None
        self.timestamps = []

        self._load_dataset()
        self._setup_reconstructors()


    def _load_dataset(self):
        """Load the dataset once for all streams."""
        first = next(iter(self.streams_cfg.values()))
        dataset_path = first["params"]["file"]

        if not os.path.exists(dataset_path):
            raise FileNotFoundError(f"Dataset not found: {dataset_path}")

        df = pd.read_csv(dataset_path)
        if "Measurement Timestamp" not in df.columns:
            raise ValueError("Missing 'Measurement Timestamp' column in dataset.")

        df.sort_values("Measurement Timestamp", inplace=True)
        self.df = df
        self.timestamps = sorted(df["Measurement Timestamp"].unique())
        LOG.info(f"[ExperimentCoordinator] Loaded {len(df)} rows, "
                 f"{len(self.timestamps)} unique timestamps from {dataset_path}")

    def _setup_reconstructors(self):
        """Wire predictors and reconstructors for each stream."""
        for stream_id, cfg in self.streams_cfg.items():
            predictor_template = cfg.get("predictor_template")
            predictor_cfg = self.predictors_cfg.get(predictor_template)

            if predictor_cfg is None:
                raise ValueError(f"[ExperimentCoordinator] Missing predictor template: {predictor_template}")

            predictor_cls = get_predictor_class(predictor_cfg["type"])
            predictor = predictor_cls(**predictor_cfg.get("params", {}))

            reconstructor = Reconstructor(
                stream_id=stream_id,
                predictor=predictor,
                event_stream=self.event_stream
            )

            # Subscribe reconstructor to observed events for its stream
            self.event_stream.subscribe(reconstructor, "observed", stream_id)
            self.reconstructors[stream_id] = reconstructor

        LOG.info(f"[ExperimentCoordinator] Setup complete for {len(self.reconstructors)} reconstructors.")



    # Main run loop
    def start(self):
        self.running = True
        LOG.info("[ExperimentCoordinator] Starting dataset replay...")

        try:
            with tqdm(total=len(self.timestamps),
                      desc="Replaying dataset",
                      unit="timestamp",
                      dynamic_ncols=True,
                      leave=True,
                      colour="cyan") as pbar:

                for ts in self.timestamps:
                    if not self.running:
                        break

                    timestamp_slice = self.df[self.df["Measurement Timestamp"] == ts]
                    events_to_emit = []

                    for _, row in timestamp_slice.iterrows():
                        beach = row["Beach Name"]
                        structural_gap = int(row.get("structural_gap", 0))

                        for col_name in [
                            c for c in self.df.columns
                            if any(k in c for k in
                                   ["Water Temperature", "Turbidity", "Wave Height", "Wave Period"])
                            and "_groundtruth" not in c
                        ]:
                            val = row.get(col_name)
                            groundtruth = row.get(f"{col_name}_groundtruth", None)
                            stream_id = f"{beach.replace(' ', '_')}_{col_name.replace(' ', '_')}"
                            reconstructor = self.reconstructors.get(stream_id)

                            # Construct event ID based on Measurement ID
                            measurement_id = row.get("Measurement ID", None)
                            safe_col = col_name.replace(" ", "_")
                            event_id = f"{measurement_id}_{safe_col}" if measurement_id is not None else f"missing_{safe_col}"

                            # Structural gap
                            if structural_gap == 1:
                                if reconstructor:
                                    reconstructor.advance_without_event()
                                continue

                            # Missing value
                            if pd.isna(val):
                                if reconstructor:
                                    missing_event = {
                                        "stream_id": stream_id,
                                        "event_id": event_id,
                                        "origin": "missing",
                                        "value": None,
                                        "event_ts": ts,
                                        "extras": {"ground_truth": groundtruth},
                                    }
                                    reconstructor.handle_timeout(missing_event)
                                continue

                            # Observed value
                            try:
                                event = make_event(
                                    stream_id=stream_id,
                                    event_id=event_id,
                                    value=val,
                                    unit=None,
                                    datatype="float",
                                    event_ts=ts,
                                    status="observed",
                                    source="dataset",
                                    origin="source",
                                    extras={"ground_truth": groundtruth}
                                )
                                # events_to_emit.append(event)
                                self.event_stream.add_event(event, "observed", event["stream_id"])
                            except Exception as e:
                                LOG.warning(f"[ExperimentCoordinator] Skipped malformed event ({stream_id}): {e}")
                                continue

                    # for event in events_to_emit:
                    #         self.event_stream.add_event(event, "observed", event["stream_id"])

                    # slight delay between timesteps
                    time.sleep(self.interval)
                    pbar.update(1)

        except KeyboardInterrupt:
            LOG.warning("[ExperimentCoordinator] Interrupted manually.")
        finally:
            LOG.info("[ExperimentCoordinator] Dataset replay complete.")
            self.running = False
            if self.on_complete:
                self.on_complete()

    def stop(self):
        self.running = False
        LOG.info("[ExperimentCoordinator] Stop signal received.")
