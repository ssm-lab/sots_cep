import logging
from app.core.runtime.EventStream import EventStream
from app.core.stream.StreamManager import StreamManager
from app.core.imputation.ReconstructionManager import ReconstructionManager
from app.core.logger.Logger import CSVLogger
from app_examples.utils.java_runner import start_java, stop_java

logging.basicConfig(
    format="[%(levelname)s] %(message)s",
    level=logging.DEBUG
)


def main():
    pattern_file = "patterns/basic_patterns.json"
    log_dir = "data/logs/main_example"

    # Start Esper
    esper_service = start_java(
        main_class="app.Main",
        jar_name="sots-uncertainty-aware-cep-0.0.1-SNAPSHOT.jar",
        java_dir="app/java",
        args=[pattern_file, log_dir],
        rebuild=True
    )


    event_stream = EventStream()

    with CSVLogger(output_dir=log_dir, name="events") as logger:
        # Subscribe logger to all partitions
        for partition in list(event_stream.partitions.keys()):
            event_stream.subscribe(logger, partition, "*")

        # Managers
        reconstruction_manager = ReconstructionManager(
            event_stream,
            "app_examples/main_example/configs/streams.json",
            "app_examples/main_example/configs/filters.json"
        )
        stream_manager = StreamManager(event_stream, "app_examples/main_example/configs/streams.json")
        stream_manager.start()

        try:
            event_stream.dispatch(timeout=1000)
        except KeyboardInterrupt:
            event_stream.stop()
            logging.info("[MAIN] Stopping pipeline")

    # --- Shutdown esper service ---
    stop_java(esper_service)


if __name__ == "__main__":
    main()
