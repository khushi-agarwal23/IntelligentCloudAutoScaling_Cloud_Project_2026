from pathlib import Path
import numpy as np
import pandas as pd

DATA = Path("data/alibaba2018/processed/machine_timeseries.csv")
OUT = Path("data/alibaba2018/processed")
RESULT = OUT / "capacity_response_sensitivity.csv"

MIN_INSTANCES = 1
MAX_INSTANCES = 3
TRAIN_FRACTION = 0.70
VALIDATION_FRACTION = 0.15
CPU_LIMIT = 80.0
MEMORY_LIMIT = 95.0
INITIAL_INSTANCES = 2

# Explicit sensitivity assumptions: utilization is divided by the
# instance-count ratio when the count changes. These are NOT measured
# capacity-response coefficients.
CAPACITY_FACTORS = [0.75, 1.0, 1.25]

def load_trace():
    df = pd.read_csv(DATA).sort_values("timestamp").reset_index(drop=True)
    df = df[df["timestamp"] >= 160380].copy()
    df = df.dropna(subset=["cpu_mean", "memory_mean"]).reset_index(drop=True)

    if not {"timestamp", "cpu_mean", "memory_mean"}.issubset(df.columns):
        raise ValueError("Required timestamp, cpu_mean, memory_mean columns missing.")

    if len(df) < 100:
        raise ValueError("Not enough trace observations.")

    if not df["timestamp"].diff().dropna().eq(10).all():
        raise ValueError("Selected trace segment is not uniformly spaced at 10 seconds.")

    n = len(df)
    train_end = int(n * TRAIN_FRACTION)
    validation_end = int(n * (TRAIN_FRACTION + VALIDATION_FRACTION))

    return (
        df.iloc[:train_end].reset_index(drop=True),
        df.iloc[train_end:validation_end].reset_index(drop=True),
        df.iloc[validation_end:].reset_index(drop=True),
    )

def bins(cpu, memory):
    return (
        int(np.digitize(cpu, [30.0, 45.0])),
        int(np.digitize(memory, [87.0, 90.0])),
    )

def apply_action(action, instances):
    if action == 0:
        return max(MIN_INSTANCES, instances - 1)
    if action == 2:
        return min(MAX_INSTANCES, instances + 1)
    return instances

def threshold_action(cpu, memory):
    if cpu >= 45.0 or memory >= 90.0:
        return 2
    if cpu < 30.0 and memory < 87.0:
        return 0
    return 1

def q_learning_action(q_table, cpu, memory, instances):
    state = (*bins(cpu, memory), instances)
    values = q_table.get(state, [0.0, 0.0, 0.0])
    return int(np.argmax(values))

def run_policy(df, policy, capacity_factor, q_table=None):
    instances = INITIAL_INSTANCES
    previous_instances = instances
    rows = []

    for i in range(len(df) - 1):
        row = df.iloc[i]
        next_row = df.iloc[i + 1]

        cpu = float(row["cpu_mean"])
        memory = float(row["memory_mean"])

        if policy == "q_learning":
            action = q_learning_action(q_table, cpu, memory, instances)
        elif policy == "threshold":
            action = threshold_action(cpu, memory)
        else:
            action = 1

        new_instances = apply_action(action, instances)

        # Hypothetical next-utilization model:
        # utilization changes inversely with instance count, multiplied
        # by an explicit capacity sensitivity factor. This is an assumption.
        ratio = instances / new_instances
        next_cpu = min(100.0, max(0.0,
            float(next_row["cpu_mean"]) * ratio * capacity_factor))
        next_memory = min(100.0, max(0.0,
            float(next_row["memory_mean"]) * ratio * capacity_factor))

        overloaded = next_cpu > CPU_LIMIT or next_memory > MEMORY_LIMIT
        change = new_instances != instances

        # Transparent proxy cost: instance usage plus a small action-change
        # penalty and a larger overload penalty. Units are arbitrary.
        proxy_cost = (
            new_instances
            + (0.25 if change else 0.0)
            + (5.0 if overloaded else 0.0)
        )

        rows.append({
            "policy": policy,
            "capacity_factor": capacity_factor,
            "timestamp": int(row["timestamp"]),
            "action": action,
            "instances_before": instances,
            "instances_after": new_instances,
            "hypothetical_next_cpu": next_cpu,
            "hypothetical_next_memory": next_memory,
            "overload_flag": int(overloaded),
            "proxy_cost": proxy_cost,
        })

        previous_instances = instances
        instances = new_instances

    return pd.DataFrame(rows)

def main():
    if not DATA.exists():
        raise FileNotFoundError(f"Missing dataset: {DATA}")

    _, validation, test = load_trace()

    # Load the Q-table created by the separate Alibaba experiment.
    model_path = Path("models/alibaba2018_q_table.pkl")
    if model_path.exists():
        import pickle
        with open(model_path, "rb") as f:
            q_table = pickle.load(f)
    else:
        q_table = None
        print("WARNING: Alibaba Q-table not found; Q-learning uses default ties.")

    print(f"Validation observations: {len(validation)}")
    print(f"Test observations: {len(test)}")
    print("Running sensitivity analysis on the held-out test segment.")
    print("All capacity-response effects and proxy costs are hypothetical.")

    results = []
    for factor in CAPACITY_FACTORS:
        for policy in ["q_learning", "threshold", "persistence"]:
            result = run_policy(test, policy, factor, q_table)
            results.append(result)

    all_results = pd.concat(results, ignore_index=True)
    OUT.mkdir(parents=True, exist_ok=True)
    all_results.to_csv(RESULT, index=False)

    summary = all_results.groupby(["capacity_factor", "policy"]).agg(
        observations=("action", "size"),
        mean_instances=("instances_after", "mean"),
        scale_up_count=("action", lambda s: int((s == 2).sum())),
        scale_in_count=("action", lambda s: int((s == 0).sum())),
        overload_rate_percent=("overload_flag", lambda s: 100 * s.mean()),
        mean_proxy_cost=("proxy_cost", "mean"),
    ).reset_index()

    print("\nSensitivity results:")
    print(summary.round(3).to_string(index=False))
    print(f"\nDetailed results saved to: {RESULT}")
    print("\nDo not interpret proxy costs or overload rates as real AWS measurements.")

if __name__ == "__main__":
    main()
