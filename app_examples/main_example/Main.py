from app.Orchestrator import Orchestrator

def main():
    orch = Orchestrator(
        pattern_file="patterns/main_example_patterns.json",
        log_dir="data/logs/main_example",
        streams_cfg="app_examples/main_example/configs/streams.json",
        filters_cfg="app_examples/main_example/configs/filters.json",
        base_run_name="run",
        use_java=True,
        rebuild=True
    )
    orch.start()

if __name__ == "__main__":
    main()
