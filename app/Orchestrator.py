import logging
import os
import time

from app.core.runtime.EventStream import EventStream
from app.core.runtime.Coordinator import Coordinator
from app.core.utils.EventListener.Logger import CSVLogger
from app.core.communication.comm_types.ZMQClient import ZMQClient
from app.core.communication.comm_types.ZMQServer import ZMQServer
from app.core.communication.Server import Server

__author__ = "Feyi Adesanya"

"""
Orchestrator: High-level controller for running the end-to-end pipeline.
Starts CEP engine, logging, and the Coordinator to manage streams + reconstructors.
Main entry point
"""

logging.basicConfig(
    format="[%(levelname)s] %(message)s",
    level=logging.INFO
)

class Orchestrator:
    def __init__(self, pattern_cfg, log_dir, streams_cfg, predictors_cfg, base_run_name,
                 client_type=ZMQClient, server_type=ZMQServer,
                 bridge=None, bridge_kwargs=None):
        self.pattern_cfg = pattern_cfg
        self.streams_cfg = streams_cfg
        self.predictors_cfg = predictors_cfg
        self.base_run_name = base_run_name

        self.client_type = client_type
        self.server: Server = server_type()

        self.coordinator = None
        self.event_stream = EventStream(client_type=self.client_type)
        self.logger = None

        self.bridge = bridge
        self.bridge_kwargs = bridge_kwargs or {}
        self.cep_engine = None

        # Generate run folder
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        self.run_dir = os.path.join(log_dir, f"{base_run_name}_{timestamp}")
        os.makedirs(self.run_dir, exist_ok=True)
        

    def start(self):
        # Start server
        self.server.run(in_thread=True)
        time.sleep(5)

        # Start up bridge
        if self.bridge:
            self.cep_engine = self.bridge(
                pattern_cfg=self.pattern_cfg,
                run_dir=self.run_dir,
                **self.bridge_kwargs
            )
            self.cep_engine.start()
        time.sleep(7)

        # Setup logger
        self.logger = CSVLogger(self.run_dir)
        for partition in self.event_stream.partitions.keys():
            self.event_stream.subscribe(self.logger, partition, "*")

        # Coordinator
        self.coordinator = Coordinator(
            event_stream=self.event_stream,
            streams_config_path=self.streams_cfg,
            predictors_config_path=self.predictors_cfg,
        )
        time.sleep(5)
        self.coordinator.start()

        try:
            self.event_stream.dispatch(timeout=1000)
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        logging.info("[ORCHESTRATOR] Stopping pipeline")
        if self.coordinator:
            self.coordinator.stop()
        if self.logger:
            self.logger.close()
        if self.cep_engine:
            self.cep_engine.stop()
        if self.server:
            self.server.stop()
        logging.info("[ORCHESTRATOR] Shutdown complete")
