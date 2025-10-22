import pandas as pd
import numpy as np
import os
import logging

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


def analyze_confidence_from_events(events_path: str, output_path: str = None):
    """
    Analyzes confidence evolution per Beach × Attribute from an events.csv log file.

    Parameters
    ----------
    events_path : str
        Path to events.csv (should include columns like 'Beach Name', 'Attribute', 'confidence').
    output_path : str, optional
        Path to save the resulting confidence summary CSV.

    Returns
    -------
    pd.DataFrame
        Summary matrix of confidence statistics per beach and attribute.
    """
    if not os.path.exists(events_path):
        raise FileNotFoundError(f"Could not find events file: {events_path}")

    df = pd.read_csv(events_path,  comment="#")
    df.columns = df.columns.str.strip().str.replace('"', '')

    # Try to infer attribute and beach names if not explicitly present
    if "Attribute" not in df.columns:
        # Extract attribute name from stream_id if necessary (e.g., "Montrose_Beach_Water_Temperature")
        if "stream_id" in df.columns:
            df["Attribute"] = df["stream_id"].apply(
                lambda x: (
                    x.split("_")[-2] + " " + x.split("_")[-1]
                    if len(x.split("_")) > 2
                    else x
                ).replace("_", " ").title()
            )
        else:
            raise ValueError("No 'Attribute' or 'stream_id' column found in events.csv")

    if "Beach Name" not in df.columns:
        if "stream_id" in df.columns:
            df["Beach Name"] = df["stream_id"].apply(
                lambda x: (
                    " ".join(x.split("_")[:-2])
                    if len(x.split("_")) > 2
                    else x
                ).replace("_", " ").title()
            )
        else:
            raise ValueError("No 'Beach Name' or 'stream_id' column found in events.csv")

    if "confidence" not in df.columns:
        raise ValueError("Missing required column 'confidence' in events.csv")

    # Remove NaN/confidence=0 (invalid)
    df = df[df["confidence"].notna() & (df["confidence"] > 0)]

    results = []
    for (beach, attr), group in df.groupby(["Beach Name", "Attribute"]):
        confs = group["confidence"].dropna().values
        if len(confs) < 3:
            continue

        mean_c = np.mean(confs)
        std_c = np.std(confs)
        min_c, max_c = np.min(confs), np.max(confs)
        coeff_var = std_c / (mean_c + 1e-8)
        iqr = np.percentile(confs, 75) - np.percentile(confs, 25)
        skew = pd.Series(confs).skew()
        kurt = pd.Series(confs).kurt()

        results.append({
            "Beach": beach,
            "Attribute": attr,
            "Mean Confidence": mean_c,
            "StdDev": std_c,
            "Min": min_c,
            "Max": max_c,
            "CoeffVar (σ/μ)": coeff_var,
            "IQR (P75-P25)": iqr,
            "Skew": skew,
            "Kurtosis": kurt,
            "Samples": len(confs)
        })

    summary = pd.DataFrame(results).sort_values(["Beach", "Attribute"]).reset_index(drop=True)

    # Optional output
    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        summary.to_csv(output_path, index=False)
        logging.info(f"[INFO] Confidence summary saved to: {output_path}")

    logging.info(f"[INFO] Summary matrix computed for {len(summary)} beach–attribute pairs.")
    return summary


if __name__ == "__main__":
    # Example run:
    EVENTS_PATH = "data/logs/experiment_example/Kalman Filter/hybrid_10/events.csv"
    OUTPUT_PATH = "data/logs/experiment_example/Kalman Filter/evaluation_results/confidence_analysis_summary.csv"

    matrix = analyze_confidence_from_events(EVENTS_PATH, OUTPUT_PATH)
    print("\n=== Confidence Stability Matrix ===")
    print(matrix.to_string(index=False))
