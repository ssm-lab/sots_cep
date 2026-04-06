import json
import os
import logging
import time

from app.core.source.EventSourceRegistry import get_source_class

from .ExperimentEventStream import ExperimentEventStream
from app.core.processor.EventProcessor import EventProcessor
from app.core.utils.EventListener.Logger import CSVLogger
from app.core.communication.comm_types.ZMQClient import ZMQClient
from app.core.communication.comm_types.ZMQServer import ZMQServer
from app.core.communication.ClientRegistry import get_client_class
from app.core.communication.ServerRegistry import get_server_class

from app.core.source.source_type import *
from app.core.communication.comm_types import *
from app.core.compensator.predictor_types import *
from app_examples.experiments.overrides.sources import *

from .ExperimentReconstructor import ExperimentReconstructor, ExperimentalExpectedSchedule
from app.core.compensator.PredictorRegistry import get_predictor_class

from app.core.utils.UtilsFuncs import load_plugins_from_package
from app.state_charts.lv4_adaptive import Statechart

load_plugins_from_package("app.core.source.source_type")
load_plugins_from_package("app.core.compensator.predictor_types")
load_plugins_from_package("app.core.communication.comm_types")
load_plugins_from_package("app_examples.experiments.overrides.sources")

from app_examples.experiments.overrides.ExperimentLifecycleManager import ExperimentLifecycleManager

LOG = logging.getLogger(__name__)

class ExperimentOrchestrator:

    def __init__(self, config_path: str, scenario, clock):

        with open(config_path, "r") as f:
            self.cfg = json.load(f)

        self.clock = clock
        self.scenario = scenario

        self.server = None
        self.stream = None
        self.logger = None
        self.cep = None
        self.lifecycle = None

        self.sources = []
        self.reconstructors = []

        base_dir = self.cfg["logging"]["base_dir"]
        self.run_dir = os.path.join(base_dir, f"experiment_{scenario.name()}")
        os.makedirs(self.run_dir, exist_ok=True)

    def _start_server(self):

        cfg = self.cfg["messaging"]

        server_cls = get_server_class(cfg["server_type"])

        self.server = server_cls(
            pub_endpoint=cfg["pub_endpoint"],
            pull_endpoint=cfg["pull_endpoint"],
        )

        self.server.run(in_thread=True)

    def _start_eventstream(self):

        cfg = self.cfg["messaging"]

        client_cls = get_client_class(cfg["client_type"])

        self.stream = ExperimentEventStream(client_cls)

    def _start_logger(self):

        if not self.cfg["logging"]["enabled"]:
            return

        self.logger = CSVLogger(self.run_dir)

        for partition in self.stream.partitions.keys():
            self.stream.subscribe(self.logger, partition, "*")

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

    def _start_lifecycle(self):

        self.lifecycle = ExperimentLifecycleManager(
            run_dir=self.run_dir,
            clock=self.clock,
            scenario=self.scenario
        )

    def _load_sources(self):

        with open(self.cfg["sources_config"], "r") as f:
            return json.load(f)

    def _build_source(self, source_id, cfg):

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

    def _start_constituents(self):

        sources_cfg = self._load_sources()

        with open(self.cfg["coordination"]["predictors_config"], "r") as f:
            predictors_cfg = json.load(f)

        for source_id, cfg in sources_cfg.items():

            # ----------------------------
            # Schedule (EXPERIMENTAL)
            schedule = ExperimentalExpectedSchedule(
                interval=cfg.get("interval", 1.0),
                clock=self.clock,
            )

            # ----------------------------
            # Predictor
            predictor_template = cfg["predictor_template"]
            predictor_cfg = predictors_cfg[predictor_template]

            predictor_cls = get_predictor_class(predictor_cfg["type"])
            predictor = predictor_cls(**predictor_cfg.get("params", {}))

            # ----------------------------
            # Reconstructor
            reconstructor = ExperimentReconstructor(
                source_id=source_id,
                predictor=predictor,
                event_stream=self.stream,
                lifecycle=self.lifecycle,
                schedule=schedule,
                clock=self.clock,
            )

            # ----------------------------
            # Event Source
            src = self._build_source(source_id, cfg)

            if hasattr(src, "override_observation"):
                src.override_observation(self.scenario, self.clock)

            # ----------------------------
            # Register with lifecycle
            self.lifecycle.register_constituent(
                source_id=source_id,
                statechart_cls=Statechart,
                event_source=src,
                reconstructor=reconstructor,
                schedule=schedule,
            )

            # Connect components
            src.connect()
            reconstructor.connect()

            self.sources.append(src)
            self.reconstructors.append(reconstructor)

            LOG.info(f"[EXPERIMENT] Started constituent '{source_id}'")


    def _apply_scenario_state(self, t):
        for src in self.sources:
            source_id = src.id

            # Health
            current_health = self.lifecycle.get_health(source_id)
            new_health = self.scenario.get_health(
                t,
                current_health,
                source_id
            )
            if new_health != current_health:
                self.lifecycle.set_health(source_id, new_health)

            # Belonging
            current_belonging = self.lifecycle.get_belonging(source_id)

            goal = self.scenario.get_belonging(
                t,
                current_belonging["sub"],
                source_id
            )

            if goal is None:
                return

            try:
                runtime = self.lifecycle.get_runtime(source_id)
                runtime.step_towards_belonging(goal)

            except Exception as e:
                logging.debug(
                    f"[LIFECYCLE] Step blocked for {source_id}: {e}"
                )

    def run(self, T=5):

        LOG.info(f"[EXPERIMENT] Running scenario: {self.scenario.name()}")

        self._start_server()
        self._start_cep()
        self._start_eventstream()
        self._start_logger()

        self._start_lifecycle()
        self._start_constituents()

        self.lifecycle.activate_all()


        # Simulation loop
        for _ in range(T):

            self.clock.tick()
            t = self.clock.now()

            # Apply state changes
            self._apply_scenario_state(t)

            # Generate events
            for src in self.sources:
                src.step(t)

            # Dispatch events
            self.stream.dispatch(timeout=0.5)

            # Reconstruction step
            for r in self.reconstructors:
                r.step()

            time.sleep(0.1)

        self.stop()



    def stop(self):
        LOG.info("[EXPERIMENT] Stopping")

        if self.logger:
            self.logger.close(timeout=5)

        if self.stream:
            self.stream.stop()

        if self.cep:
            self.cep.stop()

        if self.server:
            self.server.stop()

        LOG.info("[EXPERIMENT] Complete")