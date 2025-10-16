"""
oracle_analysis.py — Compare experiment runs against oracle patterns.
Computes event-level and pattern-level agreement metrics.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import json
import matplotlib.pyplot as plt
import seaborn as sns

# ----------------------------------------------------------------------
# CONFIGURATION
# ----------------------------------------------------------------------

RUN_DIR = Path("data/logs/experiment_example/20251015-172248/oracle")  # ← change to current run
EVENT_FILE = RUN_DIR / "events.csv"
PATTERN_FILE = RUN_DIR / "patterns.csv"
ORACLE_PATTERN_FILE = Path("data/logs/oracle/patterns.csv")  # ← optional oracle baseline

TIME_TOLERANCE = 30.0  # seconds for matching patterns between runs

# ----------------------------------------------------------------------
# LOAD DATA
# ----------------------------------------------------------------------

def load_patterns(path):
    df = pd.read_csv(path, comment="#")
    # Extract core fields
    df["fired_at"] = pd.to_datetime(df["fired_at"], errors="coerce")
    df["pattern_tier"] = np.where(df["pattern_type"] == "atomic", "atomic",
                           np.where(df["pattern_name"].str.contains("Local"), "local", "distributed"))
    return df

def load_events(path):
    df = pd.read_csv(path, comment="#")
    df["event_ts"] = pd.to_datetime(df["event_ts"], unit="s", errors="coerce")
    df["beach"] = df["stream_id"].str.extract(r"(Calumet|Montrose|63rd)")
    df["attribute"] = df["stream_id"].str.extract(r"(Water_Temperature|Turbidity|Wave_Height|Wave_Period)")
    return df

patterns = load_patterns(PATTERN_FILE)
events = load_events(EVENT_FILE)
print(f"[INFO] Loaded {len(events)} events and {len(patterns)} patterns")

# ----------------------------------------------------------------------
# SUMMARY STATISTICS
# ----------------------------------------------------------------------

summary = (
    patterns.groupby(["pattern_tier", "pattern_name"])
    .size()
    .reset_index(name="count")
    .sort_values(["pattern_tier", "count"], ascending=[True, False])
)
print("\n=== Pattern Firing Summary ===")
print(summary)

# ----------------------------------------------------------------------
# IF ORACLE AVAILABLE — COMPARE DETECTIONS
# ----------------------------------------------------------------------

if ORACLE_PATTERN_FILE.exists():
    oracle = load_patterns(ORACLE_PATTERN_FILE)
    oracle["match"] = False

    matches = []
    for _, row in patterns.iterrows():
        # try matching same pattern name within time tolerance
        mask = (
            (oracle["pattern_name"] == row["pattern_name"])
            & (np.abs((oracle["fired_at"] - row["fired_at"]).dt.total_seconds()) < TIME_TOLERANCE)
        )
        if mask.any():
            oracle.loc[mask, "match"] = True
            matches.append(row["pattern_name"])

    detected = oracle["match"].sum()
    missed = (~oracle["match"]).sum()
    precision = detected / len(patterns)
    recall = detected / len(oracle)

    print(f"\n=== Oracle Comparison ===")
    print(f"Detected: {detected} / {len(oracle)}")
    print(f"Precision: {precision:.3f}, Recall: {recall:.3f}")
else:
    print("\n[WARN] No oracle pattern file found, skipping comparison.")

# ----------------------------------------------------------------------
# CONFIDENCE DISTRIBUTIONS
# ----------------------------------------------------------------------

plt.figure(figsize=(8,5))
sns.boxplot(x="pattern_tier", y="confidence", data=patterns, showmeans=True)
plt.title("Pattern Confidence by Tier")
plt.tight_layout()
plt.show()

# ----------------------------------------------------------------------
# TEMPORAL ALIGNMENT CHECK
# ----------------------------------------------------------------------

def plot_timeline(df):
    plt.figure(figsize=(12,6))
    sns.scatterplot(
        x="fired_at", y="pattern_tier", hue="pattern_type",
        data=df, alpha=0.7, edgecolor=None
    )
    plt.title("Pattern Firing Timeline")
    plt.tight_layout()
    plt.show()

plot_timeline(patterns)

# ----------------------------------------------------------------------
# EXPORT SUMMARY
# ----------------------------------------------------------------------

summary.to_csv(RUN_DIR / "pattern_summary.csv", index=False)
print(f"[INFO] Summary exported to {RUN_DIR / 'pattern_summary.csv'}")
