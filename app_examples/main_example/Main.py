from app.Orchestrator import Orchestrator
from app.core.cep.cep_engine_types.EsperCEPEngine import EsperCEPEngine

def main():
    orch = Orchestrator(
        pattern_file="patterns/main_example_patterns.json",
        log_dir="data/logs/main_example",
        streams_cfg="app_examples/main_example/configs/streams.json",
        predictors_cfg="app_examples/main_example/configs/predictors.json",
        base_run_name="run",
        cep_engine_cls=EsperCEPEngine,
        cep_engine_kwargs={
            "jar_name": "sots-uncertainty-aware-cep-0.0.1-SNAPSHOT.jar",
            "java_dir": "app/java",
            "rebuild": True
        }
    )
    orch.start()

if __name__ == "__main__":
    main()
