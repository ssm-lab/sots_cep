import logging
from app.core.runtime.Coordinator import Coordinator
from ..stream.StreamTypes.ExperimentStream import EndOfDataset

# Auto load registries
from ..stream.StreamTypes import *

class ExperimentCoordinator(Coordinator):
    def _run_stream(self, stream_id, scheduler, stream):
        while self.running:
            event_time = scheduler.wait_next()
            try:
                observed, groundtruth = stream.generate_event(event_time)

                # Always publish ground truth
                self.event_stream.add_event(groundtruth, "groundtruth", stream_id)

                if observed is not None:
                    # Normal observed case
                    self.event_stream.add_event(observed, "observed", stream_id)
                else:
                    # Missing: forward to reconstructor
                    missing_event = {**groundtruth,
                                     "origin": "missing",
                                     "value": None}
                    reconstructor = self.reconstructors.get(stream_id)
                    if reconstructor:
                        reconstructor.handle_timeout(missing_event)

            except EndOfDataset:
                logging.info(f"[COORD] End of dataset for {stream_id}")
                break
            except Exception as e:
                logging.exception(f"[EXPERIMENT COORD] Error in {stream_id}: {e}")
