import logging
from app.core.stream.StreamManager import StreamManager
from app.core.schema.Event import Event

class ExperimentStreamManager(StreamManager):
    """
    Experimental variant of StreamManager that publishes both events and duplicates a groundtruth event if extras.ground_truth is present.
    For experimental evaluation
    """

    def __init__(self, event_stream, streams_config_path: str):
        super().__init__(event_stream, streams_config_path)

    def _publish(self, stream_id: str, event: Event, partition: str = "observed") -> None:
        try:
            # Always publish the original event normally
            super()._publish(stream_id, event, partition)

            # If ground truth is available, publish it to the "groundtruth" partition
            gt_val = event.get("extras", {}).get("ground_truth")
            if gt_val is not None:
                groundtruth_event = dict(event)
                groundtruth_event["partition"] = "groundtruth"
                groundtruth_event["status"] = "groundtruth"
                groundtruth_event["value"] = gt_val
                groundtruth_event["source"] = "GroundTruthStream"

                self.event_stream.add_event(groundtruth_event, "groundtruth", stream_id)
        except Exception as e:
            logging.exception(f"[EXPERIMENT] Failed to publish event for {stream_id}: {e}")
