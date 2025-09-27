from ..utils.UtilityFunctions import _load_json
from .Reconstructor import Reconstructor
from .predictors.predictorTypes import *
from .predictors.PredictorRegistry import get_predictor_class

class ReconstructionManager:
    def __init__(self, event_stream, streams_config_path: str, filters_config_path: str):
        self.event_stream = event_stream
        self.streams_config = _load_json(streams_config_path)
        self.filters_config = _load_json(filters_config_path)
        self.workers: dict[str, Reconstructor] = {}
        self._create_reconstructors()

    def _create_predictor(self, filter_template: str):
        cfg = self.filters_config.get(filter_template)
        ftype = cfg["type"]
        params = cfg["params"]

        cls = get_predictor_class(ftype)
        return cls(**params)

    def _create_reconstructors(self):
        for stream_id, cfg in self.streams_config.items():
            predictor = self._create_predictor(cfg.get("filter_template"))
            worker = Reconstructor(stream_id=stream_id, predictor=predictor, event_stream=self.event_stream)
            self.workers[stream_id] = worker

            # Subscribe worker to its own observed.<stream_id>
            self.event_stream.subscribe(worker, "observed", stream_id)
