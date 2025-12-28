import json
import time
import os
import logging

from app.core.runtime.EventStream import EventStream
from app.core.runtime.Coordinator import Coordinator
from app.core.processor.EventProcessor import EventProcessor
from app.core.utils.EventListener.Logger import CSVLogger
from app.core.communication.ClientRegistry import get_client_class
from app.core.communication.ServerRegistry import get_server_class
from app.core.source.source_type import *
from app.core.communication.comm_types import *


__author__ = "Feyi Adesanya"

logging.basicConfig(
    format="[%(levelname)s] %(message)s",
    level=logging.INFO
)

LOG = logging.getLogger(__name__)


class Orchestrator:
    """
    Orchestrator: Main entry point into framework
    """

    def __init__(self, config_path: str):
        with open(config_path, "r") as f:
            self.cfg = json.load(f)

        self.server = None
        self.stream = None
        self.coordinator = None
        self.logger = None
        self.cep = None
        self.sources = []

        ts = time.strftime("%Y%m%d-%H%M%S")
        base_dir = self.cfg["logging"]["base_dir"]
        self.run_dir = os.path.join(base_dir, ts)
        os.makedirs(self.run_dir, exist_ok=True)

    
    # Startup
    def start(self):
        LOG.info("[ORCH] Starting pipeline")

        self._start_server()
        self._start_cep()
        self._start_eventstream()
        self._start_logger()
        self._start_coordinator()
        self._start_sources()

        LOG.info("[ORCH] Pipeline started")

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()

    
    # Components
    def _start_server(self):
        cfg = self.cfg["messaging"]
        server_cls = get_server_class(cfg["server_type"])

        self.server = server_cls(
            pub_endpoint=cfg["pub_endpoint"],
            pull_endpoint=cfg["pull_endpoint"],
        )
        self.server.run(in_thread=True)
        time.sleep(2)


    def _start_eventstream(self):
        cfg = self.cfg["messaging"]

        client_cls = get_client_class(cfg["client_type"])

        self.stream = EventStream(client_cls)
        self.stream.start()


    def _start_logger(self):
        if not self.cfg["logging"]["enabled"]:
            return

        self.logger = CSVLogger(self.run_dir)
        for partition in self.stream.partitions.keys():
            self.stream.subscribe(self.logger, partition, "*")

    def _start_coordinator(self):
        self.coordinator = Coordinator(
            event_stream=self.stream,
            sources_config_path=self.cfg["sources_config"],
            predictors_config_path=self.cfg["coordination"]["predictors_config"],
        )
        self.coordinator.start()


    
    # Sources
    def _load_sources(self):
        with open(self.cfg["sources_config"], "r") as f:
            return json.load(f)

    def _build_source(self, source_id: str, cfg: dict):
        from app.core.source.EventSourceRegistry import get_source_class

        cls = get_source_class(cfg["type"])

        return cls(
            id=source_id,
            type=cfg["datatype"],
            stream=self.stream,
            interval=cfg.get("interval"),
            value_unit=cfg.get("unit"),
            **cfg.get("params", {})
        )

    def _start_sources(self):
        sources_cfg = self._load_sources()

        for source_id, cfg in sources_cfg.items():
            src = self._build_source(source_id, cfg)
            src.start()
            self.sources.append(src)

            LOG.info(
                f"[ORCH] Started source '{source_id}' "
                f"(type={cfg['type']})"
            )

    
    # CEP
    def _start_cep(self):
        if not self.cfg["cep"]["enabled"]:
            return

        self.cep = EventProcessor(
            pattern_cfg=self.cfg["cep"]["pattern_cfg"],
            run_dir=self.run_dir,
            jar_name=self.cfg["cep"]["jar_name"],
            java_dir=self.cfg["cep"]["java_dir"],
            rebuild=self.cfg["cep"]["rebuild"],
            log_matches=str(self.cfg["cep"]["log_matches"]),
        )
        self.cep.start()
        time.sleep(3)

    
    # Shutdown
    def stop(self):
        LOG.info("[ORCH] Shutting down pipeline")

        for src in self.sources:
            src.stop()
            
        if self.coordinator:
            self.coordinator.stop()

        if self.logger:
            self.logger.close(timeout=5)

        if self.stream:
            self.stream.stop()

        if self.cep:
            self.cep.stop()

        if self.server:
            self.server.stop()

        LOG.info("[ORCH] Shutdown complete")
