import json
import time
import os
import logging

from app.core.runtime.EventStream import EventStream
from app.core.processor.EventProcessor import EventProcessor
from app.core.utils.EventListener.Logger import CSVLogger
from app.core.runtime.LifecycleManager import LifecycleManager

from app.core.communication.ClientRegistry import get_client_class
from app.core.communication.ServerRegistry import get_server_class

from app.core.source.source_type import *
from app.core.communication.comm_types import *
from app.core.compensator.predictor_types import *

from app.core.compensator.Reconstructor import Reconstructor
from app.core.compensator.PredictorRegistry import get_predictor_class
from app.core.runtime.ExpectedSchedule import ExpectedSchedule

from app.core.runtime.ConstituentController import ConstituentController
from app.core.utils.UtilsFuncs import load_plugins_from_package
from app.state_charts.lv4_adaptive import Statechart

load_plugins_from_package("app.core.source.source_type")
load_plugins_from_package("app.core.compensator.predictor_types")
load_plugins_from_package("app.core.communication.comm_types")

__author__ = "Feyi Adesanya"


logging.basicConfig(
    format="[%(levelname)s] %(message)s",
    level=logging.INFO
)

LOG = logging.getLogger(__name__)


class Orchestrator:
    """
    Orchestrator: system startup + constituent construction
    """

    def __init__(self, config_path: str):

        with open(config_path, "r") as f:
            self.cfg = json.load(f)

        self.server = None
        self.stream = None
        self.logger = None
        self.cep = None
        self.lifecycle = None

        self.sources = []

        ts = time.strftime("%Y%m%d-%H%M%S")
        base_dir = self.cfg["logging"]["base_dir"]

        self.run_dir = os.path.join(base_dir, ts)
        os.makedirs(self.run_dir, exist_ok=True)

    # --------------------------------------------------
    # Startup
    # --------------------------------------------------

    def start(self):

        LOG.info("[ORCH] Starting pipeline")

        self._start_server()
        self._start_cep()
        self._start_eventstream()
        self._start_logger()

        self._start_lifecycle()
        self._start_constituents()

        # --------------------------------------------------
        # Activate all constituents AFTER registration
        # --------------------------------------------------

        self.lifecycle.activate_all()

        LOG.info("[ORCH] Pipeline started")

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()

    # --------------------------------------------------
    # Messaging Server
    # --------------------------------------------------

    def _start_server(self):

        cfg = self.cfg["messaging"]

        server_cls = get_server_class(cfg["server_type"])

        self.server = server_cls(
            pub_endpoint=cfg["pub_endpoint"],
            pull_endpoint=cfg["pull_endpoint"],
        )

        self.server.run(in_thread=True)

        time.sleep(2)

    # --------------------------------------------------
    # Event Stream
    # --------------------------------------------------

    def _start_eventstream(self):

        cfg = self.cfg["messaging"]

        client_cls = get_client_class(cfg["client_type"])

        self.stream = EventStream(client_cls)

        self.stream.start()

    # --------------------------------------------------
    # Logger
    # --------------------------------------------------

    def _start_logger(self):

        if not self.cfg["logging"]["enabled"]:
            return

        self.logger = CSVLogger(self.run_dir)

        for partition in self.stream.partitions.keys():
            self.stream.subscribe(self.logger, partition, "*")

    # --------------------------------------------------
    # Lifecycle Manager
    # --------------------------------------------------

    def _start_lifecycle(self):
        self.lifecycle = LifecycleManager(self.run_dir)

    # --------------------------------------------------
    # CEP Engine
    # --------------------------------------------------

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

    # --------------------------------------------------
    # Source Config
    # --------------------------------------------------

    def _load_sources(self):

        with open(self.cfg["sources_config"], "r") as f:
            return json.load(f)

    def _build_source(self, source_id, cfg):

        from app.core.source.EventSourceRegistry import get_source_class

        cls = get_source_class(cfg["type"])

        return cls(
            id=source_id,
            type=cfg["datatype"],
            stream=self.stream,
            lifecycle=self.lifecycle,
            interval=cfg.get("interval"),
            value_unit=cfg.get("unit"),
            **cfg.get("params", {})
        )

    # --------------------------------------------------
    # Build Constituent Pipelines
    # --------------------------------------------------

    def _start_constituents(self):

        sources_cfg = self._load_sources()

        with open(self.cfg["coordination"]["predictors_config"], "r") as f:
            predictors_cfg = json.load(f)

        for source_id, cfg in sources_cfg.items():
            runtime = ConstituentController(Statechart, source_id, self.lifecycle.lifecycle_logger)

            # ----------------------------
            # Schedule

            schedule = ExpectedSchedule(
                interval=cfg.get("interval", 1.0),
                grace=cfg.get("grace", 0.1),
            )

            # ----------------------------
            # Predictor

            predictor_template = cfg["predictor_template"]
            predictor_cfg = predictors_cfg[predictor_template]
            predictor_cls = get_predictor_class(predictor_cfg["type"])
            predictor = predictor_cls(**predictor_cfg.get("params", {}))

            # ----------------------------
            # Reconstructor
            reconstructor = Reconstructor(
                source_id=source_id,
                predictor=predictor,
                event_stream=self.stream,
                lifecycle=self.lifecycle,
                schedule=schedule,
            )

            # ----------------------------
            # Event Source
            src = self._build_source(source_id, cfg)

            # ----------------------------
            # Register constituent
            self.lifecycle.register_constituent(
                source_id=source_id,
                runtime=runtime,
                event_source=src,
                reconstructor=reconstructor,
                schedule=schedule,
            )

            # Connect components to lifecycle statecharts
            src.connect()
            reconstructor.connect()

            # ----------------------------
            # Start components
            reconstructor.start()
            src.start()

            self.sources.append(src)

            LOG.info(
                f"[ORCH] Started constituent '{source_id}' "
                f"(type={cfg['type']})"
            )

    # --------------------------------------------------
    # Shutdown
    # --------------------------------------------------

    def stop(self):

        LOG.info("[ORCH] Shutting down pipeline")

        for src in self.sources:
            src.stop()

        if self.logger:
            self.logger.close(timeout=5)

        if self.stream:
            self.stream.stop()

        if self.cep:
            self.cep.stop()

        if self.server:
            self.server.stop()

        LOG.info("[ORCH] Shutdown complete")
