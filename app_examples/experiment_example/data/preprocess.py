import json
import logging
import os
from typing import Union, List, Optional

import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

class MissingnessInjector:
    """
    Injects artificial missingness (MCAR, MAR, MNAR, STRUCTURAL) into
    already expanded datasets. Skips rows with structural_gap == 1.
    """

    def __init__(self, rate: float, mode: str = "MCAR", seed: int = 42, block_size: int = 12):
        self.rate = rate
        self.mode = mode.upper() if mode else None
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

        # Protect structural gaps
        df = df.copy()
        if "structural_gap" in df.columns:
            df = df[df["structural_gap"] == 0]

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
            k = int(self.rate * n)
            if k == 0:
                continue

            # === MCAR ===
            if self.mode == "MCAR":
                drop_idx = np.random.choice(n, size=k, replace=False)
                uncertain_df.iloc[drop_idx, uncertain_df.columns.get_loc(col)] = np.nan

            # === MAR (block missingness) ===
            elif self.mode == "MAR":
                drop_idx = []
                while len(drop_idx) < k:
                    start = np.random.randint(0, max(1, n - self.block_size))
                    end = min(start + self.block_size, n)
                    drop_idx.extend(range(start, end))
                drop_idx = drop_idx[:k]
                uncertain_df.iloc[drop_idx, uncertain_df.columns.get_loc(col)] = np.nan

            # === MNAR (value-dependent) ===
            elif self.mode == "MNAR":
                ref_values = pd.to_numeric(uncertain_df[col], errors="coerce")
                if ref_values.isnull().all():
                    continue

                valid_mask = ~ref_values.isna()
                valid_values = ref_values[valid_mask]
                probs = (valid_values - valid_values.min()) / (valid_values.max() - valid_values.min() + 1e-9)
                probs = probs / probs.sum()
                valid_indices = np.where(valid_mask)[0]
                drop_valid_idx = np.random.choice(valid_indices, size=min(k, len(valid_indices)), replace=False, p=probs)
                uncertain_df.iloc[drop_valid_idx, uncertain_df.columns.get_loc(col)] = np.nan

            # === STRUCTURAL: used intentionally, marks new permanent gaps ===
            elif self.mode == "STRUCTURAL":
                drop_idx = np.random.choice(n, size=k, replace=False)
                uncertain_df.iloc[drop_idx, uncertain_df.columns.get_loc(col)] = np.nan
                uncertain_df.iloc[drop_idx, uncertain_df.columns.get_loc("structural_gap")] = 1

            # === ORACLE (no injection) ===
            elif self.mode is None or self.mode == "ORACLE":
                return uncertain_df

            else:
                raise ValueError(f"Unknown missingness mode: {self.mode}")

        return uncertain_df


def expand_to_hourly(
    df: pd.DataFrame,
    value_cols: List[str],
    timestamp_col="Readable Timestamp",
    group_col="Beach Name"
) -> pd.DataFrame:
    """
    Pads the dataset to a full hourly grid per beach and marks true structural gaps.
    Structural gaps are timestamps that had no original measurement at all.
    """
    all_groups = []
    for group_name, group in df.groupby(group_col):
        group = group.copy()
        group[timestamp_col] = pd.to_datetime(group[timestamp_col], errors="coerce")
        group = group.set_index(timestamp_col)

        full_index = pd.date_range(
            start=group.index.min().floor("h"),
            end=group.index.max().ceil("h"),
            freq="h"
        )
        expanded = group.reindex(full_index)
        expanded[group_col] = group_name

        # Structural gap = when all values are NaN (no record existed)
        expanded["structural_gap"] = expanded[value_cols].isna().all(axis=1).astype(int)
        all_groups.append(expanded.reset_index().rename(columns={"index": timestamp_col}))

    return pd.concat(all_groups).reset_index(drop=True)



CONFIG_PATH = "app_examples/experiment_example/data/miss_config.json"
OUTPUT_DIR = "app_examples/experiment_example/data/processed/experiment_dfs"


def main():
    # Load config
    with open(CONFIG_PATH, "r") as f:
        config = json.load(f)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Load base dataset (raw)
    df = pd.read_csv(config["dataset_path"])
    DEFAULT_VALUE_COLS = ["Water Temperature", "Turbidity", "Wave Height", "Wave Period"]

    # Expand first — define structural gaps once
    df_expanded = expand_to_hourly(
        df,
        timestamp_col="Readable Timestamp",
        group_col="Beach Name",
        value_cols=DEFAULT_VALUE_COLS
    )

    # For each experiment, inject missingness only into non-structural rows
    for exp in config["experiments"]:
        name = exp["name"]
        rate = exp.get("rate", 0.1)
        mode = exp.get("mode", "MCAR")
        block_size = exp.get("block_size", 12)

        logging.info(f"[{name}] Injecting {mode} missingness at rate={rate}")

        injector = MissingnessInjector(
            rate=rate,
            mode=mode,
            seed=exp.get("seed", 42),
            block_size=block_size
        )

        # Inject only on structural_gap == 0
        df_injected = injector.inject(df_expanded[df_expanded["structural_gap"] == 0], DEFAULT_VALUE_COLS, group_col="Beach Name")

        # Merge back with structural rows untouched
        df_final = pd.concat([
            df_injected,
            df_expanded[df_expanded["structural_gap"] == 1]
        ]).sort_values("Readable Timestamp").reset_index(drop=True)

        # Save
        out_path = os.path.join(OUTPUT_DIR, f"{name}.csv")
        df_final.to_csv(out_path, index=False)
        logging.info(f"[INFO] Saved processed dataset: {out_path}")


if __name__ == "__main__":
    main()
