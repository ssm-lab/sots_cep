import numpy as np
import pandas as pd
import logging
from itertools import product
from app.core.reconstruction.predictor_types.Filters import KalmanFilter


YEAR = 2016
BEACH = "Montrose Beach"

NUMERIC_COLS = [
    "Water Temperature",
    "Turbidity",
    "Wave Height",
    "Wave Period",
]

MODES = ["position", "velocity", "acceleration"]

PARAM_GRID = {
    "Q": [0.10, 0.20, 0.30, 0.45, 0.60, 0.75],
    "R": [0.001, 0.0015, 0.002, 0.003, 0.004, 0.006, 0.01],
}

DT = 1.0  # hour interval
DATA_PATH = "app_examples/experiment_example/data/processed/preprocessed_2016_5_9.csv"

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


def mae(y_true, y_pred):
    mask = ~np.isnan(y_true)
    return np.mean(np.abs(np.array(y_true)[mask] - np.array(y_pred)[mask]))


def tune_for_series(values):
    best = {"mae": float("inf"), "q": None, "r": None, "mode": None}
    series = np.array(values, dtype=np.float64)
    series = series[~np.isnan(series)]
    if len(series) < 10:
        return best

    for mode in MODES:
        for q, r in product(PARAM_GRID["Q"], PARAM_GRID["R"]):
            kf = KalmanFilter(dt=DT, Q=q, R=r, mode=mode)
            preds = []
            for z in series:
                kf.update(z)
                preds.append(kf.predict())
            err = mae(series, preds)
            if err < best["mae"]:
                best.update({"mae": err, "q": q, "r": r, "mode": mode})
    return best


def main():
    df = pd.read_csv(DATA_PATH)
    df.columns = df.columns.str.strip().str.replace('"', '')
    df = df[df["Beach Name"] == BEACH]

    if df.empty:
        logging.error(f"No data found for {BEACH} in {YEAR}. Check the file path or column names.")
        return

    logging.info(f"[INFO] Dataset loaded: {len(df)} rows for {BEACH}")
    logging.info(df[NUMERIC_COLS].describe())
    print("\n")

    results = {}

    for col in NUMERIC_COLS:
        if col not in df.columns:
            logging.warning(f"Skipping {col} (not found in dataset).")
            continue

        series = df[col].values
        best = tune_for_series(series)
        if best["q"] is None:
            logging.info(f"{col:20s} | Insufficient data, skipped.")
            continue

        results[col] = {
            "process_noise": best["q"],
            "measurement_noise": best["r"],
            "mode": best["mode"],
            "mae": best["mae"],
        }

        logging.info(
            f"{col:20s} | MAE={best['mae']:.4f} | Q={best['q']:.5f} | R={best['r']:.5f} | Mode={best['mode']}"
        )
if __name__ == "__main__":
    main()
