from app.core.runtime.LifecycleManager import ConstituentContext, LifecycleManager
from app_examples.experiments.overrides.ExperimentConstituentController import ExperimentConstituentController

class ExperimentLifecycleManager(LifecycleManager):

    def __init__(self, run_dir, clock, scenario):
        super().__init__(run_dir)

        self.clock = clock
        self.scenario = scenario

    def register_constituent(
        self,
        source_id,
        statechart_cls,
        event_source,
        reconstructor,
        schedule
    ):

        runtime = ExperimentConstituentController(
            statechart_cls=statechart_cls,
            constituent_id=source_id,
            lifecycle_logger=self.lifecycle_logger,
            clock=self.clock,
            scenario=self.scenario.name()
        )

        ctx = ConstituentContext(
            source_id=source_id,
            runtime=runtime,
            event_source=event_source,
            reconstructor=reconstructor,
            schedule=schedule
        )

        self.constituents[source_id] = ctx