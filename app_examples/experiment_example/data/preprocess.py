import json
import logging
import os
from typing import Union, List, Optional

import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


class MissingnessInjector:
    """
    Injects artificial missingness (MCAR, MAR, MNAR, HYBRID) into datasets.
    HYBRID mixes MCAR and block missingness with 50/50 probability.
    """

    def __init__(
        self,
        rate: float,
        mode: str = "MCAR",
        seed: int = 42,
        block_ranges: tuple = (2, 6)
    ):
        self.rate = rate
        self.mode = mode.upper() if mode else None
        self.seed = seed
        self.block_ranges = block_ranges
        np.random.seed(self.seed)

    def inject(
        self,
        df: pd.DataFrame,
        value_cols: Union[str, List[str]],
        group_col: Optional[str] = None
    ) -> pd.DataFrame:
        """Applies missingness independently per group (beach) and per column."""
        if isinstance(value_cols, str):
            value_cols = [value_cols]

        df = df.copy()

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

            drop_idx = set()

            # === HYBRID (MCAR + Block Missingness) ===
            if self.mode == "HYBRID":
                while len(drop_idx) < k:
                    i = np.random.randint(0, n)
                    if np.random.rand() < 0.5:
                        # MCAR: single missing point
                        drop_idx.add(i)
                    else:
                        # Block missingness
                        block_len = np.random.randint(*self.block_ranges)
                        start = max(0, min(i, n - block_len))
                        block = range(start, start + block_len)
                        drop_idx.update(block)
                drop_idx = list(drop_idx)[:k]
                uncertain_df.iloc[drop_idx, uncertain_df.columns.get_loc(col)] = np.nan

            # === MCAR ===
            elif self.mode == "MCAR":
                drop_idx = np.random.choice(n, size=k, replace=False)
                uncertain_df.iloc[drop_idx, uncertain_df.columns.get_loc(col)] = np.nan

            # === ORACLE (no missingness) ===
            elif self.mode is None or self.mode == "ORACLE":
                return uncertain_df

            else:
                raise ValueError(f"Unknown missingness mode: {self.mode}")

        return uncertain_df


def expand_to_hourly(
    df: pd.DataFrame,
    value_cols: List[str],
    timestamp_col="Readable Timestamp",
    group_col="Beach Name",
    interpolate: bool = True
) -> pd.DataFrame:
    all_groups = []
    for group_name, group in df.groupby(group_col):
        group = group.copy()
        group[timestamp_col] = pd.to_datetime(group[timestamp_col], errors="coerce")
        group = group.set_index(timestamp_col).sort_index()

        # Create full hourly index for this beach
        full_index = pd.date_range(
            start=group.index.min().floor("h"),
            end=group.index.max().ceil("h"),
            freq="h"
        )
        expanded = group.reindex(full_index)
        expanded[group_col] = group_name

        # Interpolate time-based gaps if enabled
        if interpolate:
            expanded[value_cols] = expanded[value_cols].interpolate(
                method="time", limit_direction="both"
            )

        # Reset index to restore timestamp column
        expanded = expanded.reset_index().rename(columns={"index": timestamp_col})

        # Add numeric Measurement Timestamp (POSIX seconds)
        expanded["Measurement Timestamp"] = expanded[timestamp_col].astype("int64").astype(int) // 10**9

        # Generate unique Measurement ID = BeachNameYYYYMMDDHHMM
        expanded["Measurement ID"] = expanded.apply(
            lambda row: f"{row[group_col].replace(' ', '')}"
                        f"{pd.to_datetime(row[timestamp_col]).strftime('%Y%m%d%H%M')}",
            axis=1
        )

        # Add *_groundtruth columns as interpolated reference values
        for col in value_cols:
            expanded[f"{col}_groundtruth"] = expanded[col]

        all_groups.append(expanded)

    # Combine all beaches
    return pd.concat(all_groups).sort_values(["Measurement Timestamp", group_col]).reset_index(drop=True)


# ====================================================
#  MAIN
# ====================================================
CONFIG_PATH = "app_examples/experiment_example/data/miss_config.json"
OUTPUT_DIR = "app_examples/experiment_example/data/processed/experiment_dfs"


def main():
    with open(CONFIG_PATH, "r") as f:
        config = json.load(f)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    df = pd.read_csv(config["dataset_path"])
    DEFAULT_VALUE_COLS = ["Water Temperature", "Turbidity", "Wave Height", "Wave Period"]

    # Expand to hourly + interpolate
    df_expanded = expand_to_hourly(
        df,
        timestamp_col="Readable Timestamp",
        group_col="Beach Name",
        value_cols=DEFAULT_VALUE_COLS,
        interpolate=True
    )

    for col in DEFAULT_VALUE_COLS:
        df_expanded[f"{col}_groundtruth"] = df_expanded[col]

    # Inject missingness experiments
    for exp in config["experiments"]:
        name = exp["name"]
        rate = exp.get("rate", 0.1)
        mode = exp.get("mode", "HYBRID")   # default to hybrid
        block_ranges = tuple(exp.get("block_ranges", [2, 6]))

        logging.info(f"[{name}] Injecting {mode} missingness at rate={rate}")

        injector = MissingnessInjector(
            rate=rate,
            mode=mode,
            seed=exp.get("seed", 42),
            block_ranges=block_ranges
        )

        df_injected = injector.inject(
            df_expanded,
            DEFAULT_VALUE_COLS,
            group_col="Beach Name"
        )

        out_path = os.path.join(OUTPUT_DIR, f"{name}.csv")
        df_injected.to_csv(out_path, index=False)
        logging.info(f"[INFO] Saved processed dataset: {out_path}")


if __name__ == "__main__":
    main()
