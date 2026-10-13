from pathlib import Path
import random
import pickle

import numpy as np
import pandas as pd


# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------
DATA_PATH = Path("data/alibaba2018/processed/machine_timeseries.csv")
OUTPUT_DIR = Path("data/alibaba2018/processed")
MODEL_PATH = Path("models/alibaba2018_q_table.pkl")
RESULT_PATH = OUTPUT_DIR / "alibaba2018_rl_evaluation.csv"

SEED = 42
TRAIN_FRACTION = 0.70
VALIDATION_FRACTION = 0.15

MIN_INSTANCES = 1
MAX_INSTANCES = 3
ACTIONS = (0, 1, 2)  # 0=scale in, 1=maintain, 2=scale out

EPISODES = 150
MAX_STEPS_PER_EPISODE = 300

CPU_BINS = (30.0, 45.0)
MEMORY_BINS = (87.0, 90.0)

random.seed(SEED)
np.random.seed(SEED)


# ---------------------------------------------------------
# Q-learning agent
# ---------------------------------------------------------
class Agent:
    def __init__(self):
        self.q = {}
        self.alpha = 0.10
        self.gamma = 0.90
        self.epsilon = 1.0
        self.epsilon_min = 0.05
        self.epsilon_decay = 0.97

    def values(self, state):
        if state not in self.q:
            self.q[state] = [0.0, 0.0, 0.0]
        return self.q[state]

    def choose(self, state, training=True):
        values = self.values(state)

        if training and random.random() < self.epsilon:
            return random.choice(ACTIONS)

        best = max(values)
        choices = [a for a, value in enumerate(values) if value == best]
        return random.choice(choices)

    def update(self, state, action, reward, next_state):
        current = self.values(state)[action]
        future = max(self.values(next_state))
        self.q[state][action] = current + self.alpha * (
            reward + self.gamma * future - current
        )


# ---------------------------------------------------------
# Data preparation: preserve chronology and the known gap
# ---------------------------------------------------------
def load_data():
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Dataset not found: {DATA_PATH}")

    df = pd.read_csv(DATA_PATH)
    required = {"timestamp", "cpu_mean", "memory_mean"}
    missing = required - set(df.columns)

    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    df = df.sort_values("timestamp").reset_index(drop=True)

    # Use the previously identified regular second segment.
    df = df[df["timestamp"] >= 160380].copy()
    df = df.dropna(subset=["cpu_mean", "memory_mean"])
    df = df[
        df["cpu_mean"].between(0, 100)
        & df["memory_mean"].between(0, 100)
    ].reset_index(drop=True)

    if len(df) < 100:
        raise ValueError("Not enough valid observations to evaluate.")

    gaps = df["timestamp"].diff().dropna()
    if not gaps.eq(10).all():
        raise ValueError(
            "The selected workload segment is not uniformly spaced "
            "at 10-second intervals. Inspect timestamp gaps before training."
        )

    n = len(df)
    train_end = int(n * TRAIN_FRACTION)
    validation_end = int(n * (TRAIN_FRACTION + VALIDATION_FRACTION))

    return (
        df.iloc[:train_end].reset_index(drop=True),
        df.iloc[train_end:validation_end].reset_index(drop=True),
        df.iloc[validation_end:].reset_index(drop=True),
    )


def levels(cpu, memory):
    cpu_level = int(np.digitize(cpu, CPU_BINS))
    memory_level = int(np.digitize(memory, MEMORY_BINS))
    return cpu_level, memory_level


def state_for(row, instances):
    cpu_level, memory_level = levels(
        float(row["cpu_mean"]), float(row["memory_mean"])
    )
    return cpu_level, memory_level, instances


# ---------------------------------------------------------
# Explicit proxy reward
# ---------------------------------------------------------
def reward_for(action, cpu, memory, instances):
    """
    Assumption-based proxy reward, not a measured AWS reward.

    High CPU/memory: scaling out is encouraged.
    Low CPU and memory: scaling in is encouraged if feasible.
    Otherwise: maintaining is encouraged.
    Every actual instance change receives a small penalty.
    """

    high = cpu >= 45.0 or memory >= 90.0
    low = cpu < 30.0 and memory < 87.0

    next_instances = instances
    if action == 0 and instances > MIN_INSTANCES:
        next_instances -= 1
    elif action == 2 and instances < MAX_INSTANCES:
        next_instances += 1

    if high:
        base = {0: -5.0, 1: -1.0, 2: 2.0}[action]
    elif low:
        base = {0: 2.0, 1: 1.0, 2: -3.0}[action]
    else:
        base = {0: -1.0, 1: 2.0, 2: -1.0}[action]

    changed = next_instances != instances
    return base - (0.25 if changed else 0.0), next_instances


# ---------------------------------------------------------
# Train on the first chronological segment only
# ---------------------------------------------------------
def train_agent(train_df):
    agent = Agent()
    rng = random.Random(SEED)

    # Episodes start at random points within training data, then move forward.
    for episode in range(EPISODES):
        max_start = max(0, len(train_df) - MAX_STEPS_PER_EPISODE - 1)
        start = rng.randint(0, max_start)
        instances = rng.randint(MIN_INSTANCES, MAX_INSTANCES)

        for offset in range(MAX_STEPS_PER_EPISODE):
            idx = start + offset
            row = train_df.iloc[idx]
            next_row = train_df.iloc[idx + 1]

            state = state_for(row, instances)
            action = agent.choose(state, training=True)
            reward, next_instances = reward_for(
                action,
                float(row["cpu_mean"]),
                float(row["memory_mean"]),
                instances,
            )

            next_state = state_for(next_row, next_instances)
            agent.update(state, action, reward, next_state)
            instances = next_instances

        agent.epsilon = max(
            agent.epsilon_min, agent.epsilon * agent.epsilon_decay
        )

        if (episode + 1) % 25 == 0:
            print(
                f"Episode {episode + 1}/{EPISODES} | "
                f"States learned: {len(agent.q)} | "
                f"Epsilon: {agent.epsilon:.3f}"
            )

    return agent


# ---------------------------------------------------------
# Validation-based policy selection
# ---------------------------------------------------------
def evaluate_policy(df, policy_name, agent=None, cpu_high=45.0,
                    memory_high=90.0, initial_instances=2):
    rows = []
    instances = initial_instances

    for i in range(len(df) - 1):
        row = df.iloc[i]
        next_row = df.iloc[i + 1]
        cpu = float(row["cpu_mean"])
        memory = float(row["memory_mean"])

        if policy_name == "q_learning":
            state = state_for(row, instances)
            action = agent.choose(state, training=False)

        elif policy_name == "threshold":
            if cpu >= cpu_high or memory >= memory_high:
                action = 2
            elif cpu < 30.0 and memory < 87.0:
                action = 0
            else:
                action = 1

        elif policy_name == "persistence":
            # No change to the instance count.
            action = 1

        else:
            raise ValueError(f"Unknown policy: {policy_name}")

        reward, new_instances = reward_for(action, cpu, memory, instances)

        rows.append({
            "policy": policy_name,
            "timestamp": int(row["timestamp"]),
            "cpu_current": cpu,
            "memory_current": memory,
            "cpu_next": float(next_row["cpu_mean"]),
            "memory_next": float(next_row["memory_mean"]),
            "instances_before": instances,
            "action": action,
            "instances_after": new_instances,
            "proxy_reward": reward,
        })

        instances = new_instances

    return pd.DataFrame(rows)


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)

    train_df, validation_df, test_df = load_data()

    print("Alibaba 2018 trace-based Q-learning experiment")
    print(f"Training observations:   {len(train_df)}")
    print(f"Validation observations: {len(validation_df)}")
    print(f"Test observations:       {len(test_df)}")
    print("Sampling interval: 10 seconds")
    print("Reward: assumption-based proxy; not measured cloud cost/latency")

    agent = train_agent(train_df)

    # Save this model separately from the original Q-table.
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(agent.q, f)

    # Compare candidate policies on validation data. No Q-table updates occur.
    validation_results = []
    for name in ["q_learning", "threshold", "persistence"]:
        result = evaluate_policy(
            validation_df, name, agent=agent
        )
        validation_results.append({
            "policy": name,
            "mean_proxy_reward": result["proxy_reward"].mean(),
            "scale_up_rate_percent": (result["action"] == 2).mean() * 100,
            "scale_in_rate_percent": (result["action"] == 0).mean() * 100,
        })

    validation_summary = pd.DataFrame(validation_results)
    print("\nValidation results (for policy inspection only):")
    print(validation_summary.round(3).to_string(index=False))

    # Evaluate all candidates on the untouched test period.
    test_frames = []
    for name in ["q_learning", "threshold", "persistence"]:
        test_frames.append(
            evaluate_policy(test_df, name, agent=agent)
        )

    results = pd.concat(test_frames, ignore_index=True)
    results.to_csv(RESULT_PATH, index=False)

    print("\nHeld-out test summary:")
    summary = results.groupby("policy").agg(
        observations=("action", "size"),
        mean_proxy_reward=("proxy_reward", "mean"),
        scale_up_count=("action", lambda x: int((x == 2).sum())),
        scale_in_count=("action", lambda x: int((x == 0).sum())),
        maintain_count=("action", lambda x: int((x == 1).sum())),
        mean_instances=("instances_after", "mean"),
    )
    summary["scale_up_rate_percent"] = (
        summary["scale_up_count"] / summary["observations"] * 100
    )
    print(summary.round(3).to_string())

    print(f"\nSeparate model saved to: {MODEL_PATH}")
    print(f"Test decisions saved to: {RESULT_PATH}")
    print("\nLIMITATIONS:")
    print("- This is an offline trace replay, not live AWS scaling.")
    print("- Rewards are assumptions, not measured cost or latency.")
    print("- The trace is aggregate data-center utilization, not a direct")
    print("  measurement of e-commerce demand or required server count.")
    print("- Do not claim this experiment proves RL is better unless the")
    print("  held-out results and evaluation assumptions support that claim.")


if __name__ == "__main__":
    main()
