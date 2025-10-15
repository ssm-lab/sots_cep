import logging
import os
import time
import threading
from app.Orchestrator import Orchestrator
from .core.runtime.ExperimentCoordinator import ExperimentCoordinator
from app.core.utils.EventListener.Logger import CSVLogger
from app.core.communication.comm_types.ZMQClient import ZMQClient
from app.core.communication.comm_types.ZMQServer import ZMQServer

LOG = logging.getLogger(__name__)

class ExperimentOrchestrator(Orchestrator):
    """
    Orchestrator for dataset-driven experiments.
    Uses callback signaling from coordinator for shutdown.
    """

    def __init__(self, pattern_cfg, log_dir, streams_cfg, predictors_cfg,
                 base_run_name, dataset_name=None,
                 client_type=ZMQClient, server_type=ZMQServer,
                 bridge=None, bridge_kwargs=None, log_matches="False"):
        super().__init__(
            pattern_cfg=pattern_cfg,
            log_dir=log_dir,
            streams_cfg=streams_cfg,
            predictors_cfg=predictors_cfg,
            base_run_name=base_run_name,
            client_type=client_type,
            server_type=server_type,
            bridge=bridge,
            bridge_kwargs=bridge_kwargs,
        )
        self.log_matches = log_matches
        self._stop_lock = threading.Lock()
        self._shutdown_triggered = False

        timestamp = time.strftime("%Y%m%d-%H%M%S")
        dataset_id = dataset_name or self._infer_dataset_id(streams_cfg)
        self.run_dir = os.path.join(
            log_dir, f"{base_run_name}_{timestamp}_{dataset_id}"
        )
        os.makedirs(self.run_dir, exist_ok=True)
        LOG.info(f"[ExperimentOrchestrator] Using run_dir: {self.run_dir}")

    @staticmethod
    def _infer_dataset_id(streams_cfg_path):
        filename = os.path.basename(streams_cfg_path)
        return os.path.splitext(filename)[0]

    def start(self):
        """Full experiment lifecycle."""
        self.server.run(in_thread=True)
        time.sleep(2)

        if self.bridge:
            self.cep_engine = self.bridge(
                pattern_cfg=self.pattern_cfg,
                run_dir=self.run_dir,
                **self.bridge_kwargs,
            )
            self.cep_engine.start()
        time.sleep(2)

        self.logger = CSVLogger(self.run_dir)
        for topic in ["reconstructed"]:
            self.event_stream.subscribe(self.logger, topic, "*")

        self.coordinator = ExperimentCoordinator(
            event_stream=self.event_stream,
            streams_config_path=self.streams_cfg,
            predictors_config_path=self.predictors_cfg,
            on_complete=self._on_dataset_complete,
        )
        time.sleep(1)

        self.dispatch_thread = threading.Thread(
            target=self.event_stream.dispatch, kwargs={"timeout": 5}, daemon=True
        )
        self.dispatch_thread.start()

        LOG.info("[ExperimentOrchestrator] Starting dataset coordinator...")
        self.coordinator.start()

        while not self._shutdown_triggered:
            time.sleep(0.5)

    def _on_dataset_complete(self):
        """Callback triggered by coordinator."""
        with self._stop_lock:
            if self._shutdown_triggered:
                return
            LOG.info("[ExperimentOrchestrator] Dataset complete callback received.")
            self._shutdown_triggered = True
            time.sleep(5) #  slight time for everything to finish up
        self.stop()

    def stop(self):
        """Cleanly stop all components."""
        LOG.info("[ExperimentOrchestrator] Stopping pipeline...")
        try:
            if hasattr(self, "coordinator"):
                self.coordinator.running = False
            if hasattr(self, "logger"):
                LOG.info("[ExperimentOrchestrator] Waiting for logger to finish...")
                self.logger.close(timeout=5) 
            if hasattr(self, "cep_engine"):
                self.cep_engine.stop()
            if hasattr(self, "server"):
                self.server.stop()
            LOG.info("[ExperimentOrchestrator] All stopped.")
        except Exception as e:
            LOG.exception(f"[ExperimentOrchestrator] Error during stop: {e}")
