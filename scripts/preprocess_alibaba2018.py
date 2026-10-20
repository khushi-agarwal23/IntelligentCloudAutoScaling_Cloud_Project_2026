
from pathlib import Path
import json

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

INPUT_FILE = (
    ROOT / "data" / "alibaba2018" / "raw"
    / "extracted" / "machine_usage.csv"
)

WORK_DIR = ROOT / "data" / "alibaba2018" / "processed" / "checkpoints"
OUTPUT_DIR = ROOT / "data" / "alibaba2018" / "processed"
OUTPUT_FILE = OUTPUT_DIR / "machine_timeseries.csv"
PROGRESS_FILE = WORK_DIR / "progress.json"

CHUNK_SIZE = 500_000

COLUMNS = [
    "machine_id", "timestamp", "cpu_util_percent",
    "mem_util_percent", "mem_gps", "mkpi",
    "net_in", "net_out", "disk_io_percent",
]


def main():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Dataset not found: {INPUT_FILE}")

    WORK_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if PROGRESS_FILE.exists():
        progress = json.loads(PROGRESS_FILE.read_text())
        next_chunk = int(progress["next_chunk"])
        print(f"Resuming from chunk {next_chunk + 1}.")
    else:
        next_chunk = 0
        print("Starting from the beginning.")

    # Each chunk has its own durable checkpoint file.
    reader = pd.read_csv(
        INPUT_FILE,
        header=None,
        names=COLUMNS,
        chunksize=CHUNK_SIZE,
        low_memory=False,
    )

    for chunk_number, chunk in enumerate(reader):
        checkpoint = WORK_DIR / f"chunk_{chunk_number:06d}.csv"

        if chunk_number < next_chunk:
            continue

        if checkpoint.exists():
            print(f"Chunk {chunk_number + 1}: checkpoint already exists.")
        else:
            for col in COLUMNS[1:]:
                chunk[col] = pd.to_numeric(chunk[col], errors="coerce")

            chunk = chunk.dropna(
                subset=[
                    "timestamp",
                    "cpu_util_percent",
                    "mem_util_percent",
                ]
            )

            grouped = chunk.groupby("timestamp").agg(
                cpu_sum=("cpu_util_percent", "sum"),
                cpu_count=("cpu_util_percent", "count"),
                mem_sum=("mem_util_percent", "sum"),
                mem_count=("mem_util_percent", "count"),
                machine_count=("machine_id", "nunique"),
            ).reset_index()

            grouped.to_csv(checkpoint, index=False)

        # Update progress only after the checkpoint is safely written.
        temp_progress = PROGRESS_FILE.with_suffix(".tmp")
        temp_progress.write_text(
            json.dumps({"next_chunk": chunk_number + 1})
        )
        temp_progress.replace(PROGRESS_FILE)

        print(
            f"Saved checkpoint for chunk {chunk_number + 1}; "
            f"{checkpoint.name}"
        )

    print("Combining checkpoint files...")

    # Sum/count aggregation avoids incorrect averages across chunks.
    combined = {}

    for checkpoint in sorted(WORK_DIR.glob("chunk_*.csv")):
        partial = pd.read_csv(checkpoint)

        for row in partial.itertuples(index=False):
            timestamp = int(row.timestamp)

            if timestamp not in combined:
                combined[timestamp] = {
                    "cpu_sum": 0.0,
                    "cpu_count": 0,
                    "mem_sum": 0.0,
                    "mem_count": 0,
                    "machine_count_sum": 0,
                }

            item = combined[timestamp]
            item["cpu_sum"] += row.cpu_sum
            item["cpu_count"] += int(row.cpu_count)
            item["mem_sum"] += row.mem_sum
            item["mem_count"] += int(row.mem_count)
            item["machine_count_sum"] += int(row.machine_count)

    records = []

    for timestamp, item in sorted(combined.items()):
        if item["cpu_count"] == 0 or item["mem_count"] == 0:
            continue

        records.append({
            "timestamp": timestamp,
            "cpu_mean": item["cpu_sum"] / item["cpu_count"],
            "memory_mean": item["mem_sum"] / item["mem_count"],
            "machine_count_sum_per_chunk": item["machine_count_sum"],
        })

    result = pd.DataFrame(records)
    result.to_csv(OUTPUT_FILE, index=False)

    print("\nPreprocessing complete.")
    print(f"Output: {OUTPUT_FILE}")
    print(f"Timestamp rows: {len(result):,}")
    print(f"First timestamp: {result['timestamp'].min()}")
    print(f"Last timestamp: {result['timestamp'].max()}")
    print(result[["cpu_mean", "memory_mean"]].describe().round(3))


if __name__ == "__main__":
    main()
