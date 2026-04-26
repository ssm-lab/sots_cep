import logging
import time
from typing import Dict
from dataclasses import dataclass, field

from ..utils.EventListener.Logger import LifecycleLogger


@dataclass
class ConstituentContext:

    source_id: str
    runtime: object
    event_source: object
    reconstructor: object
    schedule: object

    last_event_ts: float = field(default_factory=time.time)

class LifecycleManager:

    def __init__(self, run_dir: str):
        self.constituents: Dict[str, ConstituentContext] = {}
        self.lifecycle_logger = LifecycleLogger(run_dir)

    def register_constituent(
        self,
        source_id,
        runtime,
        event_source,
        reconstructor,
        schedule
    ):
        ctx = ConstituentContext(
            source_id=source_id,
            runtime=runtime,
            event_source=event_source,
            reconstructor=reconstructor,
            schedule=schedule
        )

        self.constituents[source_id] = ctx
        logging.info(f"[LIFECYCLE] Registered {source_id}")


    def get_state(self, source_id):
        ctx = self.constituents.get(source_id)
        if not ctx:
            return None

        return ctx.runtime.state_snapshot()

    def get_runtime(self, source_id):
        ctx = self.constituents.get(source_id)
        if not ctx:
            return None

        return ctx.runtime


    def activate_all(self):
        logging.info("[LIFECYCLE] Activating all constituents")
        for source_id, ctx in self.constituents.items():
            runtime = ctx.runtime
            try:
                runtime.ensure_participating()
            except Exception as e:
                logging.warning(
                    f"[LIFECYCLE] Failed to activate {source_id}: {e}"
                )

    def apply_initial_lifecycle(self, sources_cfg):
        logging.info("[LIFECYCLE] Applying initial lifecycle configuration")

        for source_id, cfg in sources_cfg.items():
            lifecycle_cfg = cfg.get("default_lifecycle_state", {})
            belonging = lifecycle_cfg.get("initial_belonging")
            health = lifecycle_cfg.get("initial_health")

            if belonging:
                self.set_belonging(source_id, belonging)
            if health:
                self.set_health(source_id, health)


    def set_health(self, source_id, new_health):
        ctx = self.constituents.get(source_id)
        if not ctx:
            return

        runtime = ctx.runtime
        current = runtime.health_name()

        if current == new_health:
            return

        try:
            runtime.ensure_health(new_health)

            logging.info(f"[LIFECYCLE] {source_id} health → {new_health}")

        except Exception as e:
            logging.warning(f"[LIFECYCLE] Failed health update for {source_id}: {e}")


    def get_health(self, source_id):
        ctx = self.constituents.get(source_id)
        if not ctx:
            return None

        return ctx.runtime.health_name()
    

    def set_belonging(self, source_id, new_belonging):
        ctx = self.constituents.get(source_id)
        if not ctx:
            return

        runtime = ctx.runtime
        current = runtime.belonging_substate()

        if current == new_belonging:
            return

        try:
            success = runtime.ensure_belonging(new_belonging)

            logging.info(
                f"[LIFECYCLE] {source_id} belonging step → {new_belonging} "
                f"[success={success}]"
            )

        except Exception as e:
            logging.warning(
                f"[LIFECYCLE] Failed belonging update for {source_id}: {e}"
            )

    def get_belonging(self, source_id):
        ctx = self.constituents.get(source_id)
        if not ctx:
            return None

        runtime = ctx.runtime

        return {
            "main": runtime.belonging_main(),
            "sub": runtime.belonging_substate()
        }

    def print_states(self):
        for source_id, ctx in self.constituents.items():
            state = ctx.runtime.state_snapshot()
            logging.info(
                f"{source_id} | "
                f"{state['belonging_main']} / {state['belonging_sub']} | "
                f"{state['health_main']}"
    )

    def close(self):
        self.lifecycle_logger.close()
