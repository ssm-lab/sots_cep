from app.messaging.EventStream import EventStream
from app.stream.StreamManager import StreamManager
from app.imputation.ImputersManager import ImputerManager
from app.logger.Logger import Logger
from app_examples.Main_Evaluation import evaluate_imputation 
import logging

logging.basicConfig(
    format="[%(levelname)s] %(message)s",
    level=logging.DEBUG
)

def main():
    event_stream = EventStream()

    stream_manager = StreamManager(event_stream, "app/configs/streams.json")
    imputer_manager = ImputerManager(event_stream, "app/configs/streams.json", "app/configs/filters.json")
    stream_manager.start()

    logger = Logger()
    for partition in list(event_stream.partitions.keys()):
        event_stream.subscribe(logger, partition, "*") 
   
    try:
        event_stream.dispatch(timeout=1000)
    except KeyboardInterrupt:
        event_stream.stop()
        logger.close()
        logging.info("[MAIN] Stopping pipeline")

        # run eval after closing
        logging.info("[MAIN] Running evaluation...")
        results = evaluate_imputation(logger.filepath)
        logging.info(f"[MAIN] Evaluation finished, results:\n{results}")


if __name__ == "__main__":
    main()

