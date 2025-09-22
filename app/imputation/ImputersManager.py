import json
import logging
from app.imputation.Imputer import Imputer
from app.imputation.predictors.Predictor import KalmanFilter


class ImputerManager:
    """
    Creates and manages imputers that consume observed events and publish imputed events.
    """
    def __init__(self, event_stream, streams_config_path: str, filters_config_path: str):
        self.event_stream = event_stream
        self.streams_config = self._load_json(streams_config_path)
        self.filters_config = self._load_json(filters_config_path)
        self.workers: dict[str, Imputer] = {}
        self._create_workers()

    def _load_json(self, path: str) -> dict:
        with open(path, "r") as f:
            return json.load(f)

    def _create_predictor(self, filter_template: str):
        cfg = self.filters_config.get(filter_template)
        ftype = cfg["type"]
        params = cfg["params"]

        if ftype == "KalmanFilter":
            return KalmanFilter(**params)

    def _create_workers(self):
        for stream_id, cfg in self.streams_config.items():
            predictor = self._create_predictor(cfg.get("filter_template"))
            worker = Imputer(stream_id=stream_id, predictor=predictor, event_stream=self.event_stream)
            self.workers[stream_id] = worker

            # Subscribe worker to observed.<id>
            self.event_stream.subscribe(worker, "observed", stream_id)
            logging.info(f"[IMPUTER-MANAGER] Worker for {stream_id} subscribed to observed.{stream_id}")
