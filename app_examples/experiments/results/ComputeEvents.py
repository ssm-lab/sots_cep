import pandas as pd
import numpy as np
import os
import json
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D

LOG_DIR = "data/logs/experiments/experiment_LifecycleEvaluation"
EVENT_LOG = os.path.join(LOG_DIR, "events.csv")

def load_data():
    df = pd.read_csv(EVENT_LOG, comment="#", engine="python")
    df.columns = df.columns.str.strip()
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df["event_ts"] = pd.to_numeric(df["event_ts"], errors="coerce")
    return df

def expand_extras(df):
    def safe_parse(x):
        if pd.isna(x):
            return {}
        try:
            return json.loads(x)
        except:
            return {}

    extras = df["extras"].apply(safe_parse)
    extras_df = pd.json_normalize(extras)
    extras_df.index = df.index

    return df.join(extras_df)


def filter_cep_active(df):
    return df[
        df["belonging_sub"].isin(["full_role", "restricted_role"])
    ]

def build_partition_df(df):
    pivot = df.pivot_table(
        index="event_ts",
        columns="partition",
        values="value",
        aggfunc="first"
    )
    return pivot.sort_index()

# ground truth
def build_state_df(df):
    state_df = df[df["partition"] == "ground_truth"].copy()
    state_df = state_df.set_index("event_ts")
    return state_df[["health", "belonging_main", "belonging_sub"]]


def build_full_df(pivot_df, state_df):
    df = pivot_df.join(state_df, how="left")

    for col in ["health", "belonging_main", "belonging_sub"]:
        if col in df.columns:
            df[col] = df[col].ffill().bfill()

    return df


def system_value(df):
    observed = df.get("observed.validated", pd.Series(index=df.index))
    reconstructed = df.get("reconstructed", pd.Series(index=df.index))
    return observed.combine_first(reconstructed)

def compute_errors(df):
    system = system_value(df)
    valid = system.notna()

    if valid.sum() == 0:
        return 0.0, 0.0

    mae = (system[valid] - df["ground_truth"][valid]).abs().mean()
    rmse = np.sqrt(((system[valid] - df["ground_truth"][valid]) ** 2).mean())

    return float(mae), float(rmse)


def compute_availability(df):
    observed = df.get("observed.validated", pd.Series(index=df.index)).notna()
    reconstructed = df.get("reconstructed", pd.Series(index=df.index)).notna()

    system = observed | reconstructed

    return float(observed.mean()), float(system.mean())


def compute_gap_stats(df):
    observed = df.get("observed.validated", pd.Series(index=df.index)).notna()
    reconstructed = df.get("reconstructed", pd.Series(index=df.index)).notna()

    gap = ~observed

    groups = (gap != gap.shift()).cumsum()
    lengths = gap.groupby(groups).sum()
    gaps = lengths[lengths > 0]

    if gaps.empty:
        return 0, 0, 0

    return int(len(gaps)), float(gaps.mean()), int(gaps.max())

def confidence_stats_and_correlation(df):
    recon = df[df["partition"] == "reconstructed"].copy()

    if recon.empty:
        return None, None, None, None

    recon["confidence"] = pd.to_numeric(recon["confidence"], errors="coerce")
    recon["value"] = pd.to_numeric(recon["value"], errors="coerce")

    gt = df[df["partition"] == "ground_truth"][["event_ts", "value"]].rename(
        columns={"value": "ground_truth"}
    )

    recon = recon.merge(gt, on="event_ts", how="left")
    recon["error"] = (recon["value"] - recon["ground_truth"]).abs()

    recon = recon.dropna(subset=["confidence", "error"])

    if len(recon) < 2:
        return None, None, None, None

    conf_mean = float(recon["confidence"].mean())
    conf_min = float(recon["confidence"].min())
    conf_max = float(recon["confidence"].max())
    corr = float(recon["confidence"].corr(recon["error"]))

    return conf_mean, conf_min, conf_max, corr

def overlay_participation(ax, df):
    belonging = df["belonging_sub"].fillna("none")

    def classify(state):
        if state == "full_role":
            return "full"
        elif state == "restricted_role":
            return "restricted"
        else:
            return "none"

    categories = belonging.apply(classify)

    prev = categories.iloc[0]
    start = df.index[0]

    for t, curr in categories.items():
        if curr != prev:
            color = {
                "full": "green",
                "restricted": "orange",
                "none": "red"
            }[prev]

            ax.axvspan(start, t, color=color, alpha=0.15)

            start = t
            prev = curr

    color = {
        "full": "green",
        "restricted": "orange",
        "none": "red"
    }[prev]

    ax.axvspan(start, df.index.max(), color=color, alpha=0.10)

def plot_health_transitions(ax, df):
    health = df["health"].fillna("unknown")
    prev = ""

    for t, curr in health.items():
        if curr != prev:
            ax.axvline(t, linestyle="--", alpha=0.25, color="black", linewidth=1)

            y_pos = 1.02
            ax.text(
                t,
                y_pos,
                curr.capitalize(),
                transform=ax.get_xaxis_transform(),
                rotation=0,
                fontsize=8,
                alpha=0.9,
                ha="center",
                va="bottom",
                clip_on=False
            )
            prev = curr

def plot_event_stream_all(df, t_start=None, t_end=None, name=None, fig_size=(12, 6)):
    df = df.copy()

    if t_start is not None and t_end is not None:
        df = df[(df["event_ts"] >= t_start) & (df["event_ts"] <= t_end)]

    signals = sorted(df["src"].unique())

    colors = {
        "dt-1": "blue",
        "dt-2": "green",
        "dt-3": "purple"
    }

    fig, ax = plt.subplots(figsize=fig_size)

    # Overlays
    if len(signals) > 0:
        ref_signal = signals[0]
        df_ref = df[df["src"] == ref_signal]

        pivot_ref = build_partition_df(df_ref)
        state_ref = build_state_df(df_ref)
        full_ref = build_full_df(pivot_ref, state_ref)

        if t_start is not None and t_end is not None:
            full_ref = full_ref[(full_ref.index >= t_start) & (full_ref.index <= t_end)]

        if "belonging_sub" in full_ref.columns:
            overlay_participation(ax, full_ref)
            plot_health_transitions(ax, full_ref)

    # lines
    for s in signals:
        df_s = df[df["src"] == s]

        pivot = build_partition_df(df_s)
        state = build_state_df(df_s)
        full = build_full_df(pivot, state)

        if t_start is not None and t_end is not None:
            full = full[(full.index >= t_start) & (full.index <= t_end)]

        gt = full.get("ground_truth", pd.Series(index=full.index))
        obs = full.get("observed.validated", pd.Series(index=full.index))
        sys = system_value(full)

        color = colors.get(s, "black")

        ax.plot(full.index, gt, color=color, linewidth=1.1, alpha=0.2, zorder=1)
        ax.plot(full.index, sys, linestyle=":", linewidth=1.1, color=color, alpha=0.7, zorder=2)
        ax.plot(full.index, obs, linewidth=0.8, color=color, zorder=3)

        recon = full.get("reconstructed", pd.Series(index=full.index))
        recon_only = recon[recon.notna() & obs.isna()]

        # ax.scatter(recon_only.index, recon_only, color=color, s=2, alpha=0.9, zorder=4)

  
    ax.set_xlabel("Time Steps")
    ax.set_ylabel("Measured Value")
    ax.grid(True, alpha=0.3)


    legend_elements = [
        Line2D([0], [0], color='black', lw=1.0, label='Baseline'),
        Line2D([0], [0], color='black', lw=1.6, linestyle=':', label='Compensated'),
        Line2D([0], [0], color='black', lw=0.8, alpha=0.3, label='Ground Truth'),
        # Line2D([0], [0], marker='o', color='black', linestyle='None', markersize=4, label='Reconstructed'),

        # mpatches.Patch(color='green', alpha=0.15, label='Full Contribution'),
        # mpatches.Patch(color='orange', alpha=0.15, label='Restricted Contribution (with Compensation)'),
        # mpatches.Patch(color='red', alpha=0.15, label='No Contribution'),
    ]

    ax.legend(handles=legend_elements, fontsize=9, loc="upper left")

    plt.tight_layout()

    if name:
        plt.savefig(
            f"app_examples/experiments/results/figures/event_stream_all_{name}.png",
            dpi=300
        )
    else:
        plt.savefig(
            "app_examples/experiments/results/figures/event_stream_all.png",
            dpi=300
        )


def main():
    df = load_data()
    df = expand_extras(df)

    signals = df["src"].unique()

    results = []

    for s in signals:
        df_s = df[df["src"] == s]

        pivot = build_partition_df(df_s)
        state = build_state_df(df_s)
        full = build_full_df(pivot, state)

        cep_df = filter_cep_active(full)

        mae, rmse = compute_errors(cep_df)

        conf_mean, conf_min, conf_max, corr = confidence_stats_and_correlation(df_s)

        obs_avail, sys_avail = compute_availability(cep_df)
        num_gaps, avg_gap, max_gap = compute_gap_stats(cep_df)

        results.append({
            "signal": s,
            "mae": mae,
            "rmse": rmse,
            "observed_availability": obs_avail,
            "system_availability": sys_avail,
            "num_gaps": num_gaps,
            "avg_gap": avg_gap,
            "max_gap": max_gap,
            "confidence_mean": conf_mean,
            "confidence_min": conf_min,
            "confidence_max": conf_max,
            "confidence_error_corr": corr
        })

    results_df = pd.DataFrame(results)

    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", 200)

    print("\n=== Per Signal Metrics ===")
    print(results_df.to_string(index=False))

    print("\n=== Average Metrics ===")
    print(results_df.mean(numeric_only=True))

    plot_event_stream_all(df, t_start=0, t_end=500, name="full", fig_size=(12, 6))
    plot_event_stream_all(df, t_start=0, t_end=50, name="step_1_stream", fig_size=(7, 5))
    plot_event_stream_all(df, t_start=75, t_end=235, name="step_2_stream", fig_size=(7, 5))
    plot_event_stream_all(df, t_start=350, t_end=425, name="step_3_stream", fig_size=(7, 5))
    plot_event_stream_all(df, t_start=430, t_end=464, name="step_4_stream", fig_size=(7, 5))

if __name__ == "__main__":
    main()