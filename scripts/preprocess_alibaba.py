
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

RAW_FILE = ROOT / "data" / "alibaba" / "raw" / "server_usage.csv"
OUTPUT_FILE = ROOT / "data" / "alibaba" / "processed" / "cluster_timeseries.csv"

COLUMNS = [
    "timestamp",
    "machine_id",
    "cpu_percent",
    "memory_percent",
    "disk_percent",
    "load_1",
    "load_5",
    "load_15",
]


def main():
    if not RAW_FILE.exists():
        raise FileNotFoundError(f"Dataset not found: {RAW_FILE}")

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    print("Reading Alibaba server usage data...")

    df = pd.read_csv(
        RAW_FILE,
        header=None,
        names=COLUMNS,
    )

    print(f"Original rows: {len(df):,}")

    numeric_columns = [
        "timestamp",
        "cpu_percent",
        "memory_percent",
        "disk_percent",
        "load_1",
        "load_5",
        "load_15",
    ]

    for column in numeric_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    df = df.dropna(
        subset=["timestamp", "cpu_percent", "memory_percent"]
    )

    df = df[
        df["cpu_percent"].between(0, 100)
        & df["memory_percent"].between(0, 100)
    ]

    print(f"Valid rows: {len(df):,}")

    # Aggregate recorded machine measurements by timestamp.
    result = (
        df.groupby("timestamp")
        .agg(
            cpu_mean=("cpu_percent", "mean"),
            cpu_p95=("cpu_percent", lambda x: x.quantile(0.95)),
            memory_mean=("memory_percent", "mean"),
            memory_p95=("memory_percent", lambda x: x.quantile(0.95)),
            disk_mean=("disk_percent", "mean"),
            load1_mean=("load_1", "mean"),
            load5_mean=("load_5", "mean"),
            load15_mean=("load_15", "mean"),
            machine_count=("machine_id", "nunique"),
        )
        .reset_index()
        .sort_values("timestamp")
    )

    result.to_csv(OUTPUT_FILE, index=False)

    print("\nPreprocessing complete.")
    print(f"Output: {OUTPUT_FILE}")
    print(f"Time windows: {len(result):,}")
    print("\nFirst five rows:")
    print(result.head().to_string(index=False))

    print("\nSummary:")
    print(result[["cpu_mean", "memory_mean"]].describe())


if __name__ == "__main__":
    main()
