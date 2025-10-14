import numpy as np
import pandas as pd
import logging
import os

# Most full seasonal peroid with the selected beaches that have the most amount of days
YEAR = 2015
START_MONTH = 5
END_MONTH = 9
BEACHES = ["Calumet Beach", "Montrose Beach", "63rd Street Beach"]
DROP_THRESHOLD = 0.05

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

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
    df[timestamp_col] = pd.to_datetime(
        df[timestamp_col],
        format="%m/%d/%Y %I:%M:%S %p",
        errors="coerce"
    )
    
    df = df.dropna(subset=[timestamp_col])

    # Filter by year, season, and selected beaches
    df = df[
        (df[timestamp_col].dt.year == year) &
        (df[timestamp_col].dt.month >= start_month) &
        (df[timestamp_col].dt.month <= end_month) &
        (df[group_col].isin(BEACHES))
    ]

    df["Readable Timestamp"] = df[timestamp_col]
    print(df.columns)
    df[timestamp_col] = df[timestamp_col].apply(lambda x: float(x.timestamp()))

    # Sort
    df = df.sort_values([group_col, timestamp_col]).reset_index(drop=True)

    


    # Convert numeric cols
    NUMERIC_COLS = [
            "Water Temperature",
            "Turbidity",
            "Transducer Depth",
            "Wave Height",
            "Wave Period",
            "Battery Life"
        ]

    for col in NUMERIC_COLS:
        df[col] = (
            df[col]
            .replace({",": ""}, regex=True)   # remove commas
            .replace("", np.nan)              # treat empty as NaN
            .astype(float)                    # convert to float
        )

    # Drop columns with too many missing values
    missing_report = df.isna().mean().sort_values(ascending=False)
    logging.info("=== Missingness Report ===")
    for col, rate in missing_report.items():
        logging.info(f"{col}: {rate:.2%} missing")

    drop_cols = [col for col, rate in missing_report.items() if rate > DROP_THRESHOLD]
    if drop_cols:
        logging.warning(f"\nDropping columns above {DROP_THRESHOLD:.0%} missingness: {drop_cols}")
        df = df.drop(columns=drop_cols)

    # Remove unnecessary cols
    df = df.drop(columns=['Battery Life', 'Measurement Timestamp Label'])

    # Save
    df.to_csv(os.path.join(output_path,  f"preprocessed_{year}_{start_month}_{end_month}.csv"), index=False)
    logging.info(f"\nPreprocessed dataset saved to {output_path}")

    return df

def analyze_and_preprocess(df, timestamp_col="Readable Timestamp", group_col="Beach Name", output_dir="data/processed"):
    os.makedirs(output_dir, exist_ok=True)

    df["Date"] = df[timestamp_col].dt.date

    # Contingency table (counts per day per beach)
    contingency = df.groupby([group_col, "Date"]).size().unstack(fill_value=0)

    logging.info("\n=== Contingency Table for amount of measurements per day ===")
    print(contingency)

if __name__ == "__main__":
    dataset_path = "app_examples/experiment_example/data/original/Beach_Water_Quality_-_Automated_Sensors_20250918.csv"
    output_path = "app_examples/experiment_example/data/processed"
    preprocessed_df = filter_year(dataset_path, output_path=output_path)
    analyze_and_preprocess(preprocessed_df, output_dir="app_examples/experiment_example/data/processed")
