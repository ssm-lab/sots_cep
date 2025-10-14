import logging
import os
import time
from app.Orchestrator import Orchestrator
from ..core.runtime.ExperimentCoordinator import ExperimentCoordinator
from app.core.utils.EventListener.Logger import AsyncCSVLogger, CSVLogger
from app.core.communication.comm_types.ZMQClient import ZMQClient
from app.core.communication.comm_types.ZMQServer import ZMQServer

LOG = logging.getLogger(__name__)


class ExperimentOrchestrator(Orchestrator):
    """
    Specialized orchestrator for dataset-driven experiments.
    Automatically appends dataset name to run_dir and uses ExperimentCoordinator.
    """

    def __init__(self, pattern_cfg, log_dir, streams_cfg, predictors_cfg,
                 base_run_name, dataset_name=None,
                 client_type=ZMQClient, server_type=ZMQServer,
                 bridge=None, bridge_kwargs=None, log_matches = "False"):
        super().__init__(
            pattern_cfg=pattern_cfg,
            log_dir=log_dir,
            streams_cfg=streams_cfg,
            predictors_cfg=predictors_cfg,
            base_run_name=base_run_name,
            client_type=client_type,
            server_type=server_type,
            bridge=bridge,
            bridge_kwargs=bridge_kwargs
        )
        self.log_matches = log_matches

        timestamp = time.strftime("%Y%m%d-%H%M%S")
        dataset_id = dataset_name or self._infer_dataset_id(streams_cfg)

        self.run_dir = os.path.join(
            log_dir,
            f"{base_run_name}_{timestamp}_{dataset_id}"
        )
        os.makedirs(self.run_dir, exist_ok=True)
        LOG.info(f"[ExperimentOrchestrator] Using run_dir: {self.run_dir}")

    @staticmethod
    def _infer_dataset_id(streams_cfg_path):
        """Extract dataset identifier from the stream config filename if possible."""
        filename = os.path.basename(streams_cfg_path)
        dataset_id = os.path.splitext(filename)[0]
        return dataset_id

    def start(self):
        """Run full experiment pipeline with ExperimentCoordinator."""
        # Start ZMQ server
        self.server.run(in_thread=True)
        time.sleep(5)

        # Start up Java bridge
        if self.bridge:
            self.cep_engine = self.bridge(
                pattern_cfg=self.pattern_cfg,
                run_dir=self.run_dir,
                **self.bridge_kwargs
            )
            self.cep_engine.start()
        time.sleep(7)


        # self.logger = CSVLogger(self.run_dir)
        self.logger = AsyncCSVLogger(self.run_dir)
        for partition in self.event_stream.partitions.keys():
            self.event_stream.subscribe(self.logger, partition, "*")

        self.coordinator = ExperimentCoordinator(
            event_stream=self.event_stream,
            streams_config_path=self.streams_cfg,
            predictors_config_path=self.predictors_cfg,
        )
        time.sleep(5)
        self.coordinator.start()

        try:
            self.event_stream.dispatch(timeout=5)
        except KeyboardInterrupt:
            self.stop()
        except Exception as e:
            LOG.exception(f"[ExperimentOrchestrator] Runtime error: {e}")
            self.stop()
