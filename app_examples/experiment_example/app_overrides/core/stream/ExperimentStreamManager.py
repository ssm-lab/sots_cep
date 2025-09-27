import csv
import logging
import re
from app.core.stream.StreamManager import StreamManager
from app.core.schema.Event import Event
from app.core.stream.StreamRegistry import get_stream_class


def normalize_id(s: str) -> str:
    """Remove non-alphanumeric chars and lowercase for safe IDs."""
    return re.sub(r'[^a-zA-Z0-9]', '', s).lower()


class ExperimentStreamManager(StreamManager):
    """
    Experimental StreamManager:
    - Auto-discovers dataset streams (Beach × Field).
    - Publishes both observed/reconstructed and groundtruth partitions.
    """

    FIELD_UNITS = {
        "Water Temperature": "C",
        "Turbidity": "NTU",
        "Transducer Depth": "m",
        "Wave Height": "m",
        "Wave Period": "s",
        "Battery Life": "%"
    }

    def __init__(self, event_stream, streams_config_path: str):
        super().__init__(event_stream, streams_config_path)

    def _create_stream(self, stream_id: str, cfg: dict):
        stream_type = cfg.get("type", "simulated")

        # --- Auto-discover dataset streams ---
        if stream_type == "dataset_stream" and cfg.get("auto_discover", False):
            dataset_path = cfg["dataset_path"]

            with open(dataset_path, newline="") as f:
                reader = csv.DictReader(f)
                beaches = set(row["Beach Name"] for row in reader if row["Beach Name"])
                fields = [h for h in reader.fieldnames if h not in [
                    "Beach Name", "Measurement Timestamp", "Measurement Timestamp Label", "Measurement ID"
                ]]

            logging.info(
                f"[EXPERIMENT] Auto-discovered {len(beaches)} beaches × {len(fields)} fields from {dataset_path}"
            )

            expanded = {}
            for beach in beaches:
                for field in fields:
                    s_id = f"{normalize_id(beach)}_{normalize_id(field)}"
                    expanded[s_id] = {
                        "type": "dataset_stream",
                        "dataset_path": dataset_path,
                        "beach": beach,
                        "field": field,
                        "unit": self.FIELD_UNITS.get(field, ""),
                        "datatype": "float",
                        "interval": cfg.get("interval", 1.0),
                        "missing_strategy": cfg.get("missing_strategy", "mark-missing")
                    }

            self.streams_config.update(expanded)
            logging.debug(f"[EXPERIMENT] Example streams: {list(expanded.keys())[:5]}")
            return None

        # For other stream types (including experimental ones)
        cls = get_stream_class(cfg["type"], allow_experimental=True)
        return cls(stream_id=stream_id, **cfg)

    def _publish(self, stream_id: str, event: Event, partition: str = "observed") -> None:
        try:
            # Always publish original event
            super()._publish(stream_id, event, partition)

            # Duplicate groundtruth if available
            gt_val = event.get("extras", {}).get("ground_truth")
            if gt_val is not None:
                groundtruth_event = dict(event)
                groundtruth_event["partition"] = "groundtruth"
                groundtruth_event["status"] = "groundtruth"
                groundtruth_event["value"] = gt_val
                groundtruth_event["source"] = "GroundTruthStream"

                self.event_stream.add_event(groundtruth_event, "groundtruth", stream_id)
                logging.debug(
                    f"[EXPERIMENT] Published groundtruth event for {stream_id} with value={gt_val}"
                )
        except Exception as e:
            logging.exception(f"[EXPERIMENT] Failed to publish event for {stream_id}: {e}")
