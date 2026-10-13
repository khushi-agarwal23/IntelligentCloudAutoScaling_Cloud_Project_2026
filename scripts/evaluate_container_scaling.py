
from pathlib import Path
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parents[1]

DATA_FILE = (
    ROOT / "data" / "alibaba" / "processed" /
    "container_timeseries.csv"
)

OUTPUT_FILE = (
    ROOT / "data" / "alibaba" / "processed" /
    "container_scaling_evaluation.csv"
)


def choose_action(cpu, memory, cpu_low, cpu_high,
                  memory_low, memory_high):
    if cpu >= cpu_high or memory >= memory_high:
        return "scale_up"

    if cpu <= cpu_low and memory <= memory_low:
        return "scale_down"

    return "maintain"


def report_detection(actual, predicted, label):
    tp = int((actual & predicted).sum())
    fp = int((~actual & predicted).sum())
    fn = int((actual & ~predicted).sum())
    tn = int((~actual & ~predicted).sum())

    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0

    print(f"\n{label} high-workload detection:")
    print(f"Actual high-workload windows: {int(actual.sum())}")
    print(f"True positives: {tp}")
    print(f"False positives: {fp}")
    print(f"False negatives: {fn}")
    print(f"True negatives: {tn}")
    print(f"Precision: {precision:.3f}")
    print(f"Recall: {recall:.3f}")

    if actual.sum() == 0:
        print("Recall is not meaningfully measurable: no actual high windows.")


def main():
    if not DATA_FILE.exists():
        raise FileNotFoundError(
            f"Processed container data not found: {DATA_FILE}"
        )

    df = pd.read_csv(DATA_FILE)
    df = df.sort_values("timestamp").reset_index(drop=True)

    required = [
        "timestamp", "cpu_p95", "memory_p95",
        "container_count"
    ]

    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}")

    df = df.replace([np.inf, -np.inf], np.nan)
    df = df.dropna(subset=required).reset_index(drop=True)

    if len(df) < 20:
        raise ValueError(
            "Too few time windows for chronological evaluation."
        )

    # Persistence baseline: current P95 predicts the next interval.
    df["forecast_cpu_p95"] = df["cpu_p95"]
    df["forecast_memory_p95"] = df["memory_p95"]

    df["actual_next_cpu_p95"] = df["cpu_p95"].shift(-1)
    df["actual_next_memory_p95"] = df["memory_p95"].shift(-1)

    # Chronological 60/40 split. Thresholds use training data only.
    split = int(len(df) * 0.60)
    training = df.iloc[:split].copy()
    evaluation = df.iloc[split:-1].copy()

    if evaluation.empty:
        raise ValueError("Evaluation period is empty.")

    cpu_low = training["cpu_p95"].quantile(0.25)
    cpu_high = training["cpu_p95"].quantile(0.75)
    memory_low = training["memory_p95"].quantile(0.25)
    memory_high = training["memory_p95"].quantile(0.75)

    print("=" * 60)
    print("CONTAINER-BASED OFFLINE SCALING EVALUATION")
    print("=" * 60)

    print("\nData split:")
    print(f"Total windows: {len(df)}")
    print(f"Training windows: {len(training)}")
    print(f"Evaluation windows: {len(evaluation)}")

    print("\nThresholds learned from training data:")
    print(f"CPU P95 low: {cpu_low:.2f}%")
    print(f"CPU P95 high: {cpu_high:.2f}%")
    print(f"Memory P95 low: {memory_low:.2f}%")
    print(f"Memory P95 high: {memory_high:.2f}%")

    evaluation = evaluation.copy()

    evaluation["action"] = evaluation.apply(
        lambda row: choose_action(
            row["forecast_cpu_p95"],
            row["forecast_memory_p95"],
            cpu_low,
            cpu_high,
            memory_low,
            memory_high,
        ),
        axis=1,
    )

    # Evaluate whether the next observed interval crosses the
    # training-period upper thresholds.
    evaluation["actual_high_cpu"] = (
        evaluation["actual_next_cpu_p95"] >= cpu_high
    )
    evaluation["forecast_high_cpu"] = (
        evaluation["forecast_cpu_p95"] >= cpu_high
    )

    evaluation["actual_high_memory"] = (
        evaluation["actual_next_memory_p95"] >= memory_high
    )
    evaluation["forecast_high_memory"] = (
        evaluation["forecast_memory_p95"] >= memory_high
    )

    # Persistence forecast errors on held-out observations.
    for resource in ["cpu", "memory"]:
        forecast = evaluation[f"forecast_{resource}_p95"]
        actual = evaluation[f"actual_next_{resource}_p95"]

        mae = (forecast - actual).abs().mean()
        rmse = np.sqrt(((forecast - actual) ** 2).mean())

        print(f"\n{resource.upper()} P95 forecast:")
        print(f"MAE: {mae:.3f} percentage points")
        print(f"RMSE: {rmse:.3f} percentage points")

    print("\nScaling decisions:")
    counts = evaluation["action"].value_counts()
    for action in ["scale_up", "maintain", "scale_down"]:
        print(f"{action}: {int(counts.get(action, 0))}")

    report_detection(
        evaluation["actual_high_cpu"].astype(bool),
        evaluation["forecast_high_cpu"].astype(bool),
        "CPU",
    )

    report_detection(
        evaluation["actual_high_memory"].astype(bool),
        evaluation["forecast_high_memory"].astype(bool),
        "Memory",
    )

    # Save results for reproducibility and further analysis.
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    evaluation.to_csv(OUTPUT_FILE, index=False, float_format="%.4f")

    print(f"\nSaved results to: {OUTPUT_FILE}")
    print(
        "\nImportant: this is an offline evaluation using real "
        "container measurements. It does not measure actual "
        "cloud scaling effects or prove cost/performance improvements."
    )


if __name__ == "__main__":
    main()
