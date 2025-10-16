import logging
import os
import time
import threading
from app.core.communication.comm_types.ZMQClient import ZMQClient
from app.core.communication.comm_types.ZMQServer import ZMQServer
from app.core.runtime.EventStream import EventStream
from app.core.utils.EventListener.Logger import CSVLogger
from app.core.bridge.JavaCEPBridge import JavaCEPBridge
from .core.runtime.ExperimentCoordinator import ExperimentCoordinator

LOG = logging.getLogger(__name__)


class ExperimentOrchestrator:
    def __init__(self, pattern_cfg, log_dir, streams_cfg, predictors_cfg,
                 base_run_name, dataset_name=None,
                 client_type=ZMQClient, server_type=ZMQServer,
                 bridge=JavaCEPBridge, bridge_kwargs=None,
                 log_matches="False"):
        # --- basic attributes
        self.pattern_cfg = pattern_cfg
        self.log_dir = log_dir
        self.streams_cfg = streams_cfg
        self.predictors_cfg = predictors_cfg
        self.base_run_name = base_run_name
        self.client_type = client_type
        self.server_type = server_type
        self.bridge = bridge
        self.bridge_kwargs = bridge_kwargs or {}
        self.log_matches = log_matches
        self.event_stream = EventStream(client_type=self.client_type)

        # --- control flags
        self._stop_lock = threading.Lock()
        self._shutdown_triggered = False

        # --- directory structure
        dataset_id = dataset_name or self._infer_dataset_id(streams_cfg)
        self.run_dir = os.path.join(log_dir, f"{dataset_id}")
        os.makedirs(self.run_dir, exist_ok=True)
        LOG.info(f"[ExperimentOrchestrator] Using run_dir: {self.run_dir}")

        # --- runtime components (initialized in start)
        self.server = None
        self.cep_engine = None
        self.coordinator = None
        self.logger = None
        self.dispatch_thread = None

    @staticmethod
    def _infer_dataset_id(streams_cfg_path):
        filename = os.path.basename(streams_cfg_path)
        return os.path.splitext(filename)[0]

    # ------------------------------------------------------------------
    # LIFECYCLE
    # ------------------------------------------------------------------
    def start(self):
        """Full experiment lifecycle."""
        # --- start messaging server
        self.server = self.server_type()
        self.server.run(in_thread=True)
        time.sleep(3)

        # --- start CEP engine
        if self.bridge:
            self.cep_engine = self.bridge(
                pattern_cfg=self.pattern_cfg,
                run_dir=self.run_dir,
                **self.bridge_kwargs,
            )
            self.cep_engine.start()
        time.sleep(5)

        # --- create CSV logger
        self.logger = CSVLogger(self.run_dir)
        for topic in ["reconstructed"]:
            self.event_stream.subscribe(self.logger, topic, "*")

        # --- create coordinator
        self.coordinator = ExperimentCoordinator(
            event_stream=self.event_stream,
            streams_config_path=self.streams_cfg,
            predictors_config_path=self.predictors_cfg,
            on_complete=self._on_dataset_complete,
            interval=0.05,  # slightly safer default
        )
        time.sleep(3)

        # --- start event dispatch loop
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
            time.sleep(7)  # small grace for Esper flush
        self.stop()

    def stop(self):
        logging.info("[ExperimentOrchestrator] Stopping pipeline...")
        try:
            if self.coordinator:
                self.coordinator.running = False
                self.coordinator.stop()
                time.sleep(1)

            if self.event_stream:
                self.event_stream.stop()
                self.dispatch_thread.join(timeout=3)

            # --- Now it's safe to close logger
            if self.logger:
                logging.info("[ExperimentOrchestrator] Closing logger...")
                try:
                    self.logger.close(timeout=5)
                except Exception as e:
                    logging.warning(f"[ExperimentOrchestrator] Logger already closed: {e}")

            if self.cep_engine:
                self.cep_engine.stop()

            if self.server:
                self.server.stop()

            logging.info("[ExperimentOrchestrator] All stopped.")
        except Exception as e:
            logging.exception(f"[ExperimentOrchestrator] Error during stop: {e}")

