
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error

ROOT = Path(__file__).resolve().parents[1]

DATA_FILE = (
    ROOT / "data" / "alibaba" / "processed" / "cluster_timeseries.csv"
)

BASE_FEATURES = [
    "cpu_mean",
    "memory_mean",
    "cpu_p95",
    "memory_p95",
]

TARGETS = ["cpu_mean", "memory_mean"]
LAGS = [1, 2, 3, 5, 10]


def calculate_metrics(actual, predicted):
    return {
        "MAE": mean_absolute_error(actual, predicted),
        "RMSE": np.sqrt(mean_squared_error(actual, predicted)),
    }


def main():
    if not DATA_FILE.exists():
        raise FileNotFoundError(
            f"Processed dataset not found: {DATA_FILE}"
        )

    df = pd.read_csv(DATA_FILE)
    df = df.sort_values("timestamp").reset_index(drop=True)

    print("Dataset loaded successfully.")
    print(f"Original time windows: {len(df)}")

    # Create historical features.
    feature_columns = list(BASE_FEATURES)

    for column in BASE_FEATURES:
        for lag in LAGS:
            feature_name = f"{column}_lag{lag}"
            df[feature_name] = df[column].shift(lag)
            feature_columns.append(feature_name)

    # Predict the next recorded five-minute interval.
    df["target_cpu"] = df["cpu_mean"].shift(-1)
    df["target_memory"] = df["memory_mean"].shift(-1)

    # Moving-average baseline using the latest three observations.
    df["moving_cpu"] = df["cpu_mean"].rolling(window=3).mean()
    df["moving_memory"] = df["memory_mean"].rolling(window=3).mean()

    df = df.dropna().reset_index(drop=True)

    if len(df) < 50:
        raise ValueError(
            "Not enough usable time windows after preprocessing."
        )

    # Chronological 60% training, 20% validation, 20% testing.
    n = len(df)
    train_end = int(n * 0.60)
    validation_end = int(n * 0.80)

    train = df.iloc[:train_end]
    validation = df.iloc[train_end:validation_end]
    test = df.iloc[validation_end:]

    y_train = train[["target_cpu", "target_memory"]].to_numpy()
    y_validation = validation[
        ["target_cpu", "target_memory"]
    ].to_numpy()
    y_test = test[["target_cpu", "target_memory"]].to_numpy()

    print(f"Usable time windows: {n}")
    print(f"Training windows: {len(train)}")
    print(f"Validation windows: {len(validation)}")
    print(f"Test windows: {len(test)}")

    # Baseline 1: next value equals the latest observation.
    validation_predictions = {
        "Persistence": validation[
            ["cpu_mean", "memory_mean"]
        ].to_numpy(),
        "Moving Average": validation[
            ["moving_cpu", "moving_memory"]
        ].to_numpy(),
    }

    test_predictions = {
        "Persistence": test[
            ["cpu_mean", "memory_mean"]
        ].to_numpy(),
        "Moving Average": test[
            ["moving_cpu", "moving_memory"]
        ].to_numpy(),
    }

    # Candidate learned models.
    models = {
        "Linear Regression": LinearRegression(),
        "Random Forest": RandomForestRegressor(
            n_estimators=200,
            max_depth=6,
            min_samples_leaf=3,
            random_state=42,
            n_jobs=-1,
        ),
    }

    for name, model in models.items():
        model.fit(train[feature_columns], y_train)

        validation_predictions[name] = model.predict(
            validation[feature_columns]
        )

    # Select the model using average CPU and memory MAE
    # on validation data only.
    validation_scores = {}

    print("\nVALIDATION RESULTS")

    for name, predicted in validation_predictions.items():
        cpu_metrics = calculate_metrics(
            y_validation[:, 0], predicted[:, 0]
        )
        memory_metrics = calculate_metrics(
            y_validation[:, 1], predicted[:, 1]
        )

        average_mae = (
            cpu_metrics["MAE"] + memory_metrics["MAE"]
        ) / 2

        validation_scores[name] = average_mae

        print(f"\n{name}")
        print(f"  CPU MAE: {cpu_metrics['MAE']:.4f}")
        print(f"  CPU RMSE: {cpu_metrics['RMSE']:.4f}")
        print(f"  Memory MAE: {memory_metrics['MAE']:.4f}")
        print(f"  Memory RMSE: {memory_metrics['RMSE']:.4f}")
        print(f"  Average MAE: {average_mae:.4f}")

    winner = min(validation_scores, key=validation_scores.get)

    print(f"\nSelected using validation MAE: {winner}")

    # Evaluate the selected approach once on the untouched test set.
    if winner in models:
        selected_model = models[winner]

        # Retrain using training + validation data after selection.
        train_validation = df.iloc[:validation_end]

        selected_model.fit(
            train_validation[feature_columns],
            train_validation[["target_cpu", "target_memory"]].to_numpy(),
        )

        test_predictions[winner] = selected_model.predict(
            test[feature_columns]
        )

    # Final test results.
    final_prediction = test_predictions[winner]

    cpu_test_metrics = calculate_metrics(
        y_test[:, 0], final_prediction[:, 0]
    )
    memory_test_metrics = calculate_metrics(
        y_test[:, 1], final_prediction[:, 1]
    )

    print("\nHELD-OUT TEST RESULTS")
    print(f"Selected approach: {winner}")
    print(f"CPU MAE: {cpu_test_metrics['MAE']:.4f}")
    print(f"CPU RMSE: {cpu_test_metrics['RMSE']:.4f}")
    print(f"Memory MAE: {memory_test_metrics['MAE']:.4f}")
    print(f"Memory RMSE: {memory_test_metrics['RMSE']:.4f}")

    # Show the selected approach against the persistence baseline.
    if winner != "Persistence":
        baseline_prediction = test_predictions["Persistence"]

        baseline_cpu = calculate_metrics(
            y_test[:, 0], baseline_prediction[:, 0]
        )
        baseline_memory = calculate_metrics(
            y_test[:, 1], baseline_prediction[:, 1]
        )

        print("\nPERSISTENCE BASELINE ON THE SAME TEST SET")
        print(f"CPU MAE: {baseline_cpu['MAE']:.4f}")
        print(f"Memory MAE: {baseline_memory['MAE']:.4f}")


if __name__ == "__main__":
    main()
