
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
INPUT_FILE = (
    ROOT / "data" / "alibaba2018" / "processed"
    / "machine_timeseries.csv"
)
OUTPUT_FILE = (
    ROOT / "data" / "alibaba2018" / "processed"
    / "forecast_baseline_results_triple_split.csv"
)

EXPECTED_INTERVAL = 10


def calculate_metrics(actual, predicted):
    errors = actual - predicted
    mae = np.mean(np.abs(errors))
    rmse = np.sqrt(np.mean(errors ** 2))
    return float(mae), float(rmse)


def main():
    df = pd.read_csv(INPUT_FILE)
    df = df.sort_values("timestamp").reset_index(drop=True)

    # Exclude the first segment and the long gap.
    # Start with the larger continuous segment.
    df = df[df["timestamp"] >= 160380].copy()
    df = df.sort_values("timestamp").reset_index(drop=True)

    if df.empty:
        raise ValueError("The second segment contains no rows.")

    intervals = df["timestamp"].diff().dropna()
    irregular = intervals[intervals != EXPECTED_INTERVAL]

    if not irregular.empty:
        print("Irregular timestamp intervals detected:")
        print(irregular.value_counts().to_string())
        raise ValueError(
            "Segment is not regularly spaced. "
            "Split at every gap before evaluating."
        )

    for col in ["cpu_mean", "memory_mean"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["cpu_mean", "memory_mean"]).reset_index(drop=True)

    train_end = int(len(df) * 0.60)
    validation_end = int(len(df) * 0.80)
    if train_end < 2 or validation_end <= train_end or validation_end >= len(df):
        raise ValueError("Not enough rows for chronological train/validation/test splits.")

    train = df.iloc[:train_end].copy()
    validation = df.iloc[train_end:validation_end].copy()
    test = df.iloc[validation_end:].copy()

    results = []

    print("Alibaba 2018 persistence baseline")
    print("---------------------------------")
    print(f"Rows in segment: {len(df):,}")
    print(f"Training rows: {len(train):,}")
    print(f"Validation rows: {len(validation):,}")
    print(f"Testing rows: {len(test):,}")
    print(f"Training timestamps: {train['timestamp'].min()} to "
          f"{train['timestamp'].max()}")
    print(f"Testing timestamps: {test['timestamp'].min()} to "
          f"{test['timestamp'].max()}")

    for col, label in [
        ("cpu_mean", "CPU"),
        ("memory_mean", "Memory"),
    ]:
        # Predict each point from the immediately preceding observation.
        # For the first test point, use the final training observation.
        validation_actual = validation[col].to_numpy()
        validation_predicted = df[col].shift(1).iloc[train_end:validation_end].to_numpy()
        test_actual = test[col].to_numpy()
        test_predicted = df[col].shift(1).iloc[validation_end:].to_numpy()
        validation_mae, validation_rmse = calculate_metrics(validation_actual, validation_predicted)
        test_mae, test_rmse = calculate_metrics(test_actual, test_predicted)

        train_p95 = float(train[col].quantile(0.95))
        test_p95 = float(test[col].quantile(0.95))
        exceedances = int((test[col] > train_p95).sum())

        results.append({
            "metric": label,
            "forecast_horizon_seconds": EXPECTED_INTERVAL,
            "training_rows": len(train),
            "validation_rows": len(validation),
            "test_rows": len(test),
            "validation_mae_percentage_points": validation_mae,
            "validation_rmse_percentage_points": validation_rmse,
            "test_mae_percentage_points": test_mae,
            "test_rmse_percentage_points": test_rmse,
            "training_p95": train_p95,
            "test_p95": test_p95,
            "test_values_above_training_p95": exceedances,
        })

        print(f"\n{label}")
        print(f"  Validation MAE/RMSE: {validation_mae:.4f} / {validation_rmse:.4f} percentage points")
        print(f"  Held-out test MAE/RMSE: {test_mae:.4f} / {test_rmse:.4f} percentage points")
        print(f"  Training 95th percentile: {train_p95:.4f}")
        print(f"  Test 95th percentile: {test_p95:.4f}")
        print(f"  Test observations above training P95: "
              f"{exceedances}/{len(test)}")

    pd.DataFrame(results).to_csv(OUTPUT_FILE, index=False)
    print(f"\nResults saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
