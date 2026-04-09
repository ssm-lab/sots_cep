import pandas as pd
import os
from collections import defaultdict

LOG_DIR = "data/logs/experiments/experiment_LifecycleEvaluation"
PATTERN_LOG = os.path.join(LOG_DIR, "patterns.csv")

PATTERNS = [
    "CrossSignalAgreement",
    "CrossSignalDivergence",
    "CrossSignalRelativeStable"
]


def load_data():
    df = pd.read_csv(PATTERN_LOG, comment="#")
    df.columns = df.columns.str.strip()
    return df


def get_base_pattern(name):
    return name.rsplit("_", 1)[0]

def split_pattern_types(df):
    return {
        "OBS": df[df["pattern_name"].str.endswith("_OBS")],
        "SYS": df[df["pattern_name"].str.endswith("_SYS")],
        "GT": df[df["pattern_name"].str.endswith("_GT")],
    }


def compute_detection_counts(groups):
    return {k: len(v) for k, v in groups.items()}

def match_events(gt_times, test_times, tolerance=1.0):
    i, j = 0, 0
    matched = 0

    while i < len(gt_times) and j < len(test_times):
        diff = test_times[j] - gt_times[i]

        if abs(diff) <= tolerance:
            matched += 1
            i += 1
            j += 1
        elif test_times[j] < gt_times[i]:
            j += 1
        else:
            i += 1

    missed = len(gt_times) - matched
    false_pos = len(test_times) - matched

    return matched, missed, false_pos


def compute_temporal_metrics(df, pattern_base, tolerance=1.0):
    gt = df[df["pattern_name"] == f"{pattern_base}_GT"]
    obs = df[df["pattern_name"] == f"{pattern_base}_OBS"]
    sys = df[df["pattern_name"] == f"{pattern_base}_SYS"]

    gt_times = sorted(gt["fired_offset_sec"].tolist())
    obs_times = sorted(obs["fired_offset_sec"].tolist())
    sys_times = sorted(sys["fired_offset_sec"].tolist())

    def compute_metrics(gt_times, test_times):
        matched, missed, false_pos = match_events(
            gt_times, test_times, tolerance
        )

        precision = matched / len(test_times) if len(test_times) > 0 else 0
        recall = matched / len(gt_times) if len(gt_times) > 0 else 0

        # F1
        if precision + recall == 0:
            f1 = 0
        else:
            f1 = 2 * (precision * recall) / (precision + recall)

        # F2 (beta = 2)
        beta = 2
        if precision + recall == 0:
            f2 = 0
        else:
            f2 = (1 + beta**2) * (precision * recall) / ((beta**2 * precision) + recall)

        return {
            "matched": matched,
            "missed": missed,
            "false_pos": false_pos,
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "f2": f2,
        }
    return {
        "OBS": compute_metrics(gt_times, obs_times),
        "SYS": compute_metrics(gt_times, sys_times),
    }

def compute_pattern_breakdown(df):
    results = defaultdict(dict)

    for pattern_base in PATTERNS:
        for suffix in ["OBS", "SYS", "GT"]:
            name = f"{pattern_base}_{suffix}"
            subset = df[df["pattern_name"] == name]

            results[pattern_base][suffix] = {
                "count": len(subset),
            }

    return results


def main():
    df = load_data()

    groups = split_pattern_types(df)

    counts = compute_detection_counts(groups)
    breakdown = compute_pattern_breakdown(df)

    print("\n===== OVERALL METRICS =====")
    print("Counts:", counts)

    print("\n===== TEMPORAL ACCURACY (Precision / Recall / F1) =====")

    for pattern in PATTERNS:
        metrics = compute_temporal_metrics(df, pattern, tolerance=0.1)

        print(f"\n{pattern}:")
        for k, v in metrics.items():
            print(
                f"  {k}: "
                f"P={v['precision']:.3f}, "
                f"R={v['recall']:.3f}, "
                f"F1={v['f1']:.3f}, "
                f"F2={v['f2']:.3f}, "
                f"matched={v['matched']}, "
                f"missed={v['missed']}, "
                f"fp={v['false_pos']}"
            )

if __name__ == "__main__":
    main()