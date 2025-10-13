from app.Orchestrator import Orchestrator
from app.core.bridge.JavaCEPBridge import JavaCEPBridge
def main():
    orch = Orchestrator(
        pattern_cfg="patterns/main_example_patterns.json",
        log_dir="data/logs/main_example",
        streams_cfg="app_examples/main_example/configs/streams.json",
        predictors_cfg="app_examples/main_example/configs/predictors.json",
        base_run_name="run",
        bridge=JavaCEPBridge,
        bridge_kwargs={
            "jar_name": "sots-uncertainty-aware-cep-0.0.1-SNAPSHOT.jar",
            "java_dir": "app/java",
            "rebuild": True
        }
    )
    orch.start()

if __name__ == "__main__":
    main()
