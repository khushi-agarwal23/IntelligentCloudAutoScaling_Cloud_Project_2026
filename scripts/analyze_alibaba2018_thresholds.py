from pathlib import Path
import pandas as pd

source = Path("data/alibaba2018/processed/machine_timeseries.csv")
output = Path("data/alibaba2018/processed/threshold_sweep_triple_split.csv")
EXPECTED_INTERVAL = 10

df = pd.read_csv(source).sort_values("timestamp").reset_index(drop=True)
df = df[df["timestamp"] >= 160380].copy().reset_index(drop=True)
if not df["timestamp"].diff().dropna().eq(EXPECTED_INTERVAL).all():
    raise ValueError("Selected trace segment contains timestamp gaps; split into continuous segments before evaluating.")

# Match the chronological evaluation after lag preparation.
for col in ["cpu_mean", "memory_mean"]:
    for lag in [1, 2, 3, 6]:
        df[f"{col}_lag_{lag}"] = df[col].shift(lag)

df["target_cpu"] = df["cpu_mean"].shift(-1)
df["target_memory"] = df["memory_mean"].shift(-1)
df = df.dropna().reset_index(drop=True)

train_end = int(len(df) * 0.60)
validation_end = int(len(df) * 0.80)
train = df.iloc[:train_end]
validation = df.iloc[train_end:validation_end].copy()
test = df.iloc[validation_end:].copy()
if train_end < 2 or validation.empty or test.empty:
    raise ValueError("Not enough rows for chronological train/validation/test splits.")

# Thresholds and high-utilization labels are defined using training data only.
percentiles = [75, 80, 85, 90, 95]
rows = []

for percentile in percentiles:
    cpu_threshold = train["cpu_mean"].quantile(percentile / 100)
    memory_threshold = train["memory_mean"].quantile(percentile / 100)

    def evaluate(frame):
        predicted_up = (
            (frame["cpu_mean_lag_1"] >= cpu_threshold)
            | (frame["memory_mean_lag_1"] >= memory_threshold)
        )
        actual_either_high = (
            (frame["target_cpu"] >= cpu_threshold)
            | (frame["target_memory"] >= memory_threshold)
        )
        tp = int((predicted_up & actual_either_high).sum())
        fp = int((predicted_up & ~actual_either_high).sum())
        fn = int((~predicted_up & actual_either_high).sum())
        tn = int((~predicted_up & ~actual_either_high).sum())
        precision = tp / (tp + fp) if tp + fp else 0
        recall = tp / (tp + fn) if tp + fn else 0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0
        return {
            "scale_up_count": int(predicted_up.sum()),
            "scale_up_rate_percent": round(predicted_up.mean() * 100, 2),
            "high_utilization_count": int(actual_either_high.sum()),
            "true_positive": tp,
            "false_positive": fp,
            "false_negative": fn,
            "true_negative": tn,
            "precision_percent": round(precision * 100, 2),
            "recall_percent": round(recall * 100, 2),
            "f1_percent": round(f1 * 100, 2),
        }

    validation_metrics = evaluate(validation)
    test_metrics = evaluate(test)

    rows.append({
        "threshold_percentile": percentile,
        "cpu_threshold": round(cpu_threshold, 4),
        "memory_threshold": round(memory_threshold, 4),
        **{f"validation_{key}": value for key, value in validation_metrics.items()},
        **{f"test_{key}": value for key, value in test_metrics.items()},
    })

result = pd.DataFrame(rows)
result["selected_on_validation"] = result["validation_f1_percent"].eq(result["validation_f1_percent"].max())
output.parent.mkdir(parents=True, exist_ok=True)
result.to_csv(output, index=False)

print(result.to_string(index=False))
print(f"\nChronological rows: train={len(train)}, validation={len(validation)}, test={len(test)}")
print("Threshold candidates are derived from training data only; percentile selection uses validation F1 only.")
print("Held-out test metrics are reported for confirmation and were not used to select the percentile.")
print(f"\nSaved results to: {output}")
print("\nImportant: this is an offline threshold sensitivity analysis,")
print("not proof of real server capacity, cost savings, or AWS performance.")
