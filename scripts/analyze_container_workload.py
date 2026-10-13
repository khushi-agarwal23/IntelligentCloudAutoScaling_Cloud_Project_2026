
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]

DATA_FILE = (
    ROOT / "data" / "alibaba" / "processed" /
    "container_timeseries.csv"
)

OUTPUT_DIR = ROOT / "data" / "alibaba" / "processed"

def main():
    if not DATA_FILE.exists():
        raise FileNotFoundError(f"Missing file: {DATA_FILE}")

    df = pd.read_csv(DATA_FILE).sort_values("timestamp")
    df = df.reset_index(drop=True)

    split = int(len(df) * 0.60)
    train = df.iloc[:split]
    test = df.iloc[split:]

    print("FULL TIME-SERIES SUMMARY")
    print(f"Total windows: {len(df)}")
    print(f"Training windows: {len(train)}")
    print(f"Evaluation windows: {len(test)}")
    print(f"First timestamp: {df['timestamp'].min()}")
    print(f"Last timestamp: {df['timestamp'].max()}")

    for column in ["cpu_p95", "memory_p95"]:
        print(f"\n{column}")
        print(f"Training minimum: {train[column].min():.2f}")
        print(f"Training median: {train[column].median():.2f}")
        print(f"Training maximum: {train[column].max():.2f}")
        print(f"Evaluation minimum: {test[column].min():.2f}")
        print(f"Evaluation median: {test[column].median():.2f}")
        print(f"Evaluation maximum: {test[column].max():.2f}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Plot CPU P95.
    plt.figure(figsize=(11, 5))
    plt.plot(
        df["timestamp"], df["cpu_p95"],
        label="CPU P95"
    )
    plt.axvline(
        df.iloc[split]["timestamp"],
        linestyle="--",
        label="Train/evaluation split"
    )
    plt.xlabel("Timestamp (seconds)")
    plt.ylabel("CPU utilization (%)")
    plt.title("Alibaba Container CPU P95 Over Time")
    plt.legend()
    plt.tight_layout()

    cpu_plot = OUTPUT_DIR / "container_cpu_p95.png"
    plt.savefig(cpu_plot, dpi=150)
    plt.close()

    # Plot memory P95.
    plt.figure(figsize=(11, 5))
    plt.plot(
        df["timestamp"], df["memory_p95"],
        label="Memory P95"
    )
    plt.axvline(
        df.iloc[split]["timestamp"],
        linestyle="--",
        label="Train/evaluation split"
    )
    plt.xlabel("Timestamp (seconds)")
    plt.ylabel("Memory utilization (%)")
    plt.title("Alibaba Container Memory P95 Over Time")
    plt.legend()
    plt.tight_layout()

    memory_plot = OUTPUT_DIR / "container_memory_p95.png"
    plt.savefig(memory_plot, dpi=150)
    plt.close()

    print(f"\nSaved CPU plot: {cpu_plot}")
    print(f"Saved memory plot: {memory_plot}")

if __name__ == "__main__":
    main()
