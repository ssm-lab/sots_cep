from matplotlib import pyplot as plt
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


PARAM_GRID = {
    "MODES": ["position", "velocity", "acceleration"],
    "Q": [0.001, 0.005, 0.01, 0.05, 0.1, 0.2, 0.5, 1.0, 2.0],
    "R": [0.001, 0.002, 0.005, 0.01, 0.02, 0.05, 0.1, 0.2]
}

DT = 1.0
DATA_PATH = "app_examples/experiment_example/data/processed/preprocessed_2016_5_9.csv"

MISSING_RATE = 0.3     
ALPHA = 0.75  

SEED = 42
np.random.seed(SEED)

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


def mae(y_true, y_pred):
    mask = ~np.isnan(y_true)
    return np.mean(np.abs(np.array(y_true)[mask] - np.array(y_pred)[mask]))


def simulate_missingness(series, rate=0.3):
    n = len(series)
    mask = np.ones(n, dtype=bool)
    missing_idx = np.random.choice(n, int(rate * n), replace=False)
    mask[missing_idx] = False
    corrupted = series.copy()
    corrupted[~mask] = np.nan
    return corrupted, mask


def tune_for_series(values, attribute_name):
    best = {"score": float("inf"), "q": None, "r": None, "mode": None}
    series = np.array(values, dtype=np.float64)
    series = series[~np.isnan(series)]
    if len(series) < 10:
        return best
    series = (series - np.nanmean(series)) / (np.nanstd(series) + 1e-8) # Normalize series so RMSE values are around 0-1


    # simulate missingness to tune under uncertainty
    corrupted, _ = simulate_missingness(series, rate=MISSING_RATE)

    results_list = []
    for mode in PARAM_GRID["MODES"]:
        for q, r in product(PARAM_GRID["Q"], PARAM_GRID["R"]):
            kf = KalmanFilter(dt=DT, Q=q, R=r, mode=mode)
            preds, confs = [], []

            for z in corrupted:
                if np.isnan(z):
                    kf.predict()
                else:
                    kf.update(z)
                preds.append(kf.kf.x[0, 0])
                confs.append(kf.confidence())

           # Compute normalized absolute error
            preds_arr = np.array(preds)
            errors = np.abs(preds_arr - series[:len(preds_arr)])
            norm_errors = errors / (np.nanmax(errors) + 1e-8)
            confs = np.array(confs)

            # Compute correlation (confidence vs error)
            valid_mask = ~np.isnan(norm_errors) & ~np.isnan(confs)
            corr = np.corrcoef(confs[valid_mask], norm_errors[valid_mask])[0, 1] if np.sum(valid_mask) > 2 else 0.0
            corr_score = (1 + corr) / 2  # 0=good, 1=bad

            # Compute normalized RMSE
            rmse = np.sqrt(np.mean(errors ** 2))

            # Composite score (lower = better)
            score = ALPHA * rmse + (1 - ALPHA) * corr_score


            results_list.append({
                "attribute": attribute_name,
                "mode": mode,
                "Q": q,
                "R": r,
                "rmse": rmse,
                "corr_score": corr_score,
                "score": score
            })

            logging.info(f"[{mode}] Q={q:.4f}, R={r:.4f} | RMSE={rmse:.4f}, CorrScore={corr_score:.4f}, Score={score:.4f}")

            if score < best["score"]:
                best.update({"score": score, "q": q, "r": r, "mode": mode, "rmse": rmse, "corr_score": corr_score})

    return best, results_list



def main():
    np.random.seed(42)
    df = pd.read_csv(DATA_PATH)
    df.columns = df.columns.str.strip().str.replace('"', '')
    df = df[df["Beach Name"] == BEACH]

    if df.empty:
        logging.error(f"No data found for {BEACH} in {YEAR}. Check the file path or column names.")
        return

    logging.info(f"[INFO] Dataset loaded: {len(df)} rows for {BEACH}")
    results = {}
    overall_results = {}

    for col in NUMERIC_COLS:
        if col not in df.columns:
            logging.warning(f"Skipping {col} (not found in dataset).")
            continue

        logging.info(f"\n--- Tuning {col} ---")
        series = df[col].values
        best, col_results_list = tune_for_series(series, col)
        overall_results[col] = col_results_list
        if best["q"] is None:
            logging.info(f"{col:20s} | Insufficient data, skipped.")
            continue

        results[col] = {
            "process_noise": best["q"],
            "measurement_noise": best["r"],
            "mode": best["mode"],
            "rmse": best["rmse"],
            "corr_score": best["corr_score"],
            "score": best["score"],
        }

        logging.info(
            f"{col:20s} | RMSE={best['rmse']:.4f} | CorrScore={best['corr_score']:.4f} | "
            f"Score={best['score']:.4f} | Q={best['q']:.4f} | R={best['r']:.4f} | Mode={best['mode']}"
        )

    # save results
    results_df = pd.DataFrame(results).T
    results_df.to_csv("app_examples/experiment_example/configs/kalman_gridsearch_results.csv", index=True)
    logging.info("\n[INFO] Grid search complete. Results saved to kalman_gridsearch_results.csv")

    all_results_flat = []
    for attr, entries in overall_results.items():
        all_results_flat.extend(entries)

    all_results_df = pd.DataFrame(all_results_flat)
    all_results_df.to_csv("app_examples/experiment_example/configs/kalman_gridsearch_results_full.csv", index=False)
    logging.info(f"[INFO] Full grid search results saved to kalman_gridsearch_results_full.csv "
                 f"({len(all_results_flat)} rows total)")


if __name__ == "__main__":
    main()
