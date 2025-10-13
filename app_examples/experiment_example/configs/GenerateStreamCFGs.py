import json
import re
from pathlib import Path

# --- Parameters ---
BEACHES = ["Calumet Beach", "Montrose Beach", "63rd Street Beach"]
NUMERIC_COLS = [
    "Water Temperature",
    "Turbidity",
    "Wave Height",
    "Wave Period",
]

# Units per variable
UNITS = {
    "Water Temperature": "C",
    "Turbidity": "NTU",
    "Wave Height": "m",
    "Wave Period": "s",
}

# Optional: predictor templates (you can change these mappings easily)
PREDICTOR_TEMPLATES = {
    "Water Temperature": "kf1",
    "Turbidity": "kf2",
    "Wave Height": "kf3",
    "Wave Period": "kf4",
}

# --- Utility Functions ---
def normalize_beach(beach: str) -> str:
    """Removes spaces and symbols from beach names for identifier consistency."""
    return re.sub(r"[^A-Za-z0-9]", "", beach)

def normalize_col(col: str) -> str:
    """Removes spaces for consistency with dataset column names."""
    return col.replace(" ", "")

# --- Config Builder ---
def build_experiment_streams():
    config = {}
    for beach in BEACHES:
        for col in NUMERIC_COLS:
            beach_key = normalize_beach(beach)
            col_key = normalize_col(col)
            stream_id = f"{beach_key}_{col_key}"

            config[stream_id] = {
                "type": "experiment_stream",
                "unit": UNITS.get(col, None),
                "datatype": "float",
                "params": {
                    "beach": beach,
                    "column": col,
                },
                "predictor_template": PREDICTOR_TEMPLATES.get(col, "kf1"),
            }
    return config

# --- Save to file ---
def save_config(config, out_path="app_examples/experiment_example/configs/streams_experiment.json"):
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)
    print(f"[OK] Generated stream config:{out_path}")

# --- Run ---
if __name__ == "__main__":
    cfg = build_experiment_streams()
    save_config(cfg)
