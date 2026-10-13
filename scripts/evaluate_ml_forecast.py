
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error

ROOT = Path(__file__).resolve().parents[1]

INPUT_FILE = (
    ROOT / "data" / "alibaba2018" / "processed"
    / "machine_timeseries.csv"
)

OUTPUT_FILE = (
    ROOT / "data" / "alibaba2018" / "processed"
    / "forecast_model_comparison_triple_split.csv"
)

SEGMENT_START = 160380
EXPECTED_INTERVAL = 10
LAGS = [1, 2, 3, 6]


def main():
    df = pd.read_csv(INPUT_FILE)
    df = df.sort_values("timestamp").reset_index(drop=True)

    # Use the same continuous segment as the persistence baseline.
    df = df[df["timestamp"] >= SEGMENT_START].copy()
    df = df.sort_values("timestamp").reset_index(drop=True)

    for col in ["cpu_mean", "memory_mean"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(
        subset=["timestamp", "cpu_mean", "memory_mean"]
    ).reset_index(drop=True)

    intervals = df["timestamp"].diff().dropna()
    if not intervals.eq(EXPECTED_INTERVAL).all():
        raise ValueError(
            "Irregular timestamps found. Split the series at gaps first."
        )

    # Predict CPU and memory at time t using observations before time t.
    for col in ["cpu_mean", "memory_mean"]:
        for lag in LAGS:
            df[f"{col}_lag_{lag}"] = df[col].shift(lag)

    df = df.dropna().reset_index(drop=True)

    features = [
        f"{col}_lag_{lag}"
        for col in ["cpu_mean", "memory_mean"]
        for lag in LAGS
    ]
    targets = ["cpu_mean", "memory_mean"]

    train_end = int(len(df) * 0.60)
    validation_end = int(len(df) * 0.80)
    if train_end < 2 or validation_end <= train_end or validation_end >= len(df):
        raise ValueError("Not enough rows for chronological train/validation/test splits.")
    train = df.iloc[:train_end].copy()
    validation = df.iloc[train_end:validation_end].copy()
    train_validation = df.iloc[:validation_end].copy()
    test = df.iloc[validation_end:].copy()

    X_train = train[features]
    X_test = test[features]

    results = []

    print("Alibaba 2018: forecasting model comparison")
    print("-------------------------------------------")
    print(f"Training rows: {len(train):,}")
    print(f"Validation rows: {len(validation):,}")
    print(f"Testing rows: {len(test):,}")
    print(f"Features: {features}")

    for target in targets:
        model = RandomForestRegressor(
            n_estimators=100,
            max_depth=12,
            min_samples_leaf=5,
            random_state=42,
            n_jobs=1,
        )

        model.fit(X_train, train[target])
        validation_predictions = model.predict(validation[features])
        validation_actual = validation[target].to_numpy()
        validation_mae = mean_absolute_error(validation_actual, validation_predictions)
        validation_rmse = np.sqrt(mean_squared_error(validation_actual, validation_predictions))

        # Hyperparameters are fixed in advance; refit on train + validation,
        # then evaluate once on the untouched final 20% test segment.
        model.fit(train_validation[features], train_validation[target])
        predictions = model.predict(X_test)
        actual = test[target].to_numpy()

        mae = mean_absolute_error(actual, predictions)
        rmse = np.sqrt(mean_squared_error(actual, predictions))

        # Persistence prediction: most recent observed value.
        validation_persistence = validation[f"{target}_lag_1"].to_numpy()
        validation_baseline_mae = mean_absolute_error(validation_actual, validation_persistence)
        validation_baseline_rmse = np.sqrt(mean_squared_error(validation_actual, validation_persistence))
        persistence_predictions = test[f"{target}_lag_1"].to_numpy()
        baseline_mae = mean_absolute_error(actual, persistence_predictions)
        baseline_rmse = np.sqrt(mean_squared_error(actual, persistence_predictions))

        results.append({
            "target": target,
            "model": "RandomForest",
            "forecast_horizon_seconds": EXPECTED_INTERVAL,
            "training_rows": len(train),
            "validation_rows": len(validation),
            "test_rows": len(test),
            "model_validation_mae_percentage_points": validation_mae,
            "model_validation_rmse_percentage_points": validation_rmse,
            "persistence_validation_mae_percentage_points": validation_baseline_mae,
            "persistence_validation_rmse_percentage_points": validation_baseline_rmse,
            "model_test_mae_percentage_points": mae,
            "model_test_rmse_percentage_points": rmse,
            "persistence_test_mae_percentage_points": baseline_mae,
            "persistence_test_rmse_percentage_points": baseline_rmse,
            "mae_improvement_percent": (
                (baseline_mae - mae) / baseline_mae * 100
                if baseline_mae else 0.0
            ),
        })

        print(f"\n{target}")
        print(f"  Validation RF vs persistence MAE: {validation_mae:.4f} vs {validation_baseline_mae:.4f}")
        print(f"  Test RF MAE/RMSE: {mae:.4f} / {rmse:.4f}")
        print(f"  Test persistence MAE/RMSE: {baseline_mae:.4f} / {baseline_rmse:.4f}")
        print(
            "  MAE improvement: "
            f"{results[-1]['mae_improvement_percent']:.2f}%"
        )

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(results).to_csv(OUTPUT_FILE, index=False)
    print(f"\nResults saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
