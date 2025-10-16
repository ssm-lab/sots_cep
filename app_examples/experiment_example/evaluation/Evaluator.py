import os
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt


# ================================================================
# CONFIGURATION
# ================================================================
BASE_DIR = "data/logs/experiment_example/CURRENT"  # change this to your actual run directory
DATASETS = [
    "oracle",
    "mar_30",
    "mar_10",
    "mcar_10",
    "mcar_30",
    "structural_10",
    "structural_30",
]
EVENT_FILE = "events.csv"
PATTERN_FILE = "patterns.csv"
TIME_TOLERANCE_SEC = 3  # tolerance in fired_offset_sec for pattern match

# ================================================================
# HELPERS
# ================================================================
def safe_load_csv(path):
    """Loads CSVs while skipping logger comments."""
    if not os.path.exists(path):
        print(f"[WARN] Missing file: {path}")
        return pd.DataFrame()
    try:
        return pd.read_csv(path, comment="#")
    except Exception as e:
        print(f"[ERROR] Failed to load {path}: {e}")
        return pd.DataFrame()


def parse_stream_id(stream_id):
    """Split stream_id into readable beach + attribute."""
    if not isinstance(stream_id, str):
        return None, None

    # Example: 63rd_Street_Beach_Water_Temperature
    parts = stream_id.split("_")
    if "Beach" in parts:
        beach_end = parts.index("Beach") + 1
        beach = " ".join(parts[:beach_end])
        attribute = " ".join(parts[beach_end:]).replace("_", " ")
    else:
        # fallback for malformed cases
        beach = " ".join(parts[:3])
        attribute = " ".join(parts[3:]).replace("_", " ")
    return beach.strip(), attribute.strip()


def evaluate_reconstruction(df):
    """Compute MAE, RMSE, and average confidence per beach+attribute."""
    if df.empty:
        return pd.DataFrame()

    metrics = []
    for stream_id in df["stream_id"].unique():
        beach, attribute = parse_stream_id(stream_id)
        if beach is None:
            continue

        sub = df[df["stream_id"] == stream_id].copy()
        if sub.empty:
            continue

        # Extract ground truth
        sub["gt"] = (
            sub["extras"]
            .astype(str)
            .str.extract(r"'ground_truth': ([0-9.\-eE]+)")[0]
            .astype(float)
        )
        sub["pred"] = pd.to_numeric(sub["value"], errors="coerce")
        sub["conf"] = pd.to_numeric(sub["confidence"], errors="coerce")

        # Drop invalid
        sub = sub.dropna(subset=["gt", "pred"])
        if len(sub) == 0:
            continue

        mae = np.mean(np.abs(sub["pred"] - sub["gt"]))
        rmse = np.sqrt(np.mean((sub["pred"] - sub["gt"]) ** 2))
        avg_conf = np.mean(sub["conf"])

        metrics.append(
            {
                "beach": beach,
                "attribute": attribute,
                "MAE": mae,
                "RMSE": rmse,
                "avg_confidence": avg_conf,
            }
        )

    return pd.DataFrame(metrics)


def compare_patterns(oracle_df, exp_df, tolerance_s=10):
    """
    Compare pattern triggers to oracle using fired_offset_sec.
    Returns TP/FP/FN counts and detailed FP/FN pattern events.
    """
    if oracle_df.empty or exp_df.empty:
        return pd.DataFrame(columns=["pattern_name", "TP", "FP", "FN", "precision", "recall", "F1", "FP_events", "FN_events"])

    results = []
    for pattern in sorted(oracle_df["pattern_name"].unique()):
        o_sub = oracle_df[oracle_df["pattern_name"] == pattern]
        e_sub = exp_df[exp_df["pattern_name"] == pattern]

        if e_sub.empty and o_sub.empty:
            continue

        tp = 0
        matched = set()
        fn_events, fp_events = [], []

        # Match oracle vs experimental triggers by tolerance
        for _, o_row in o_sub.iterrows():
            o_time = o_row.get("fired_offset_sec", np.nan)
            if pd.isna(o_time):
                continue
            diffs = e_sub["fired_offset_sec"].apply(lambda t: abs(t - o_time))
            if not diffs.empty and diffs.min() <= tolerance_s:
                tp += 1
                matched.add(diffs.idxmin())
            else:
                fn_events.append(round(o_time, 3))

        # Remaining un-matched experiment triggers → FP
        unmatched_exp = e_sub.loc[~e_sub.index.isin(matched)]
        if not unmatched_exp.empty:
            fp_events = unmatched_exp["fired_offset_sec"].round(3).tolist()

        fp = len(fp_events)
        fn = len(fn_events)

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

        results.append(
            {
                "pattern_name": pattern,
                "TP": tp,
                "FP": fp,
                "FN": fn,
                "precision": precision,
                "recall": recall,
                "F1": f1,
                "FP_events": fp_events,
                "FN_events": fn_events,
            }
        )

    return pd.DataFrame(results)


# ================================================================
# MAIN EVALUATION PIPELINE
# ================================================================
def main():
    oracle_events = safe_load_csv(os.path.join(BASE_DIR, "oracle", EVENT_FILE))
    oracle_patterns = safe_load_csv(os.path.join(BASE_DIR, "oracle", PATTERN_FILE))

    all_recon = []
    all_patterns = []

    for dataset in DATASETS:
        print(f"\n[INFO] Evaluating {dataset}...")
        ds_dir = os.path.join(BASE_DIR, dataset)
        if not os.path.exists(ds_dir):
            print(f"[WARN] Skipping missing dataset {dataset}")
            continue

        events_path = os.path.join(ds_dir, EVENT_FILE)
        patterns_path = os.path.join(ds_dir, PATTERN_FILE)
        df_events = safe_load_csv(events_path)
        df_patterns = safe_load_csv(patterns_path)

        # 1️⃣ Reconstruction metrics
        recon_df = evaluate_reconstruction(df_events)
        recon_df["dataset"] = dataset
        all_recon.append(recon_df)

        # 2️⃣ Pattern-level metrics
        cmp_df = compare_patterns(oracle_patterns, df_patterns, tolerance_s=TIME_TOLERANCE_SEC)
        cmp_df["dataset"] = dataset
        all_patterns.append(cmp_df)

    # Combine and export
    out_dir = os.path.join(BASE_DIR, "evaluation_results")
    os.makedirs(out_dir, exist_ok=True)

    recon_all = pd.concat(all_recon, ignore_index=True)
    pattern_all = pd.concat(all_patterns, ignore_index=True)

    # Export detailed event reconstruction results
    recon_all.to_csv(os.path.join(out_dir, "reconstruction_metrics_detailed.csv"), index=False)

    # Group by dataset, beach, and attribute
    per_beach_attr = (
        recon_all.groupby(["dataset", "beach", "attribute"])
        [["MAE", "RMSE", "avg_confidence"]]
        .mean()
        .reset_index()
    )
    per_beach_attr.to_csv(os.path.join(out_dir, "reconstruction_metrics_per_beach_attr.csv"), index=False)

    # Export pattern comparison results
    pattern_all.to_csv(os.path.join(out_dir, "pattern_comparison_per_pattern.csv"), index=False)

    # Print results
    print("\n=== Reconstruction Metrics (Per Beach + Attribute) ===")
    print(per_beach_attr.round(3).to_string(index=False))

    print("\n=== Dataset Summary (Averaged) ===")
    summary = (
        per_beach_attr.groupby("dataset")[["MAE", "RMSE", "avg_confidence"]].mean().round(3)
    )
    print(summary)

    print("\n=== Pattern Match Summary (Per Pattern) ===")
    print(pattern_all[["dataset", "pattern_name", "TP", "FP", "FN", "precision", "recall", "F1"]].round(3).to_string(index=False))

    print(f"\n[INFO] Exported results to {out_dir}")











    # summary by dataset, beach, and attribute
    per_beach_attr = recon_all.groupby(["dataset", "beach", "attribute"]).mean().reset_index()

    # summary for patterns
    # Keep only numeric columns for averaging
    numeric_cols = pattern_all.select_dtypes(include=[np.number]).columns
    pattern_summary = (
        pattern_all.groupby(["dataset", "pattern_name"])[numeric_cols]
        .mean()
        .reset_index()
    )


    # dataset-level averages
    dataset_summary = (
        per_beach_attr.groupby("dataset")[["MAE", "RMSE", "avg_confidence"]].mean()
        .round(3)
        .reset_index()
    )
    dataset_summary.to_latex("dataset_summary.tex", index=False, float_format="%.3f")


    os.makedirs("figures", exist_ok=True)
    sns.set_theme(style="whitegrid", palette="deep")

    for dataset in per_beach_attr["dataset"].unique():
        df_sub = per_beach_attr[per_beach_attr["dataset"] == dataset]

        # === Reconstruction plot ===
        plt.figure(figsize=(9,6))
        sns.barplot(
            data=df_sub,
            x="attribute", y="MAE", hue="beach"
        )
        plt.title(f"Reconstruction MAE per Beach and Attribute — {dataset}")
        plt.xlabel("")
        plt.ylabel("MAE")
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(f"figures/{dataset}_recon_mae.pdf")
        plt.close()

        # === Pattern precision/recall plot ===
        df_pattern_sub = pattern_all[pattern_all["dataset"] == dataset]
        pattern_melted = df_pattern_sub.melt(
            id_vars=["pattern_name"],
            value_vars=["precision", "recall"],
            var_name="metric", value_name="score"
        )

        plt.figure(figsize=(10,6))
        sns.barplot(
            data=pattern_melted,
            x="pattern_name", y="score", hue="metric"
        )
        plt.title(f"Pattern Precision and Recall — {dataset}")
        plt.xticks(rotation=90)
        plt.ylabel("Score")
        plt.ylim(0, 1)
        plt.tight_layout()
        plt.savefig(f"figures/{dataset}_pattern_precision_recall.pdf")
        plt.close()






if __name__ == "__main__":
    main()
