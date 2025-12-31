import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import logging
from app.core.reconstruction.predictor_types.Filters import KalmanFilter


# ================================================================
# CONFIGURATION
# ================================================================
YEAR = 2016
BEACH = "Montrose Beach"
NUMERIC_COLS = ["Water Temperature", "Turbidity", "Wave Height", "Wave Period"]

DT = 1.0
DATA_PATH = "app_examples/experiment_example/configs/hybrid_grid_20.csv"
SEED = 42
np.random.seed(SEED)

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


# ================================================================
# CORE KF EXECUTION
# ================================================================
def run_with_alpha(series, groundtruth, Q, R, alpha):
    """
    Runs the Kalman filter with confidence tracking.
    Uses existing NaNs in `series` (no synthetic missingness).
    """
    kf = KalmanFilter(dt=DT, Q=Q, R=R, initial_value=series[0], mode="position", alpha=alpha)
    preds, confs, errors = [], [], []

    for i, val in enumerate(series):
        pred = kf.predict()

        if not np.isnan(val):
            kf.update(val)
            c = kf.confidence(observed_value=val)
        else:
            c = kf.confidence()

        preds.append(pred)
        confs.append(c)

        gt = groundtruth[i]
        errors.append(abs(pred - gt) if not np.isnan(gt) else np.nan)

    return np.array(preds), np.array(confs), np.array(errors)


# ================================================================
# MAIN ROUTINE
# ================================================================
def main():
    df = pd.read_csv(DATA_PATH)
    df.columns = df.columns.str.strip().str.replace('"', '')
    df = df[df["Beach Name"] == BEACH].reset_index(drop=True)

    if df.empty:
        logging.error(f"No data found for {BEACH} in {YEAR}.")
        return

    logging.info(f"[INFO] Dataset loaded: {len(df)} rows for {BEACH}")

    # Best parameters from your prior grid search
    tuned_params = {
        "Water Temperature": {"Q": 2.0, "R": 0.01},
        "Turbidity": {"Q": 2.0, "R": 0.01},
        "Wave Height": {"Q": 2.0, "R": 0.01},
        "Wave Period": {"Q": 0.05, "R": 0.02},
    }

    alpha_candidates = np.linspace(0.1, 1.0, 10)
    best_alphas, correlations, variability = {}, {}, {}
    results = {}

    # ------------------------------------------------------------
    # Alpha tuning per attribute
    # ------------------------------------------------------------
    for attr in NUMERIC_COLS:
        if attr not in df.columns or f"{attr}_groundtruth" not in df.columns:
            logging.warning(f"Skipping {attr} (missing column).")
            continue

        series = df[attr].values
        groundtruth = df[f"{attr}_groundtruth"].values

        best_corr, best_a = np.inf, None
        for a in alpha_candidates:
            _, confs, errors = run_with_alpha(series, groundtruth,
                                              tuned_params[attr]["Q"],
                                              tuned_params[attr]["R"],
                                              alpha=a)
            corr = np.corrcoef(confs, errors, rowvar=False)[0, 1]
            if corr < best_corr:
                best_corr, best_a = corr, a

        best_alphas[attr] = best_a
        correlations[attr] = best_corr
        results[attr] = (series, groundtruth)

        series_std = np.nanstd(series)
        series_mean = np.nanmean(series)
        variability[attr] = series_std / (series_mean + 1e-8)

        logging.info(f"{attr}: best α={best_a:.2f}, corr={best_corr:.3f}, CV={variability[attr]:.3f}")

    # ------------------------------------------------------------
    # Global alpha
    # ------------------------------------------------------------
    global_alpha = np.mean(list(best_alphas.values()))
    print(f"\nGlobal α (mean): {global_alpha:.2f}\n")

    # ------------------------------------------------------------
    # Visualization
    # ------------------------------------------------------------
    fig, axes = plt.subplots(len(NUMERIC_COLS), 2, figsize=(13, 11))
    summary_rows = []

    for i, attr in enumerate(NUMERIC_COLS):
        if attr not in results:
            continue

        series, groundtruth = results[attr]
        preds, confs, errors = run_with_alpha(series, groundtruth,
                                              tuned_params[attr]["Q"],
                                              tuned_params[attr]["R"],
                                              alpha=global_alpha)
        t = np.arange(len(series))

        window = max(5, len(series) // 50)
        rolling_std = pd.Series(series).rolling(window, center=True).std().to_numpy()

        # Left: Ground truth vs prediction
        ax1 = axes[i, 0]
        ax12 = ax1.twinx()

        ax1.plot(t, groundtruth, color="black", lw=1.3, label="Ground Truth")
        ax1.plot(t, preds, color="orange", lw=1.2, alpha=0.8, label="KF Prediction")
        ax12.plot(t, confs, color="#1f77b4", lw=1.8, label="Confidence")
        ax1.fill_between(t, groundtruth - rolling_std, groundtruth + rolling_std,
                         color="gray", alpha=0.15, label="Variability (±σ)")

        ax1.set_title(f"{attr} | Truth & Confidence (α={global_alpha:.2f})")
        ax1.set_xlabel("Time step")
        ax1.set_ylabel(attr)
        ax12.set_ylabel("Confidence [0–1]", color="#1f77b4")
        ax1.grid(alpha=0.3)
        if i == 0:
            ax1.legend(loc="upper left", fontsize=8)
            ax12.legend(loc="upper right", fontsize=8)

        # Right: Confidence vs Error
        ax2 = axes[i, 1]
        ax2.scatter(confs, errors, alpha=0.6)
        z = np.polyfit(confs, errors, 1)
        p = np.poly1d(z)
        ax2.plot(confs, p(confs), "r--", label=f"Fit (corr={correlations[attr]:.3f})")
        ax2.set_xlabel("Confidence")
        ax2.set_ylabel("Absolute Error (|pred - truth|)")
        ax2.set_title(f"{attr} | α*={best_alphas[attr]:.2f}")
        ax2.grid(alpha=0.3)
        ax2.legend()

        summary_rows.append([
            attr,
            f"{best_alphas[attr]:.2f}",
            f"{correlations[attr]:.3f}",
            f"{np.nanmean(confs):.3f}",
            f"{np.nanmean(errors):.3f}",
            f"{variability[attr]:.3f}"
        ])

    plt.tight_layout()
    plt.show()

    # ------------------------------------------------------------
    # Summary table
    # ------------------------------------------------------------
    summary_df = pd.DataFrame(summary_rows,
        columns=["Attribute", "Best α", "Corr(Conf,Err)", "Mean Conf", "Mean Abs Err", "CoeffVar (σ/μ)"])
    print("\n=== Summary ===")
    print(summary_df.to_string(index=False))
    summary_df.to_csv("app_examples/experiment_example/configs/kalman_confidence_results_real.csv", index=False)
    logging.info("[INFO] Results saved to kalman_confidence_results_real.csv")


# ================================================================
# ENTRY POINT
# ================================================================
if __name__ == "__main__":
    main()
