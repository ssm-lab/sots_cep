import time

from app_examples.experiments.overrides.ExperimentOrchestrator import ExperimentOrchestrator
from app_examples.experiments.runner.ExperimentClock import SimulationClock
from app_examples.experiments.runner.Scenarios import *
def main():
    config_path = "app_examples/experiments/configs/config.json"

    clock = SimulationClock()
    scenario = LifecycleEvaluationScenario()

    orchestrator = ExperimentOrchestrator(
        config_path=config_path,
        scenario=scenario,
        clock=clock
    )
    orchestrator.run(T=500)
    time.sleep(5)

if __name__ == "__main__":
    main()