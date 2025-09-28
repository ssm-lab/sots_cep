import logging
from app.Orchestrator import Orchestrator

logging.basicConfig(
    format="[%(levelname)s] %(message)s",
    level=logging.DEBUG
)

def main():
    orch = Orchestrator(
        pattern_file="patterns/basic_patterns.json",
        log_dir="data/logs/main_example",
        streams_cfg="app_examples/main_example/configs/streams.json",
        filters_cfg="app_examples/main_example/configs/filters.json",
        use_java=True,
        rebuild=True
    )
    orch.start()

if __name__ == "__main__":
    main()
