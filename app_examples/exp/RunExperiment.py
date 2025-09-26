from app.core.runtime.EventStream import EventStream
from .ExperimentStreamManager import ExperimentStreamManager
from app.core.imputation.ReconstructionManager import ReconstructionManager
from app.core.logger.Logger import CSVLogger
import logging


logging.basicConfig(
    format="[%(levelname)s] %(message)s",
    level=logging.DEBUG
)


def main():
    event_stream = EventStream()

    with CSVLogger(output_dir="data/logs", name="all_partitions") as logger:
        # Subscribe logger to all partitions
        for partition in list(event_stream.partitions.keys()):
            event_stream.subscribe(logger, partition, "*")

        # Managers
        reconstruction_manager = ReconstructionManager(
            event_stream,
            "app/core/configs/streams.json",
            "app/core/configs/filters.json"
        )
        stream_manager = ExperimentStreamManager(event_stream, "app/core/configs/streams.json")
        stream_manager.start()

        try:
            event_stream.dispatch(timeout=1000)
        except KeyboardInterrupt:
            event_stream.stop()
            logging.info("[MAIN] Stopping pipeline")

if __name__ == "__main__":
    main()
