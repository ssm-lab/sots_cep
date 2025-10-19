import os
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt


# ================================================================
# CONFIGURATION
# ================================================================
PATTERN_LEVEL_KEYWORDS = {
    "atomic": [
        "HighTurbidity",
        "HighWave",
        "HighWavePeriod",
        "LowWaterTemp",
    ],
    "local_complex": [
        "LocalAlert",
    ],
    "distributed_complex": [
        "Regional",
        "AlertSpread",
    ],
}


# ================================================================
# PIPELINE
# ================================================================
class EvaluationPipeline:
    def __init__(
        self,
        base_dir,
        datasets,
        event_file="events.csv",
        pattern_file="patterns.csv",
        tolerances=[1.0],
        confidence_thresholds=[0.65, 0.75, 0.85, 0.95],
    ):
        self.base_dir = base_dir
        self.datasets = datasets
        self.event_file = event_file
        self.pattern_file = pattern_file
        self.tolerances = tolerances if isinstance(tolerances, (list, tuple)) else [tolerances]
        self.confidence_thresholds = confidence_thresholds
        self.out_dir = os.path.join(base_dir, "evaluation_results")
        os.makedirs(self.out_dir, exist_ok=True)

        print(f"[INIT] Evaluating tolerances={self.tolerances}, confidence thresholds={self.confidence_thresholds}")

        # Build or load master CSV
        self.master_df = self.build_master_summary(force_recompute=False)

    # ----------------------------------------------------------------------
    # Core Utilities
    # ----------------------------------------------------------------------
    def safe_load_csv(self, path):
        if not os.path.exists(path):
            print(f"[WARN] Missing file: {path}")
            return pd.DataFrame()
        try:
            return pd.read_csv(path, comment="#")
        except Exception as e:
            print(f"[ERROR] Failed to load {path}: {e}")
            return pd.DataFrame()

    def classify_pattern(self, pname):
        pname = str(pname)
        for level, keys in PATTERN_LEVEL_KEYWORDS.items():
            if any(k in pname for k in keys):
                return level
        return "other"

    # ----------------------------------------------------------------------
    # Reconstruction Metrics
    # ----------------------------------------------------------------------
    def evaluate_reconstruction(self, df):
        """Compute MAE, RMSE, and average confidence per stream."""
        if df.empty:
            return pd.DataFrame()

        metrics = []
        for sid in df["stream_id"].unique():
            sub = df[df["stream_id"] == sid].copy()
            sub["gt"] = sub["extras"].astype(str).str.extract(r"'ground_truth': ([0-9.\-eE]+)")[0].astype(float)
            sub["pred"] = pd.to_numeric(sub["value"], errors="coerce")
            sub["conf"] = pd.to_numeric(sub["confidence"], errors="coerce")
            sub = sub.dropna(subset=["gt", "pred"])
            if len(sub) == 0:
                continue

            mae = np.mean(np.abs(sub["pred"] - sub["gt"]))
            rmse = np.sqrt(np.mean((sub["pred"] - sub["gt"]) ** 2))
            avg_conf = np.mean(sub["conf"])

            metrics.append({"stream_id": sid, "MAE": mae, "RMSE": rmse, "avg_confidence": avg_conf})

        return pd.DataFrame(metrics)

    # ----------------------------------------------------------------------
    # Pattern Matching
    # ----------------------------------------------------------------------
    def compare_patterns(self, oracle_df, exp_df, tol, conf_thr):
        """One-to-one matching between oracle and experimental pattern triggers."""
        if oracle_df.empty or exp_df.empty:
            return pd.DataFrame(columns=["pattern_name", "TP", "FP", "FN", "precision", "recall", "F1"])

        if "confidence" in exp_df.columns:
            exp_df = exp_df[exp_df["confidence"] >= conf_thr]

        results = []
        for pattern in sorted(oracle_df["pattern_name"].unique()):
            o_sub = oracle_df[oracle_df["pattern_name"] == pattern].dropna(subset=["fired_offset_sec"]).sort_values("fired_offset_sec")
            e_sub = exp_df[exp_df["pattern_name"] == pattern].dropna(subset=["fired_offset_sec"]).sort_values("fired_offset_sec")

            if o_sub.empty and e_sub.empty:
                continue

            o_times, e_times = o_sub["fired_offset_sec"].tolist(), e_sub["fired_offset_sec"].tolist()
            tp, matched_o, matched_e = 0, set(), set()
            fn_events, fp_events = [], []

            for i, o_time in enumerate(o_times):
                best_j, best_diff = None, float("inf")
                for j, e_time in enumerate(e_times):
                    if j in matched_e:
                        continue
                    diff = abs(e_time - o_time)
                    if diff < best_diff:
                        best_diff, best_j = diff, j
                if best_j is not None and best_diff <= tol:
                    tp += 1
                    matched_o.add(i)
                    matched_e.add(best_j)
                else:
                    fn_events.append(round(o_time, 3))

            for j, e_time in enumerate(e_times):
                if j not in matched_e:
                    fp_events.append(round(e_time, 3))

            fp, fn = len(fp_events), len(fn_events)
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0
            f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

            results.append({
                "pattern_name": pattern,
                "TP": tp, "FP": fp, "FN": fn,
                "precision": precision, "recall": recall, "F1": f1,
                "tolerance_s": tol, "confidence_thr": conf_thr
            })

        return pd.DataFrame(results)

    # ----------------------------------------------------------------------
    # Build Unified Master Summary
    # ----------------------------------------------------------------------
    def build_master_summary(self, force_recompute=False):
        master_path = os.path.join(self.out_dir, "pattern_hierarchy_master_summary.csv")
        if not force_recompute and os.path.exists(master_path):
            print(f"[INFO] Found existing master summary → {master_path}")
            return pd.read_csv(master_path)

        print(f"[BUILD] Creating master summary from scratch...")

        oracle_patterns = self.safe_load_csv(os.path.join(self.base_dir, "oracle", self.pattern_file))
        recon_dict = {}

        # --- Step 1: gather reconstruction metrics per dataset ---
        for dataset in self.datasets:
            df_events = self.safe_load_csv(os.path.join(self.base_dir, dataset, self.event_file))
            recon = self.evaluate_reconstruction(df_events)
            if not recon.empty:
                recon_summary = recon[["MAE", "RMSE", "avg_confidence"]].mean().to_dict()
                recon_dict[dataset] = recon_summary

        # --- Step 2: pattern metrics across tolerance × confidence grid ---
        all_records = []
        for conf_thr in self.confidence_thresholds:
            for tol in self.tolerances:
                print(f"[EVAL] tol={tol:.2f}s, conf≥{conf_thr:.2f}")
                for dataset in self.datasets:
                    df_patterns = self.safe_load_csv(os.path.join(self.base_dir, dataset, self.pattern_file))
                    cmp_df = self.compare_patterns(oracle_patterns, df_patterns, tol, conf_thr)
                    cmp_df["dataset"] = dataset
                    cmp_df["level"] = cmp_df["pattern_name"].apply(self.classify_pattern)

                    # attach reconstruction metrics
                    if dataset in recon_dict:
                        cmp_df["MAE"] = recon_dict[dataset]["MAE"]
                        cmp_df["RMSE"] = recon_dict[dataset]["RMSE"]
                        cmp_df["avg_confidence"] = recon_dict[dataset]["avg_confidence"]

                    all_records.append(cmp_df)

        master_df = pd.concat(all_records, ignore_index=True)
        master_df.to_csv(master_path, index=False)
        print(f"[INFO] Master summary saved → {master_path}")
        return master_df

    # ----------------------------------------------------------------------
    # Summaries & Plots (from master_df)
    # ----------------------------------------------------------------------
    def summarize_hierarchy(self):
        """Compact summaries grouped by dataset, level, tolerance, and confidence."""
        df = self.master_df.copy()
        summary = (
            df.groupby(["dataset", "level", "tolerance_s", "confidence_thr"])
            [["TP","FP","FN","precision","recall","F1","MAE","RMSE","avg_confidence"]]
            .mean().round(3).reset_index()
        )

        print("\n=== Compact Hierarchy Summary (sample) ===")
        print(summary.head(12).to_string(index=False))
        return summary
    



        # ----------------------------------------------------------------------
    # Reconstruction Results Summary (per attribute)
    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    # Reconstruction Results Summary (per dataset × attribute)
    # ----------------------------------------------------------------------
    def summarize_reconstruction_by_attribute(self, metric="MAE"):
        """
        Summarize reconstruction performance (MAE or RMSE) per dataset × attribute.
        Skips oracle and structural datasets.
        
        Parameters
        ----------
        metric : str, optional
            Either 'MAE' or 'RMSE'. Controls which metric to display/export.
        """
        assert metric in ["MAE", "RMSE"], "[ERROR] metric must be 'MAE' or 'RMSE'."
        print(f"\n[INFO] Summarizing reconstruction performance per dataset and attribute ({metric})...")

        all_recon = []
        for dataset in self.datasets:
            if dataset == "oracle" or dataset.startswith("structural"):
                continue

            df_events = self.safe_load_csv(os.path.join(self.base_dir, dataset, self.event_file))
            if df_events.empty:
                continue
            recon_df = self.evaluate_reconstruction(df_events)
            if recon_df.empty:
                continue

            # --- Extract attribute robustly ---
            def parse_attribute_from_stream_id(stream_id):
                if not isinstance(stream_id, str):
                    return "Unknown"
                parts = stream_id.split("_")
                if "Beach" in parts:
                    beach_end = parts.index("Beach") + 1
                    attr = " ".join(parts[beach_end:]).replace("_", " ").strip()
                else:
                    attr = " ".join(parts[2:]).replace("_", " ").strip()
                return attr if attr else "Unknown"

            recon_df["attribute"] = recon_df["stream_id"].apply(parse_attribute_from_stream_id)
            recon_df["dataset"] = dataset
            all_recon.append(recon_df)

        if not all_recon:
            print("[WARN] No reconstruction data found.")
            return

        recon_all = pd.concat(all_recon, ignore_index=True)

        # --- Aggregate: mean per dataset × attribute ---
        summary = (
            recon_all.groupby(["dataset", "attribute"])[metric]
            .mean()
            .round(3)
            .reset_index()
            .sort_values(["attribute", "dataset"])
        )

        print(f"\n=== Reconstruction {metric} per Dataset × Attribute ===")
        print(summary.to_string(index=False))

        # --- Pivot for LaTeX-friendly table ---
        pivot = summary.pivot(index="attribute", columns="dataset", values=metric)

        # --- Export to LaTeX ---
        caption = f"Reconstruction performance ({metric}) per dataset and attribute (averaged across beaches)."
        label = f"tab:recon_{metric.lower()}_per_dataset_attribute"
        latex_path = os.path.join(self.out_dir, f"reconstruction_{metric.lower()}_per_dataset_attribute.tex")

        with open(latex_path, "w") as f:
            f.write(
                pivot.to_latex(
                    float_format="%.3f",
                    caption=caption,
                    label=label,
                    multicolumn=True,
                    multicolumn_format="c",
                )
            )
        print(f"[INFO] LaTeX table saved → {latex_path}")

        return pivot
    
    # ----------------------------------------------------------------------
    # Summary F1 Matrix (Confidence Threshold × Pattern Level)
    # ----------------------------------------------------------------------
    def summarize_f1_confidence_matrix(self, tolerance=1.0):
        """
        Generate a numeric F1-score matrix (no heatmap) showing the average
        F1 across confidence thresholds for a fixed temporal tolerance.
        Exports to LaTeX.
        """
        df = self.master_df.copy()
        if df.empty:
            print("[WARN] No master_df available for summary matrix.")
            return

        # Filter for the representative tolerance
        df = df[np.isclose(df["tolerance_s"], tolerance)]
        if df.empty:
            print(f"[WARN] No entries found for tolerance={tolerance}")
            return

        # Aggregate across datasets for cleaner summary
        pivot = (
            df.groupby(["level", "confidence_thr"])["F1"]
            .mean()
            .unstack()
            .round(3)
            .sort_index()
        )

        print(f"\n=== F1 Summary Matrix (Tolerance = {tolerance:.1f}s) ===")
        print(pivot.to_string())

        # --- Export LaTeX table ---
        caption = (
            f"Average F1-scores across confidence thresholds and pattern levels "
            f"(fixed tolerance = {tolerance:.1f}s)."
        )
        label = f"tab:f1_confidence_summary_t{int(tolerance*10)}"
        latex_path = os.path.join(self.out_dir, f"f1_confidence_summary_t{tolerance:.1f}s.tex")

        latex_str = pivot.to_latex(
            float_format="%.3f",
            caption=caption,
            label=label,
            multicolumn=True,
            multicolumn_format="c",
        )

        wrapped = (
            "\\begin{table}[H]\n"
            "\\centering\n"
            + latex_str
            + "\\end{table}\n"
        )

        with open(latex_path, "w") as f:
            f.write(wrapped)

        print(f"[INFO] LaTeX summary table saved → {latex_path}")

        return pivot







    









    # ----------------------------------------------------------------------
    # Visualizations and Charts
    # ----------------------------------------------------------------------








# ================================================================
# EXECUTION
# ================================================================
if __name__ == "__main__":
    BASE_DIR = "data/logs/experiment_example/Kalman Filter"
    DATASETS = ["oracle", "structural_10", "structural_20", "structural_30", "hybrid_10", "hybrid_20", "hybrid_30"]

    pipeline = EvaluationPipeline(
        BASE_DIR,
        DATASETS,
        tolerances=[0.1, 0.25, 0.5, 1.0],
        confidence_thresholds=[0.65, 0.75, 0.85, 0.95],
    )

    pipeline.summarize_reconstruction_by_attribute()
    pipeline.summarize_reconstruction_by_attribute(metric="MAE")
    pipeline.summarize_f1_confidence_matrix(tolerance=0.5)

