import numpy as np
import pandas as pd
import logging
import os

# --- CONFIGURATION ---
YEAR = 2015
START_MONTH = 5
END_MONTH = 9
BEACHES = ["Calumet Beach", "Montrose Beach", "63rd Street Beach"]
DROP_THRESHOLD = 0  # no columns dropped unless completely missing

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


# -------------------------------------------------------------------------
# Helper: Remove anomalies
# -------------------------------------------------------------------------
def remove_anomalies(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans extreme outliers or sensor error codes from numeric columns.
    Replaces invalid or physically impossible values with NaN,
    and reports how many rows were affected per column.
    """
    numeric_cols = ["Water Temperature", "Turbidity", "Wave Height", "Wave Period"]

    total_replacements = 0
    per_col_counts = {}

    # Replace known sentinel negatives (e.g., -99999)
    for col in numeric_cols:
        if col not in df.columns:
            continue
        invalid_mask = df[col] < -1000
        sentinel_count = invalid_mask.sum()
        if sentinel_count > 0:
            logging.warning(f"[CLEANUP] {col}: {sentinel_count} sentinel values replaced.")
            df.loc[invalid_mask, col] = np.nan
            per_col_counts[col] = per_col_counts.get(col, 0) + sentinel_count
            total_replacements += sentinel_count

    # Remove physically impossible or negative values
    phys_rules = {
        "Water Temperature": lambda x: x < 0,
        "Turbidity": lambda x: x < 0,
        "Wave Height": lambda x: x < 0,
        "Wave Period": lambda x: x <= 0,
    }

    for col, rule in phys_rules.items():
        if col not in df.columns:
            continue
        bad_mask = rule(df[col])
        count = bad_mask.sum()
        if count > 0:
            logging.warning(f"[CLEANUP] {col}: {count} physically impossible values removed.")
            df.loc[bad_mask, col] = np.nan
            per_col_counts[col] = per_col_counts.get(col, 0) + count
            total_replacements += count

    # Drop statistical outliers (beyond ±5σ)
    for col in numeric_cols:
        if col not in df.columns or df[col].notna().sum() < 10:
            continue
        mean = df[col].mean()
        std = df[col].std()
        if std == 0 or np.isnan(std):
            continue
        outlier_mask = (df[col] - mean).abs() > 5 * std
        outlier_count = outlier_mask.sum()
        if outlier_count > 0:
            logging.warning(f"[CLEANUP] {col}: {outlier_count} statistical outliers dropped (>5σ).")
            df.loc[outlier_mask, col] = np.nan
            per_col_counts[col] = per_col_counts.get(col, 0) + outlier_count
            total_replacements += outlier_count

    # --- Summary report ---
    if total_replacements > 0:
        logging.info("\n=== Anomaly Removal Summary ===")
        for col, count in per_col_counts.items():
            logging.info(f"  {col}: {count} values cleaned")
        logging.info(f"Total affected cells: {total_replacements}\n")
    else:
        logging.info("[CLEANUP] No anomalies detected — dataset looks clean.")

    return df


# -------------------------------------------------------------------------
# Helper: Compute statistics for pattern thresholds
# -------------------------------------------------------------------------
def compute_attribute_stats(df: pd.DataFrame, output_path: str, year, start_month, end_month):
    ATTRS = ["Water Temperature", "Turbidity", "Wave Height", "Wave Period"]

    logging.info("\n[INFO] Computing attribute thresholds for pattern generation...")

    # Per-beach stats
    beach_stats = (
        df.groupby("Beach Name")[ATTRS]
        .agg(["mean", "std", "min", "max",
              lambda x: np.percentile(x.dropna(), 5),
              lambda x: np.percentile(x.dropna(), 95)])
    )
    beach_stats.columns = ["_".join(col).strip() for col in beach_stats.columns.values]
    beach_stats = beach_stats.reset_index()

    # Global stats
    global_stats = (
        df[ATTRS]
        .agg(["mean", "std", "min", "max",
              lambda x: np.percentile(x.dropna(), 5),
              lambda x: np.percentile(x.dropna(), 95)])
    ).T
    global_stats.columns = ["mean", "std", "min", "max", "p5", "p95"]

    logging.info("\n=== Global Attribute Summary ===")
    print(global_stats.round(3))

    # Save results
    beach_json_path = os.path.join(output_path, f"pattern_thresholds_by_beach_{year}_{start_month}_{end_month}.json")
    global_json_path = os.path.join(output_path, f"pattern_thresholds_global_{year}_{start_month}_{end_month}.json")

    beach_stats.to_json(beach_json_path, orient="records", indent=2)
    global_stats.to_json(global_json_path, orient="index", indent=2)

    logging.info(f"[INFO] Saved pattern threshold summaries:\n  - {beach_json_path}\n  - {global_json_path}")
    return global_stats


# -------------------------------------------------------------------------
# Main Preprocessing
# -------------------------------------------------------------------------
def filter_year(
    file_path: str,
    year: int = YEAR,
    start_month: int = START_MONTH,
    end_month: int = END_MONTH,
    timestamp_col: str = "Measurement Timestamp",
    group_col: str = "Beach Name",
    output_path: str = None
):
    logging.info(f"Loading dataset from {file_path}")
    df = pd.read_csv(file_path)

    df.columns = df.columns.str.strip().str.replace('"', '')

    # Parse timestamp
    df[timestamp_col] = pd.to_datetime(df[timestamp_col],
                                       format="%m/%d/%Y %I:%M:%S %p",
                                       errors="coerce")
    df = df.dropna(subset=[timestamp_col])

    # Filter by season and beaches
    df = df[
        (df[timestamp_col].dt.year == year)
        & (df[timestamp_col].dt.month >= start_month)
        & (df[timestamp_col].dt.month <= end_month)
        & (df[group_col].isin(BEACHES))
    ]

    df["Readable Timestamp"] = df[timestamp_col]
    df[timestamp_col] = df[timestamp_col].apply(lambda x: float(x.timestamp()))
    df = df.sort_values([group_col, timestamp_col]).reset_index(drop=True)

    # Convert numeric cols
    NUMERIC_COLS = [
        "Water Temperature", "Turbidity", "Transducer Depth",
        "Wave Height", "Wave Period", "Battery Life"
    ]
    for col in NUMERIC_COLS:
        if col in df.columns:
            df[col] = (
                df[col].replace({",": ""}, regex=True)
                .replace("", np.nan)
                .astype(float)
            )

    # Drop overly missing columns
    missing_report = df.isna().mean().sort_values(ascending=False)
    logging.info("=== Missingness Report ===")
    for col, rate in missing_report.items():
        logging.info(f"{col}: {rate:.2%} missing")

    drop_cols = [col for col, rate in missing_report.items() if rate > DROP_THRESHOLD]
    if drop_cols:
        logging.warning(f"Dropping columns above {DROP_THRESHOLD:.0%} missingness: {drop_cols}")
        df = df.drop(columns=drop_cols)

    # Remove unused columns
    for col in ["Battery Life", "Measurement Timestamp Label"]:
        if col in df.columns:
            df = df.drop(columns=[col])

    # Remove anomalies and report how many were dropped
    df = remove_anomalies(df)

    # Drop rows missing *any* key attributes
    COMPLETE_ATTRS = ["Water Temperature", "Turbidity", "Wave Height", "Wave Period"]
    before_rows = len(df)
    df = df.dropna(subset=COMPLETE_ATTRS)
    after_rows = len(df)
    logging.info(f"[CLEANUP] Dropped {before_rows - after_rows} rows with incomplete attribute sets ({(before_rows - after_rows) / before_rows:.2%}).")

    # Sort globally by time (across all beaches)
    df = df.sort_values("Measurement Timestamp").reset_index(drop=True)

    # Save cleaned dataset
    os.makedirs(output_path, exist_ok=True)
    cleaned_path = os.path.join(output_path, f"preprocessed_{year}_{start_month}_{end_month}.csv")
    df.to_csv(cleaned_path, index=False)
    logging.info(f"Preprocessed dataset saved to {cleaned_path}")

    return df


# -------------------------------------------------------------------------
# Run Preprocessor
# -------------------------------------------------------------------------
if __name__ == "__main__":
    dataset_path = "app_examples/experiment_example/data/original/Beach_Water_Quality_-_Automated_Sensors_20250918.csv"
    output_path = "app_examples/experiment_example/data/processed"

    preprocessed_df = filter_year(dataset_path, output_path=output_path)

    # Compute threshold stats after cleaning
    compute_attribute_stats(preprocessed_df, output_path, YEAR, START_MONTH, END_MONTH)
