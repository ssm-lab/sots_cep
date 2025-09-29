import logging
import os
import subprocess
import time
from app.core.runtime.EventStream import EventStream
from app.core.runtime.Coordinator import Coordinator
from app.core.utils.logger.Logger import CSVLogger
from app.JavaRunner import start_java, stop_java
from app.core.communication.comm_types.ZMQClient import ZMQClient
from app.core.communication.comm_types.ZMQServer import ZMQServer
from app.core.communication.Server import Server
import threading

"""
Orchestrator: High-level controller for running the end-to-end pipeline.
Starts Esper, logging, and the Coordinator to manage streams + reconstructors.
Main entry point for experiments and demos.
"""

logging.basicConfig(
    format="[%(levelname)s] %(message)s",
    level=logging.INFO
)

class Orchestrator:
    def __init__(self, pattern_file, log_dir, streams_cfg, filters_cfg, base_run_name,
                 client_type=ZMQClient, server_type=ZMQServer,
                 use_java=True, rebuild=True, 
                 jar_name="sots-uncertainty-aware-cep-0.0.1-SNAPSHOT.jar"):
        self.pattern_file = pattern_file
        self.streams_cfg = streams_cfg
        self.filters_cfg = filters_cfg
        self.use_java = use_java
        self.rebuild = rebuild
        self.jar_name = jar_name
        self.client_type = client_type

        self.esper_proc = None
        self.coordinator = None
        self.event_stream = EventStream(client_type=self.client_type)
        self.logger = None
        self.base_run_name = base_run_name

        self.server = server_type()
        self.server_thread = None


        # Generate run folder name
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        self.run_dir = os.path.join(log_dir, f"{base_run_name}_{timestamp}")
        os.makedirs(self.run_dir, exist_ok=True)

    def start(self):
        # Start ZMQ Server in background
        self.server.run(in_thread=True)

        # Start up Esper
        if self.use_java:
            self.esper_proc = start_java(
                main_class="app.Main",
                jar_name=self.jar_name,
                java_dir="app/java",
                args=[self.pattern_file, self.run_dir],
                rebuild=self.rebuild
            )

        # Setup Logger
        self.logger = CSVLogger(self.run_dir)
        for partition in self.event_stream.partitions.keys():
            self.event_stream.subscribe(self.logger, partition, "*")

        # Start Coordinator
        self.coordinator = Coordinator(
            event_stream=self.event_stream,
            streams_config_path=self.streams_cfg,
            filters_config_path=self.filters_cfg,
        )
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
        if self.esper_proc:
            stop_java(self.esper_proc)
        if self.server:
            self.server.stop()
        logging.info("[ORCHESTRATOR] Shutdown complete")
