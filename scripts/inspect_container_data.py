
from pathlib import Path
import csv
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "alibaba" / "raw" / "alibaba-trace-2017"

FILES = [
    "container_usage.csv",
    "server_usage.csv",
    "batch_instance.csv",
    "batch_task.csv",
    "container_event.csv",
    "server_event.csv",
]

def inspect_file(filename):
    path = DATA_DIR / filename

    print("\n" + "=" * 70)
    print(f"FILE: {filename}")
    print("=" * 70)

    if not path.exists():
        print("File not found.")
        return

    with path.open("r", encoding="utf-8", newline="") as file:
        reader = csv.reader(file)
        rows = []

        for row in reader:
            rows.append(row)
            if len(rows) >= 5:
                break

    if not rows:
        print("File is empty.")
        return

    print(f"Columns per row: {[len(row) for row in rows]}")
    print("Sample rows:")
    for row in rows[:3]:
        print(row)

    try:
        df = pd.read_csv(
            path,
            header=None,
            nrows=100_000,
            low_memory=False
        )

        print(f"\nColumns: {df.shape[1]}")
        print(f"Sampled rows: {len(df):,}")
        print("\nNumeric summary:")
        print(df.describe().round(3).to_string())

        print("\nMissing values in sample:")
        print(df.isna().sum().to_string())

    except Exception as exc:
        print(f"Could not summarize file: {exc}")

def main():
    for filename in FILES:
        inspect_file(filename)

if __name__ == "__main__":
    main()
