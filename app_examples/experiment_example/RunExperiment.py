from app.core.reconstruction.predictors.predictorTypes.KalmanFilter import KalmanFilter
from app.core.runtime.EventStream import EventStream
from .app_overrides.core.stream.ExperimentStreamManager import ExperimentStreamManager
from app.core.reconstruction.ReconstructionManager import ReconstructionManager
from app.core.logger.Logger import CSVLogger
import logging


logging.basicConfig(
    format="[%(levelname)s] %(message)s",
    level=logging.DEBUG
)

def configure_filters_dynamic(reconstruction_manager):
    # Default Kalman filter configuration
    default_kalman = KalmanFilter(
        initial_state=20.0,          # pick a reasonable water temperature prior
        process_variance=1e-3,       # how fast you expect it to drift
        measurement_variance=1e-2    # how noisy measurements are
    )

    for stream_id in reconstruction_manager.streams.keys():
        if stream_id not in reconstruction_manager.filters:
            reconstruction_manager.set_filter(stream_id, default_kalman)
            logging.info(f"[EXPERIMENT] Assigned Kalman filter to {stream_id}")



def main():
    event_stream = EventStream()

    with CSVLogger(output_dir="data/logs", name="all_partitions") as logger:
        # Subscribe logger to all partitions
        for partition in list(event_stream.partitions.keys()):
            event_stream.subscribe(logger, partition, "*")

        # Managers
        reconstruction_manager = ReconstructionManager(
            event_stream,
            "app_examples/exp/configs/streams.json",
            "app_examples/exp/filters.json"
        )
        stream_manager = ExperimentStreamManager(event_stream, "app_examples/exp/configs/streams.json")
        stream_manager.start()

        try:
            event_stream.dispatch(timeout=1000)
        except KeyboardInterrupt:
            event_stream.stop()
            logging.info("[MAIN] Stopping pipeline")

if __name__ == "__main__":
    main()
