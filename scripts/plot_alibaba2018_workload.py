"""Create a chronological Alibaba 2018 CPU/memory workload overview."""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
INPUT_FILE = ROOT / "data" / "alibaba2018" / "processed" / "machine_timeseries.csv"
OUTPUT_FILE = ROOT / "results" / "alibaba2018_workload_overview.png"
SEGMENT_START = 160380
EXPECTED_INTERVAL_SECONDS = 10


def main():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Processed workload file not found: {INPUT_FILE}")

    frame = pd.read_csv(INPUT_FILE).sort_values("timestamp").reset_index(drop=True)
    frame = frame.loc[frame["timestamp"] >= SEGMENT_START].copy().reset_index(drop=True)
    gaps = frame["timestamp"].diff().dropna()
    if frame.empty or not gaps.eq(EXPECTED_INTERVAL_SECONDS).all():
        raise ValueError("Selected segment must be nonempty and regularly sampled every 10 seconds.")

    split = int(len(frame) * 0.60)
    validation_end = int(len(frame) * 0.80)
    train = frame.iloc[:split]
    elapsed_hours = (frame["timestamp"] - frame["timestamp"].iloc[0]) / 3600
    split_train_hours = elapsed_hours.iloc[split]
    split_validation_hours = elapsed_hours.iloc[validation_end]
    cpu_p95 = train["cpu_mean"].quantile(0.95)
    memory_p95 = train["memory_mean"].quantile(0.95)

    figure, axes = plt.subplots(2, 1, figsize=(12, 7.5), sharex=True)
    series = [
        ("cpu_mean", "Mean CPU utilization (%)", cpu_p95, "#2563eb"),
        ("memory_mean", "Mean memory utilization (%)", memory_p95, "#d97706"),
    ]
    for axis, (column, label, threshold, color) in zip(axes, series):
        axis.plot(elapsed_hours, frame[column], color=color, linewidth=0.7, alpha=0.8)
        axis.axhline(threshold, color="#b91c1c", linestyle="--", linewidth=1.2,
                     label=f"Training p95 = {threshold:.2f}%")
        axis.axvline(split_train_hours, color="#475569", linestyle=":", linewidth=1.1,
                     label="Train / validation boundary")
        axis.axvline(split_validation_hours, color="#64748b", linestyle="-.", linewidth=1.1,
                     label="Validation / test boundary")
        axis.set_ylabel(label)
        axis.set_ylim(0, 100)
        axis.grid(alpha=0.2)
        axis.legend(loc="upper left", ncols=3, fontsize=8)

    axes[-1].set_xlabel("Elapsed hours from selected trace segment start")
    figure.suptitle("Alibaba Cluster Trace v2018: 10-second mean machine utilization")
    figure.text(
        0.5, 0.01,
        "Means aggregated across machines at each timestamp; workload proxy, not e-commerce demand or festival-sales data.",
        ha="center", fontsize=9,
    )
    figure.tight_layout(rect=(0, 0.035, 1, 0.96))
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(OUTPUT_FILE, dpi=160, bbox_inches="tight")
    plt.close(figure)
    print(f"Saved {OUTPUT_FILE}")
    print(f"Rows: {len(frame):,}; train/validation/test: {split:,}/{validation_end - split:,}/{len(frame) - validation_end:,}")
    print(f"Training p95 CPU/memory: {cpu_p95:.4f}% / {memory_p95:.4f}%")


if __name__ == "__main__":
    main()
