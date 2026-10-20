
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

DATA_FILE = (
    ROOT / "data" / "alibaba" / "processed" / "cluster_timeseries.csv"
)

OUTPUT_FILE = (
    ROOT / "data" / "alibaba" / "processed"
    / "scaling_evaluation_p95.csv"
)


def choose_action(cpu, memory, cpu_low, cpu_high,
                  memory_low, memory_high):
    if cpu >= cpu_high or memory >= memory_high:
        return "scale_up"

    if cpu <= cpu_low and memory <= memory_low:
        return "scale_down"

    return "maintain"


def main():
    if not DATA_FILE.exists():
        raise FileNotFoundError(f"Dataset not found: {DATA_FILE}")

    df = pd.read_csv(DATA_FILE)
    df = df.sort_values("timestamp").reset_index(drop=True)

    required = [
        "timestamp", "cpu_p95", "memory_p95"
    ]

    missing = [column for column in required if column not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    # Persistence forecast: current observation predicts the next interval.
    df["forecast_cpu_p95"] = df["cpu_p95"]
    df["forecast_memory_p95"] = df["memory_p95"]

    df["actual_next_cpu_p95"] = df["cpu_p95"].shift(-1)
    df["actual_next_memory_p95"] = df["memory_p95"].shift(-1)

    # Use the first 60% to set thresholds.
    split = int(len(df) * 0.60)
    training = df.iloc[:split]
    evaluation = df.iloc[split:-1].copy()

    cpu_low = training["cpu_p95"].quantile(0.25)
    cpu_high = training["cpu_p95"].quantile(0.75)

    memory_low = training["memory_p95"].quantile(0.25)
    memory_high = training["memory_p95"].quantile(0.75)

    print("Thresholds learned from training data:")
    print(f"CPU P95 low: {cpu_low:.2f}%")
    print(f"CPU P95 high: {cpu_high:.2f}%")
    print(f"Memory P95 low: {memory_low:.2f}%")
    print(f"Memory P95 high: {memory_high:.2f}%")

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

    # Define high workload using the training-period upper thresholds.
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

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    evaluation.to_csv(OUTPUT_FILE, index=False)

    print("\nOffline evaluation")
    print(f"Training windows: {len(training)}")
    print(f"Evaluation windows: {len(evaluation)}")

    print("\nForecasted workload range:")
    print(
        evaluation[
            ["forecast_cpu_p95", "forecast_memory_p95"]
        ].describe().round(2)
    )

    print("\nActual next-window workload range:")
    print(
        evaluation[
            ["actual_next_cpu_p95", "actual_next_memory_p95"]
        ].describe().round(2)
    )

    print("\nScaling decisions:")
    print(
        evaluation["action"]
        .value_counts()
        .reindex(
            ["scale_up", "maintain", "scale_down"],
            fill_value=0,
        )
        .to_string()
    )

    for resource in ["cpu", "memory"]:
        actual = evaluation[f"actual_high_{resource}"]
        predicted = evaluation[f"forecast_high_{resource}"]

        print(f"\n{resource.upper()} high-workload detection:")
        print(f"Actual high-workload windows: {int(actual.sum())}")
        print(f"True positives: {int((actual & predicted).sum())}")
        print(f"False positives: {int((~actual & predicted).sum())}")
        print(f"False negatives: {int((actual & ~predicted).sum())}")
        print(f"True negatives: {int((~actual & ~predicted).sum())}")

    print(f"\nSaved results to: {OUTPUT_FILE}")
    print(
        "Note: this is offline policy evaluation. "
        "It does not measure the effect of changing actual cloud capacity."
    )


if __name__ == "__main__":
    main()
