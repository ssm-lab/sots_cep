from app.Orchestrator import Orchestrator
from app.core.processor.EventProcessor import EventProcessor

# Run with: python -m app_example.main_example.Main

def main():
    orch = Orchestrator(
        config_path="app_examples/main_example/configs/config.json"
    )
    orch.start()

if __name__ == "__main__":
    main()
