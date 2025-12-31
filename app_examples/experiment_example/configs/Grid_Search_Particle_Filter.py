import numpy as np
import pandas as pd
import logging
from itertools import product
from tqdm import tqdm
from app.core.reconstruction.predictor_types.Filters import ParticleFilter

YEAR = 2016
BEACH = "Montrose Beach"

NUMERIC_COLS = [
    "Water Temperature",
    "Turbidity",
    "Wave Height",
    "Wave Period",
]

PARAM_GRID = {
    "process_std": [0.001, 0.005, 0.01, 0.05, 0.1, 0.2, 0.3],
    "meas_std": [0.002, 0.005, 0.01, 0.02, 0.03],
    "num_particles": [100, 250, 500, 750, 1000],
}

DT = 1.0
DATA_PATH = "app_examples/experiment_example/data/processed/preprocessed_2016_5_9.csv"

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

def mae(y_true, y_pred):
    mask = ~np.isnan(y_true)
    return np.mean(np.abs(np.array(y_true)[mask] - np.array(y_pred)[mask]))

def tune_for_series(values, outer_pbar):
    best = {"mae": float("inf"), "process_std": None, "meas_std": None, "num_particles": None}
    series = np.array(values, dtype=np.float64)
    series = series[~np.isnan(series)]
    if len(series) < 10:
        return best
    combos = list(product(PARAM_GRID["num_particles"], PARAM_GRID["process_std"], PARAM_GRID["meas_std"]))
    with tqdm(total=len(combos), leave=False, ncols=100, position=outer_pbar.pos + 1) as pbar:
        for n_particles, p_std, m_std in combos:
            pf = ParticleFilter(num_particles=n_particles, process_std=p_std, meas_std=m_std, initial_value=series[0])
            preds = []
            for z in series:
                pf.update(z)
                preds.append(pf.predict())
            err = mae(series, preds)
            if err < best["mae"]:
                best.update({"mae": err, "process_std": p_std, "meas_std": m_std, "num_particles": n_particles})
                pbar.set_postfix({"MAE": f"{err:.4f}", "proc": p_std, "meas": m_std, "part": n_particles})
            pbar.update(1)
    return best

def main():
    df = pd.read_csv(DATA_PATH)
    df.columns = df.columns.str.strip().str.replace('"', '')
    df = df[df["Beach Name"] == BEACH]
    if df.empty:
        logging.error(f"No data found for {BEACH} in {YEAR}.")
        return
    logging.info(f"[INFO] Dataset loaded: {len(df)} rows for {BEACH}")
    logging.info(df[NUMERIC_COLS].describe())
    print()
    results = {}
    with tqdm(NUMERIC_COLS, desc="Tuning Variables", ncols=100, position=0) as outer_pbar:
        for col in outer_pbar:
            series = df[col].values
            best = tune_for_series(series, outer_pbar)
            if best["process_std"] is None:
                continue
            results[col] = best
            logging.info(f"{col:20s} | MAE={best['mae']:.4f} | proc_std={best['process_std']:.3f} | meas_std={best['meas_std']:.3f} | particles={best['num_particles']}")


if __name__ == "__main__":
    main()
