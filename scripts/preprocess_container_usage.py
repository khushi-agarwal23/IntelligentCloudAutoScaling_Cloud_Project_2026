
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

INPUT_FILE = (
    ROOT / "data" / "alibaba" / "raw" /
    "alibaba-trace-2017" / "container_usage.csv"
)

OUTPUT_FILE = (
    ROOT / "data" / "alibaba" / "processed" /
    "container_timeseries.csv"
)

COLUMNS = [
    "timestamp",
    "instance_id",
    "cpu_util",
    "memory_util",
    "disk_util",
    "load1",
    "load5",
    "load15",
    "avg_cpi",
    "avg_mpki",
    "max_cpi",
    "max_mpki",
]

def main():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Container usage file not found: {INPUT_FILE}"
        )

    print("Loading Alibaba container usage data...")
    print(f"Input: {INPUT_FILE}")

    # Read only the columns needed for utilization analysis.
    # float32 reduces memory usage for the large CSV.
    df = pd.read_csv(
        INPUT_FILE,
        header=None,
        usecols=[0, 2, 3, 4],
        names=COLUMNS[:1] + COLUMNS[2:5],
        dtype={
            "timestamp": "int32",
            "cpu_util": "float32",
            "memory_util": "float32",
            "disk_util": "float32",
        },
    )

    original_rows = len(df)

    # Remove missing or non-finite utilization observations.
    metric_columns = ["cpu_util", "memory_util", "disk_util"]
    df = df.replace([np.inf, -np.inf], np.nan)
    df = df.dropna(subset=["timestamp"] + metric_columns)

    # Alibaba documents utilization as a percentage of requested
    # resources, with 100 representing full usage.
    # Exclude invalid utilization values outside 0-100.
    valid = (
        df[metric_columns].ge(0).all(axis=1)
        & df[metric_columns].le(100).all(axis=1)
    )
    df = df.loc[valid].copy()

    if df.empty:
        raise ValueError("No valid container utilization rows found.")

    print(f"Original rows: {original_rows:,}")
    print(f"Valid rows: {len(df):,}")
    print(f"Removed rows: {original_rows - len(df):,}")

    # Each timestamp is a measurement interval. Summarize the
    # observed containers at that timestamp.
    result = (
        df.groupby("timestamp")
        .agg(
            cpu_mean=("cpu_util", "mean"),
            cpu_p95=("cpu_util", lambda x: x.quantile(0.95)),
            cpu_max=("cpu_util", "max"),
            memory_mean=("memory_util", "mean"),
            memory_p95=("memory_util", lambda x: x.quantile(0.95)),
            memory_max=("memory_util", "max"),
            disk_mean=("disk_util", "mean"),
            container_count=("cpu_util", "size"),
        )
        .reset_index()
        .sort_values("timestamp")
        .reset_index(drop=True)
    )

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(OUTPUT_FILE, index=False, float_format="%.4f")

    print("\nContainer time series created successfully.")
    print(f"Distinct timestamps: {len(result):,}")
    print(
        f"Timestamp range: {result['timestamp'].min()} "
        f"to {result['timestamp'].max()} seconds"
    )
    print(
        f"Interval gaps greater than 300 seconds: "
        f"{int((result['timestamp'].diff() > 300).sum())}"
    )

    print("\nContainer count per timestamp:")
    print(result["container_count"].describe().round(2).to_string())

    print("\nCPU utilization summary:")
    print(
        result[["cpu_mean", "cpu_p95", "cpu_max"]]
        .describe()
        .round(2)
        .to_string()
    )

    print("\nMemory utilization summary:")
    print(
        result[["memory_mean", "memory_p95", "memory_max"]]
        .describe()
        .round(2)
        .to_string()
    )

    print(f"\nSaved to: {OUTPUT_FILE}")
    print(
        "\nNote: these are container-level summaries, not "
        "whole-cluster CPU or memory utilization."
    )

if __name__ == "__main__":
    main()
