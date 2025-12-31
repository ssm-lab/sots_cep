import numpy as np
import pandas as pd
import logging
from itertools import product
from app.core.reconstruction.predictor_types.Filters import KalmanFilter


# ================================================================
# CONFIGURATION
# ================================================================
YEAR = 2016
BEACH = "Montrose Beach"
NUMERIC_COLS = ["Water Temperature", "Turbidity", "Wave Height", "Wave Period"]

PARAM_GRID = {
    "MODES": ["position", "velocity", "acceleration"],
    "Q": [0.01, 0.05, 0.1, 0.2, 0.5, 1.0, 2.0],
    "R": [0.01, 0.02, 0.05, 0.1, 0.2]
}

DT = 1.0
DATA_PATH = "app_examples/experiment_example/configs/hybrid_grid_20.csv"
SEED = 42
np.random.seed(SEED)

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


# ================================================================
# CORE TUNING FUNCTION
# ================================================================
def tune_for_series(measured, groundtruth, attribute_name):
    """
    Tunes Kalman Filter parameters (Q, R, mode) for a single attribute,
    using measured values with real missingness and groundtruth for evaluation.
    """
    best = {"rmse": float("inf"), "norm_rmse": float("inf"), "q": None, "r": None, "mode": None}
    measured = np.array(measured, dtype=np.float64)
    groundtruth = np.array(groundtruth, dtype=np.float64)

    # Skip if too few valid values
    valid_mask = ~np.isnan(groundtruth)
    if valid_mask.sum() < 10:
        return best, []

    std_dev = np.std(groundtruth[valid_mask]) + 1e-8
    results_list = []

    for mode in PARAM_GRID["MODES"]:
        for q, r in product(PARAM_GRID["Q"], PARAM_GRID["R"]):
            kf = KalmanFilter(dt=DT, Q=q, R=r, mode=mode)
            preds = []

            for z in measured:
                if np.isnan(z):
                    kf.predict()
                else:
                    kf.update(z)
                preds.append(kf.kf.x[0, 0])

            preds = np.array(preds)
            rmse = np.sqrt(np.nanmean((preds - groundtruth) ** 2))
            norm_rmse = rmse / std_dev

            results_list.append({
                "attribute": attribute_name,
                "mode": mode,
                "Q": q,
                "R": r,
                "rmse": rmse,
                "norm_rmse": norm_rmse
            })

            logging.info(f"[{mode}] Q={q:.4f}, R={r:.4f} | RMSE={rmse:.4f} | NormRMSE={norm_rmse:.4f}")

            if rmse < best["rmse"]:
                best.update({
                    "rmse": rmse,
                    "norm_rmse": norm_rmse,
                    "q": q,
                    "r": r,
                    "mode": mode
                })

    return best, results_list


# ================================================================
# MAIN ROUTINE
# ================================================================
def main():
    np.random.seed(SEED)
    df = pd.read_csv(DATA_PATH)
    df.columns = df.columns.str.strip().str.replace('"', '')

    # Filter to one beach for tuning
    df = df[df["Beach Name"] == BEACH]
    if df.empty:
        logging.error(f"No data found for {BEACH} in {YEAR}.")
        return

    logging.info(f"[INFO] Dataset loaded: {len(df)} rows for {BEACH}")

    results = {}
    all_results = []

    for col in NUMERIC_COLS:
        if col not in df.columns:
            logging.warning(f"Skipping {col} (not found in dataset).")
            continue

        gt_col = f"{col}_groundtruth"
        if gt_col not in df.columns:
            logging.warning(f"Skipping {col} (no groundtruth column).")
            continue

        logging.info(f"\n--- Tuning {col} ---")
        best, entries = tune_for_series(df[col].values, df[gt_col].values, col)
        all_results.extend(entries)

        if best["q"] is None:
            logging.info(f"{col:20s} | Insufficient data, skipped.")
            continue

        results[col] = {
            "process_noise": best["q"],
            "measurement_noise": best["r"],
            "mode": best["mode"],
            "rmse": best["rmse"],
            "norm_rmse": best["norm_rmse"]
        }

        logging.info(
            f"{col:20s} | Best RMSE={best['rmse']:.4f} | NormRMSE={best['norm_rmse']:.4f} | "
            f"Q={best['q']:.4f} | R={best['r']:.4f} | Mode={best['mode']}"
        )

    # ------------------------------------------------------------
    # Save results
    # ------------------------------------------------------------
    summary_path = "app_examples/experiment_example/configs/kalman_gridsearch_results.csv"
    full_path = "app_examples/experiment_example/configs/kalman_gridsearch_results_full.csv"

    results_df = pd.DataFrame(results).T
    results_df.to_csv(summary_path, index=True)
    logging.info(f"[INFO] Summary results saved to {summary_path}")

    all_results_df = pd.DataFrame(all_results)
    all_results_df.to_csv(full_path, index=False)
    logging.info(f"[INFO] Full grid search results saved ({len(all_results_df)} runs total)")


# ================================================================
# ENTRY POINT
# ================================================================
if __name__ == "__main__":
    main()
