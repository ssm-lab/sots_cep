import logging
from app.core.runtime.Coordinator import Coordinator
from ..stream.StreamTypes.ExperimentStream import EndOfDataset

# Auto-load registered types
from ..stream.StreamTypes import *

LOG = logging.getLogger(__name__)

class ExperimentCoordinator(Coordinator):
    """
    Coordinator for dataset-driven experiments.
    Handles both observed and missing data,
    and advances predictors during structural gaps without emitting events.
    """

    def _run_stream(self, stream_id, scheduler, stream):
        LOG.info(f"[ExperimentCoordinator] Starting dataset replay for {stream_id}")
        reconstructor = self.reconstructors.get(stream_id)
        if not reconstructor:
            LOG.warning(f"[ExperimentCoordinator] No reconstructor for {stream_id}")
            return

        while self.running:
            event_time = scheduler.wait_next()
            try:
                event, structural = stream.generate_event(event_time)

                # Case 1: structural gap → advance predictor, no emission
                if structural:
                    reconstructor.advance_without_emission(event_time)
                    continue

                # Case 2: missing (no observed value)
                if event is None:
                    LOG.debug(f"[ExperimentCoordinator] Missing data for {stream_id} at {event_time}")
                    missing_event = {
                        "stream_id": stream_id,
                        "origin": "missing",
                        "value": None,
                        "event_ts": event_time,
                    }
                    reconstructor.handle_timeout(missing_event)
                    continue

                # Case 3: normal observation
                self.event_stream.add_event(event, "observed", stream_id)

            except EndOfDataset:
                LOG.info(f"[ExperimentCoordinator] End of dataset for {stream_id}")
                break
            except Exception as e:
                LOG.exception(f"[ExperimentCoordinator] Error in {stream_id}: {e}")

        LOG.info(f"[ExperimentCoordinator] Stream {stream_id} stopped.")
