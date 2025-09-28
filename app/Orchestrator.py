import logging
import subprocess
from app.core.runtime.EventStream import EventStream
from app.core.runtime.Coordinator import Coordinator
from app.core.utils.logger.Logger import CSVLogger
from app.JavaRunner import start_java, stop_java

"""
Orchestrator: High-level controller for running the end-to-end pipeline.
Starts Esper, logging, and the Coordinator to manage streams + reconstructors.
Main entry point for experiments and demos.
"""

class Orchestrator:
    def __init__(self, pattern_file, log_dir, streams_cfg, filters_cfg,
                 use_java=True, rebuild=True, jar_name="sots-uncertainty-aware-cep-0.0.1-SNAPSHOT.jar"):
        self.pattern_file = pattern_file
        self.log_dir = log_dir
        self.streams_cfg = streams_cfg
        self.filters_cfg = filters_cfg
        self.use_java = use_java
        self.rebuild = rebuild
        self.jar_name = jar_name

        self.esper_proc = None
        self.coordinator = None
        self.event_stream = EventStream()
        self.logger = None

    def start(self):
        # Start up Esper
        if self.use_java:
            self.esper_proc = start_java(
                main_class="app.Main",
                jar_name=self.jar_name,
                java_dir="app/java",
                args=[self.pattern_file, self.log_dir],
                rebuild=self.rebuild
            )

        # Setup Logger
        self.logger = CSVLogger(output_dir=self.log_dir, name="events")
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
        if self.server_proc:
            self.server_proc.terminate()
            self.server_proc.wait()
            logging.info("[ORCHESTRATOR] Server stopped")
        logging.info("[ORCHESTRATOR] Shutdown complete")
