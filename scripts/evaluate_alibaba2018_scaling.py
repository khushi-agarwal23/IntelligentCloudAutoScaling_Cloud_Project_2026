
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
)

ROOT = Path(__file__).resolve().parents[1]

DATA_FILE = (
    ROOT / "data" / "alibaba2018" / "processed"
    / "machine_timeseries.csv"
)

OUTPUT_DIR = ROOT / "data" / "alibaba2018" / "processed"
OUTPUT_FILE = OUTPUT_DIR / "scaling_policy_evaluation_triple_split.csv"

SEGMENT_START = 160380
LAGS = [1, 2, 3, 6]
EXPECTED_INTERVAL = 10


def action_from_forecast(cpu, memory, cpu_low, cpu_high,
                         memory_low, memory_high):
    if cpu >= cpu_high or memory >= memory_high:
        return "scale_up"
    if cpu <= cpu_low and memory <= memory_low:
        return "scale_down"
    return "maintain"


def metrics(actual, predicted):
    return {
        "MAE": mean_absolute_error(actual, predicted),
        "RMSE": np.sqrt(mean_squared_error(actual, predicted)),
    }


def main():
    if not DATA_FILE.exists():
        raise FileNotFoundError(f"Dataset not found: {DATA_FILE}")

    df = pd.read_csv(DATA_FILE).sort_values("timestamp").reset_index(drop=True)

    # Use the larger segment after the known multi-hour gap.
    df = df[df["timestamp"] >= SEGMENT_START].copy()
    df = df.sort_values("timestamp").reset_index(drop=True)

    df = df.dropna(subset=["cpu_mean", "memory_mean"]).reset_index(drop=True)

    intervals = df["timestamp"].diff().dropna()
    if not intervals.eq(EXPECTED_INTERVAL).all():
        raise ValueError(
            "Unexpected timestamp gap detected. Split into continuous "
            "segments before evaluating."
        )

    # Features use observations available before the forecast target.
    feature_columns = []
    for col in ["cpu_mean", "memory_mean"]:
        for lag in LAGS:
            name = f"{col}_lag_{lag}"
            df[name] = df[col].shift(lag)
            feature_columns.append(name)

    # Target is the next observation.
    df["target_cpu"] = df["cpu_mean"].shift(-1)
    df["target_memory"] = df["memory_mean"].shift(-1)
    df = df.dropna().reset_index(drop=True)

    train_end = int(len(df) * 0.60)
    validation_end = int(len(df) * 0.80)
    if train_end < 100 or validation_end <= train_end or validation_end >= len(df):
        raise ValueError("Not enough rows for chronological train/validation/test splits.")
    train = df.iloc[:train_end].copy()
    validation = df.iloc[train_end:validation_end].copy()
    train_validation = df.iloc[:validation_end].copy()
    test = df.iloc[validation_end:].copy()

    if len(train) < 100 or len(test) < 10:
        raise ValueError("Insufficient rows for evaluation.")

    X_train = train[feature_columns]
    X_test = test[feature_columns]

    y_train = train[["target_cpu", "target_memory"]].to_numpy()
    y_test = test[["target_cpu", "target_memory"]].to_numpy()

    model = RandomForestRegressor(
        n_estimators=100,
        max_depth=12,
        min_samples_leaf=5,
        random_state=42,
        n_jobs=1,
    )
    model.fit(X_train, y_train)
    validation_predictions = model.predict(validation[feature_columns])
    validation_actual = validation[["target_cpu", "target_memory"]].to_numpy()
    print(f"Validation rows: {len(validation):,}")
    print(f"Validation CPU/Mem MAE: {mean_absolute_error(validation_actual, validation_predictions, multioutput='raw_values')}")

    model.fit(
        train_validation[feature_columns],
        train_validation[["target_cpu", "target_memory"]].to_numpy(),
    )
    rf_predictions = model.predict(X_test)

    # Persistence uses the most recent observation.
    persistence_predictions = test[
        ["cpu_mean_lag_1", "memory_mean_lag_1"]
    ].to_numpy()

    print("Alibaba 2018 offline scaling-policy evaluation")
    print("==============================================")
    print(f"Training rows: {len(train):,}")
    print(f"Validation rows: {len(validation):,}")
    print(f"Test rows: {len(test):,}")

    for i, label in enumerate(["CPU", "Memory"]):
        rf = metrics(y_test[:, i], rf_predictions[:, i])
        persistence = metrics(
            y_test[:, i], persistence_predictions[:, i]
        )
        print(f"\n{label} forecast metrics")
        print(f"  Random Forest MAE: {rf['MAE']:.4f}")
        print(f"  Random Forest RMSE: {rf['RMSE']:.4f}")
        print(f"  Persistence MAE: {persistence['MAE']:.4f}")
        print(f"  Persistence RMSE: {persistence['RMSE']:.4f}")

    # Learn thresholds from training-period observations only.
    cpu_low = train["cpu_mean"].quantile(0.25)
    cpu_high = train["cpu_mean"].quantile(0.75)
    memory_low = train["memory_mean"].quantile(0.25)
    memory_high = train["memory_mean"].quantile(0.75)

    print("\nTraining-derived thresholds")
    print(f"CPU low/high: {cpu_low:.3f} / {cpu_high:.3f}")
    print(
        f"Memory low/high: {memory_low:.3f} / {memory_high:.3f}"
    )

    result = test[
        ["timestamp", "cpu_mean", "memory_mean"]
    ].copy()

    result = result.rename(columns={
        "cpu_mean": "observed_cpu",
        "memory_mean": "observed_memory",
    })

    result["actual_next_cpu"] = y_test[:, 0]
    result["actual_next_memory"] = y_test[:, 1]

    result["persistence_cpu_forecast"] = persistence_predictions[:, 0]
    result["persistence_memory_forecast"] = persistence_predictions[:, 1]
    result["rf_cpu_forecast"] = rf_predictions[:, 0]
    result["rf_memory_forecast"] = rf_predictions[:, 1]

    # Same action rule for both forecasts.
    result["persistence_action"] = [
        action_from_forecast(c, m, cpu_low, cpu_high, memory_low, memory_high)
        for c, m in persistence_predictions
    ]
    result["rf_action"] = [
        action_from_forecast(c, m, cpu_low, cpu_high, memory_low, memory_high)
        for c, m in rf_predictions
    ]

    # Define high utilization relative to the training upper quartile.
    result["actual_high_cpu"] = result["actual_next_cpu"] >= cpu_high
    result["actual_high_memory"] = result["actual_next_memory"] >= memory_high

    for policy in ["persistence", "rf"]:
        print(f"\n{policy.upper()} policy actions")
        print(
            result[f"{policy}_action"]
            .value_counts()
            .reindex(
                ["scale_up", "maintain", "scale_down"],
                fill_value=0,
            )
            .to_string()
        )

        predicted_cpu_high = (
            result[f"{policy}_cpu_forecast"] >= cpu_high
        )
        predicted_memory_high = (
            result[f"{policy}_memory_forecast"] >= memory_high
        )

        for resource, actual, predicted in [
            ("CPU", result["actual_high_cpu"], predicted_cpu_high),
            ("Memory", result["actual_high_memory"], predicted_memory_high),
        ]:
            tp = int((actual & predicted).sum())
            fp = int((~actual & predicted).sum())
            fn = int((actual & ~predicted).sum())
            tn = int((~actual & ~predicted).sum())

            print(f"  {resource} high-utilization detection:")
            print(f"    TP={tp}, FP={fp}, FN={fn}, TN={tn}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    result.to_csv(OUTPUT_FILE, index=False)

    print(f"\nDetailed results saved to: {OUTPUT_FILE}")
    print(
        "Offline trace evaluation only; no actual AWS capacity changes "
        "or performance improvements are measured."
    )


if __name__ == "__main__":
    main()
