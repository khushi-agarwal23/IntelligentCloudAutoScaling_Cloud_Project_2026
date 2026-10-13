
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error

ROOT = Path(__file__).resolve().parents[1]

DATA_FILE = (
    ROOT / "data" / "alibaba" / "processed" / "cluster_timeseries.csv"
)
MODEL_FILE = ROOT / "models" / "workload_forecaster.joblib"

BASE_FEATURES = [
    "cpu_mean",
    "memory_mean",
    "cpu_p95",
    "memory_p95",
]

TARGETS = ["cpu_mean", "memory_mean"]
LAGS = [1, 2, 3, 5, 10]


def main():
    df = pd.read_csv(DATA_FILE)
    df = df.sort_values("timestamp").reset_index(drop=True)

    if len(df) < 50:
        raise ValueError("Not enough time windows to train.")

    # Verify that the source is regularly sampled.
    intervals = df["timestamp"].diff().dropna()
    print("Timestamp intervals (seconds):")
    print(intervals.value_counts().head())

    # Predict the next recorded time window using observations
    # available at the current time.
    feature_columns = list(BASE_FEATURES)

    for column in BASE_FEATURES:
        for lag in LAGS:
            name = f"{column}_lag{lag}"
            df[name] = df[column].shift(lag)
            feature_columns.append(name)

    df["target_cpu"] = df["cpu_mean"].shift(-1)
    df["target_memory"] = df["memory_mean"].shift(-1)

    df = df.dropna().reset_index(drop=True)

    split = int(len(df) * 0.8)
    train = df.iloc[:split]
    test = df.iloc[split:]

    X_train = train[feature_columns]
    X_test = test[feature_columns]

    y_train = train[["target_cpu", "target_memory"]]
    y_test = test[["target_cpu", "target_memory"]].to_numpy()

    model = RandomForestRegressor(
        n_estimators=200,
        max_depth=6,
        min_samples_leaf=3,
        random_state=42,
        n_jobs=-1,
    )

    model.fit(X_train, y_train)
    predictions = model.predict(X_test)

    # Persistence baseline: predict the next value using
    # the latest observed value.
    baseline = test[["cpu_mean", "memory_mean"]].to_numpy()

    print("\nChronological holdout evaluation")
    print(f"Training samples: {len(train)}")
    print(f"Testing samples: {len(test)}")

    for i, name in enumerate(["CPU", "Memory"]):
        model_mae = mean_absolute_error(y_test[:, i], predictions[:, i])
        model_rmse = np.sqrt(
            mean_squared_error(y_test[:, i], predictions[:, i])
        )

        baseline_mae = mean_absolute_error(y_test[:, i], baseline[:, i])
        baseline_rmse = np.sqrt(
            mean_squared_error(y_test[:, i], baseline[:, i])
        )

        print(f"\n{name}")
        print(f"Random Forest MAE: {model_mae:.4f}")
        print(f"Random Forest RMSE: {model_rmse:.4f}")
        print(f"Persistence MAE: {baseline_mae:.4f}")
        print(f"Persistence RMSE: {baseline_rmse:.4f}")

    MODEL_FILE.parent.mkdir(parents=True, exist_ok=True)

    joblib.dump(
        {
            "model": model,
            "features": feature_columns,
            "targets": TARGETS,
            "lags": LAGS,
            "base_features": BASE_FEATURES,
            "prediction_horizon": "next 5-minute interval",
        },
        MODEL_FILE,
    )

    print(f"\nModel saved to: {MODEL_FILE}")


if __name__ == "__main__":
    main()
