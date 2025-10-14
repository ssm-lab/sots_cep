import json
import time
import logging
import os
from pathlib import Path

from .app_overrides.core.ExperimentOrchestrator import ExperimentOrchestrator
from app.core.bridge.JavaCEPBridge import JavaCEPBridge

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

BEACHES = ["Calumet Beach", "Montrose Beach", "63rd Street Beach"]
ATTRIBUTES = [
    ("Water Temperature", "C", "kf_water_temp"),
    ("Turbidity", "NTU", "kf_turbidity"),
    ("Wave Height", "m", "kf_wave_height"),
    ("Wave Period", "s", "kf_wave_period")
]

DATASETS = [
    "mar_10_rate0.1_MAR",
    "mar_20_rate0.2_MAR",
    "mar_30_rate0.3_MAR",
    "mcar_10_rate0.1_MCAR",
    "mcar_20_rate0.2_MCAR",
    "mcar_30_rate0.3_MCAR",
    "mnar_10_rate0.1_MNAR",
    "mnar_20_rate0.2_MNAR",
    "mnar_30_rate0.3_MNAR",
    "oracle_rate0.0_None"
]


class ExperimentBatchOrchestrator:
    """
    Runs multiple experiment configurations sequentially.
    Each configuration has its own generated stream config and Orchestrator instance.
    """

    def __init__(self, base_data_dir, log_dir, predictors_cfg, pattern_cfg,
                 bridge_class=JavaCEPBridge, bridge_kwargs=None):
        self.base_data_dir = Path(base_data_dir)
        self.log_dir = Path(log_dir)
        self.predictors_cfg = predictors_cfg
        self.pattern_cfg = pattern_cfg
        self.bridge_class = bridge_class
        self.bridge_kwargs = bridge_kwargs or {
            "jar_name": "sots-uncertainty-aware-cep-0.0.1-SNAPSHOT.jar",
            "java_dir": "app/java",
            "rebuild": True,
            "log_matches": "False"
        }

    def run_all(self):
        # Loop over all datasets (use slice for testing)
        # for dataset_name in DATASETS:
        for dataset_name in ["mnar_30_rate0.3_MNAR"]:
            LOG.info(f"===== Starting Experiment: {dataset_name} =====")

            dataset_file = self.base_data_dir / f"{dataset_name}.csv"
            streams_config_path = self._generate_streams_config(dataset_file)

            orch = ExperimentOrchestrator(
                pattern_cfg=self.pattern_cfg,
                log_dir=self.log_dir,
                streams_cfg=streams_config_path,
                predictors_cfg=self.predictors_cfg,
                base_run_name="run",
                dataset_name=dataset_name,
                bridge=self.bridge_class,
                bridge_kwargs=self.bridge_kwargs
            )

            try:
                orch.start()
            except KeyboardInterrupt:
                LOG.warning("[BatchOrchestrator] Interrupted manually.")
                orch.stop()
                break
            except Exception as e:
                LOG.exception(f"[BatchOrchestrator] Error in {dataset_name}: {e}")
                orch.stop()

            LOG.info(f"===== Completed Experiment: {dataset_name} =====")
            time.sleep(10)  # cooldown before next run

    def _generate_streams_config(self, dataset_file: Path):
        """Dynamically generate and write the streams config for one dataset."""
        cfg = {}

        for beach in BEACHES:
            for col_name, unit, predictor in ATTRIBUTES:
                stream_id = f"{beach.replace(' ', '_')}_{col_name.replace(' ', '_')}"
                cfg[stream_id] = {
                    "type": "experiment_stream",
                    "unit": unit,
                    "datatype": "float",
                    "interval": 0.02,
                    "params": {
                        "file": str(dataset_file),
                        "beach": beach,
                        "col": col_name,
                    },
                    "predictor_template": predictor
                }

        cfg_path = self.log_dir / f"streams_{dataset_file.stem}.json"
        os.makedirs(self.log_dir, exist_ok=True)
        with open(cfg_path, "w") as f:
            json.dump(cfg, f, indent=4)

        return str(cfg_path)
    

def main():
    batch = ExperimentBatchOrchestrator(
        base_data_dir="app_examples/experiment_example/data/processed/experiment_dfs",
        log_dir="data/logs/experiment_example",
        predictors_cfg="app_examples/experiment_example/configs/predictors_experiment.json",
        pattern_cfg="patterns/experiments_patterns.json",
    )
    batch.run_all()
    

if __name__ == "__main__":
    main()

