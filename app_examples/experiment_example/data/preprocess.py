import json
import logging
import os
import numpy as np
import pandas as pd
from typing import Union, List

import numpy as np
import pandas as pd
from typing import Union, List, Optional

class MissingnessInjector:
    def __init__(self, rate: float, mode: str = "MCAR", seed: int = 42, block_size: int = 12):
        self.rate = rate
        self.mode = mode.upper()
        self.seed = seed
        self.block_size = block_size
        np.random.seed(self.seed)

    def inject(
        self, 
        df: pd.DataFrame, 
        value_cols: Union[str, List[str]],
        group_col: Optional[str] = None
    ) -> pd.DataFrame:
        if isinstance(value_cols, str):
            value_cols = [value_cols]

        if group_col:
            processed = []
            for group_name, group in df.groupby(group_col):
                injected = self._inject_group(group, value_cols)
                processed.append(injected)
            return pd.concat(processed).sort_values("Measurement Timestamp").reset_index(drop=True)
        else:
            return self._inject_group(df, value_cols)

    def _inject_group(self, df: pd.DataFrame, value_cols: List[str]) -> pd.DataFrame:
        uncertain_df = df.copy()
        n = len(uncertain_df)

        for col in value_cols:
            uncertain_df[f"{col}_groundtruth"] = uncertain_df[col].copy()
            k = int(self.rate * n)  # number of rows to drop
            if k == 0:
                continue

            if self.mode == "MCAR":
                drop_idx = np.random.choice(n, size=k, replace=False)
                uncertain_df.iloc[drop_idx, uncertain_df.columns.get_loc(col)] = np.nan

            elif self.mode == "MAR":
                drop_idx = []
                while len(drop_idx) < k:
                    start = np.random.randint(0, max(1, n - self.block_size))
                    end = min(start + self.block_size, n)
                    drop_idx.extend(range(start, end))
                drop_idx = drop_idx[:k]  # trim extra
                uncertain_df.iloc[drop_idx, uncertain_df.columns.get_loc(col)] = np.nan

            elif self.mode == "MNAR":
                ref_values = pd.to_numeric(uncertain_df[col], errors="coerce")
                if ref_values.isnull().all():
                    continue
                probs = (ref_values - ref_values.min()) / (ref_values.max() - ref_values.min() + 1e-9)
                probs = probs / probs.sum()  # normalize
                drop_idx = np.random.choice(n, size=k, replace=False, p=probs)
                uncertain_df.iloc[drop_idx, uncertain_df.columns.get_loc(col)] = np.nan
            elif self.mode == None:
                return uncertain_df # oracle, nothing missing
            else:
                raise ValueError(f"Unknown missingness mode: {self.mode}")

        return uncertain_df


# Complete full 24hr readings timelines and flag structural gaps
def expand_to_hourly(
    df,
    value_cols,
    timestamp_col="Readable Timestamp",
    group_col="Beach Name"
):
    all_groups = []
    for group_name, group in df.groupby(group_col):
        group = group.copy()

        # Ensure timestamp is datetime
        group[timestamp_col] = pd.to_datetime(group[timestamp_col], errors="coerce")
        group = group.set_index(timestamp_col)

        full_index = pd.date_range(
            start=group.index.min().floor("h"),
            end=group.index.max().ceil("h"),
            freq="h"
        )

        expanded = group.reindex(full_index)

        expanded[group_col] = group_name

        # Structural gap = when all value cols are missing (true missing row)
        expanded["structural_gap"] = expanded[value_cols].isna().all(axis=1).astype(int)

        all_groups.append(
            expanded.reset_index().rename(columns={"index": timestamp_col})
        )

    return pd.concat(all_groups).reset_index(drop=True)


CONFIG_PATH = "app_examples/experiment_example/data/miss_config.json"
OUTPUT_DIR = "app_examples/experiment_example/data/processed/experiment_dfs"

def main():
    # Load config
    with open(CONFIG_PATH, "r") as f:
        config = json.load(f)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Load dataset
    df = pd.read_csv(config["dataset_path"])

    for exp in config["experiments"]:
        rate = exp.get("rate", 0.1)
        mode = exp.get("mode", "MCAR")
        block_size = exp.get("block_size", 12)

        injector = MissingnessInjector(
            rate=rate,
            mode=mode,
            seed=exp.get("seed", 42),
            block_size=block_size
        )

        DEFAULT_VALUE_COLS = [
            "Water Temperature",
            "Turbidity",
            "Wave Height",
            "Wave Period",
        ]

        processed_df = injector.inject(df, DEFAULT_VALUE_COLS, group_col="Beach Name")
        df_final = expand_to_hourly(processed_df, timestamp_col="Readable Timestamp", group_col="Beach Name", value_cols=DEFAULT_VALUE_COLS)

        filename = f"{exp['name']}_rate{rate}_{mode}.csv"
        out_path = os.path.join(OUTPUT_DIR, filename)
        df_final.to_csv(out_path, index=False)

        logging.debug(f"[INFO] Saved processed dataset: {out_path}")


if __name__ == "__main__":
    main()
