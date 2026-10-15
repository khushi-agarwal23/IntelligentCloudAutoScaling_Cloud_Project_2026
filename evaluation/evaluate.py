#!/usr/bin/env python3
"""
Evaluation & Comparison Script
================================

Loads trained DQN and PPO models, runs baseline policies,
compares all methods side-by-side, and generates publication-quality plots.

Usage:
    python -m evaluation.evaluate
    python evaluation/evaluate.py
"""

import os
import sys
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Project path setup
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from environment.ecommerce_env import ECommerceScalingEnv
from agents.dqn_agent import DQNAgent
from agents.ppo_agent import PPOAgent
from evaluation.metrics import (
    compute_metrics,
    compute_baseline_metrics,
    create_comparison_table,
    BaselinePolicy,
)

# Plot styling
sns.set_theme(style="whitegrid", palette="muted", font_scale=1.1)
PLOTS_DIR = os.path.join(PROJECT_ROOT, "evaluation", "plots")


def ensure_plots_dir():
    """Create plots directory if it doesn't exist."""
    os.makedirs(PLOTS_DIR, exist_ok=True)


def collect_episode_data(env, agent, n_episodes: int = 1):
    """
    Run episode(s) and collect per-step data for plotting.

    Returns:
        List of dicts, each containing arrays for one episode.
    """
    episodes_data = []

    for _ in range(n_episodes):
        state, _ = env.reset()
        done = False
        data = {
            "cpu": [], "request_rate": [], "response_time": [],
            "instances": [], "actions": [], "rewards": [],
            "cost": [], "queue_length": [],
        }

        while not done:
            action = agent.select_action(state, training=False)
            next_state, reward, terminated, truncated, info = env.step(action)
            done = terminated or truncated

            data["cpu"].append(float(next_state[0]))
            data["request_rate"].append(float(next_state[2]))
            data["response_time"].append(float(next_state[3]))
            data["instances"].append(float(next_state[4]))
            data["actions"].append(int(action))
            data["rewards"].append(float(reward))
            data["cost"].append(float(next_state[8]))
            data["queue_length"].append(float(next_state[5]))

            state = next_state

        episodes_data.append(data)

    return episodes_data


# ─────────────────────────────────────────────────────────
# PLOTTING FUNCTIONS
# ─────────────────────────────────────────────────────────

def plot_comparison_bar_chart(results: dict, save_path: str):
    """
    Bar chart comparing all methods across key metrics.

    Args:
        results: Dict mapping method names to metric dicts.
        save_path: Path to save the figure.
    """
    methods = list(results.keys())
    metrics_to_plot = [
        ("avg_reward", "Avg Reward"),
        ("avg_sla_violation_rate", "SLA Violation Rate"),
        ("avg_cost", "Avg Cost"),
        ("avg_scaling_events", "Scaling Events"),
    ]

    fig, axes = plt.subplots(1, 4, figsize=(20, 5))
    colors = sns.color_palette("Set2", len(methods))

    for ax, (metric_key, metric_label) in zip(axes, metrics_to_plot):
        values = [results[m].get(metric_key, 0) for m in methods]
        bars = ax.bar(methods, values, color=colors, edgecolor="black", linewidth=0.5)
        ax.set_title(metric_label, fontsize=13, fontweight="bold")
        ax.set_ylabel(metric_label)
        for bar, val in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(),
                    f"{val:.2f}", ha="center", va="bottom", fontsize=9)
        ax.tick_params(axis="x", rotation=30)

    plt.suptitle("Method Comparison — Key Metrics", fontsize=15, fontweight="bold", y=1.02)
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    print(f"  [SAVED] {save_path}")
    plt.close()


def plot_sla_violation_timeline(all_episode_data: dict, save_path: str):
    """
    Timeline plot showing SLA violations for each method over one episode.

    Args:
        all_episode_data: Dict mapping method names to episode data lists.
        save_path: Path to save figure.
    """
    n_methods = len(all_episode_data)
    fig, axes = plt.subplots(n_methods, 1, figsize=(14, 3 * n_methods), sharex=True)
    if n_methods == 1:
        axes = [axes]

    sla_threshold = 500.0

    for ax, (method, ep_data_list) in zip(axes, all_episode_data.items()):
        if not ep_data_list:
            continue
        ep_data = ep_data_list[0]  # Use first episode
        steps = range(len(ep_data["response_time"]))
        rt = ep_data["response_time"]

        ax.plot(steps, rt, color="steelblue", linewidth=0.8, label="Response Time")
        ax.axhline(y=sla_threshold, color="red", linestyle="--", alpha=0.7, label="SLA (500ms)")
        ax.fill_between(steps, sla_threshold, rt,
                        where=[r > sla_threshold for r in rt],
                        color="red", alpha=0.2, label="Violation")
        ax.set_ylabel("RT (ms)")
        ax.set_title(f"{method}", fontsize=11, fontweight="bold")
        ax.legend(loc="upper right", fontsize=8)

    axes[-1].set_xlabel("Time Step (5-min intervals)")
    plt.suptitle("SLA Violation Timeline", fontsize=14, fontweight="bold")
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    print(f"  [SAVED] {save_path}")
    plt.close()


def plot_cost_timeline(all_episode_data: dict, save_path: str):
    """
    Cost over time for each method.
    """
    fig, ax = plt.subplots(figsize=(14, 5))
    colors = sns.color_palette("Set1", len(all_episode_data))

    for (method, ep_data_list), color in zip(all_episode_data.items(), colors):
        if not ep_data_list:
            continue
        ep_data = ep_data_list[0]
        cumulative_cost = np.cumsum(ep_data["cost"])
        ax.plot(cumulative_cost, label=method, color=color, linewidth=1.5)

    ax.set_xlabel("Time Step (5-min intervals)")
    ax.set_ylabel("Cumulative Cost")
    ax.set_title("Infrastructure Cost Over Time", fontsize=14, fontweight="bold")
    ax.legend()
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    print(f"  [SAVED] {save_path}")
    plt.close()


def plot_scaling_decisions(all_episode_data: dict, save_path: str):
    """
    Scaling decisions timeline with instance count for each method.
    """
    n_methods = len(all_episode_data)
    fig, axes = plt.subplots(n_methods, 1, figsize=(14, 3 * n_methods), sharex=True)
    if n_methods == 1:
        axes = [axes]

    action_colors = {0: "gray", 1: "green", 2: "red"}
    action_labels = {0: "Hold", 1: "Scale Out", 2: "Scale In"}

    for ax, (method, ep_data_list) in zip(axes, all_episode_data.items()):
        if not ep_data_list:
            continue
        ep_data = ep_data_list[0]
        steps = range(len(ep_data["instances"]))

        ax.plot(steps, ep_data["instances"], color="steelblue", linewidth=1.2, label="Instances")
        for i, a in enumerate(ep_data["actions"]):
            if a != 0:
                ax.axvline(x=i, color=action_colors[a], alpha=0.3, linewidth=0.6)
        ax.set_ylabel("Instances")
        ax.set_title(f"{method}", fontsize=11, fontweight="bold")

        # Custom legend
        from matplotlib.lines import Line2D
        legend_elements = [
            Line2D([0], [0], color="steelblue", linewidth=2, label="Instances"),
            Line2D([0], [0], color="green", linewidth=2, alpha=0.5, label="Scale Out"),
            Line2D([0], [0], color="red", linewidth=2, alpha=0.5, label="Scale In"),
        ]
        ax.legend(handles=legend_elements, loc="upper right", fontsize=8)

    axes[-1].set_xlabel("Time Step (5-min intervals)")
    plt.suptitle("Scaling Decisions Over Time", fontsize=14, fontweight="bold")
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    print(f"  [SAVED] {save_path}")
    plt.close()


def plot_reward_comparison(all_episode_data: dict, save_path: str):
    """
    Reward per step for all methods (single episode overlay).
    """
    fig, ax = plt.subplots(figsize=(14, 5))
    colors = sns.color_palette("Set1", len(all_episode_data))

    for (method, ep_data_list), color in zip(all_episode_data.items(), colors):
        if not ep_data_list:
            continue
        ep_data = ep_data_list[0]
        cumulative_rewards = np.cumsum(ep_data["rewards"])
        ax.plot(cumulative_rewards, label=method, color=color, linewidth=1.5)

    ax.set_xlabel("Time Step (5-min intervals)")
    ax.set_ylabel("Cumulative Reward")
    ax.set_title("Cumulative Reward Over Episode", fontsize=14, fontweight="bold")
    ax.legend()
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    print(f"  [SAVED] {save_path}")
    plt.close()


# ─────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────

def main(models_dir: str = "models", n_episodes: int = 10, data_path: str = None):
    """
    Run full evaluation and comparison.

    1. Load trained DQN and PPO models (if available)
    2. Run baseline policies (random, threshold, always_scale_out)
    3. Compute metrics for all methods
    4. Generate comparison plots
    5. Print comparison table
    """
    ensure_plots_dir()
    env = ECommerceScalingEnv(data_path=data_path)

    results = {}
    episode_data = {}

    print("\n" + "=" * 60)
    print("  RUNNING FULL EVALUATION & COMPARISON")
    print("=" * 60)

    # ── Baseline Policies (Student 2 comparisons) ──
    print("\n[1/4] Evaluating baseline policies...")
    for policy_name in ["threshold", "random", "always_scale_out"]:
        if policy_name == "threshold":
            label = "Student 2 (Rule-Based Threshold)"
        else:
            label = f"Baseline ({policy_name})"
        print(f"  → {label}...")
        results[label] = compute_baseline_metrics(env, policy=policy_name, n_episodes=n_episodes)
        baseline = BaselinePolicy(policy=policy_name)
        episode_data[label] = collect_episode_data(env, baseline, n_episodes=1)

    # ── DQN Agent ──
    print("\n[2/4] Evaluating DQN agent...")
    dqn_path = os.path.join(models_dir, "best_dqn_model.pt")
    if os.path.exists(dqn_path):
        dqn_agent = DQNAgent(state_dim=10, action_dim=3)
        dqn_agent.load(dqn_path)
        results["DQN Agent"] = compute_metrics(env, dqn_agent, n_episodes=n_episodes)
        episode_data["DQN Agent"] = collect_episode_data(env, dqn_agent, n_episodes=1)
        print(f"  ✓ DQN loaded from {dqn_path}")
    else:
        print(f"  ✗ DQN model not found at {dqn_path} — skipping")

    # ── PPO Agent ──
    print("\n[3/4] Evaluating PPO agent...")
    ppo_path = os.path.join(models_dir, "best_ppo_model.zip")
    if os.path.exists(ppo_path):
        ppo_agent = PPOAgent(env=env)
        ppo_agent.load(ppo_path)
        results["PPO Agent"] = compute_metrics(env, ppo_agent, n_episodes=n_episodes)
        episode_data["PPO Agent"] = collect_episode_data(env, ppo_agent, n_episodes=1)
        print(f"  ✓ PPO loaded from {ppo_path}")
    else:
        print(f"  ✗ PPO model not found at {ppo_path} — skipping")

    # ── Hierarchical RL Agent ──
    hrl_path = os.path.join(models_dir, "hierarchical_agent")
    if os.path.exists(hrl_path):
        try:
            from novelty.hierarchical_rl import HierarchicalRLAgent
            print("\n  Evaluating Hierarchical RL agent...")
            hrl_agent = HierarchicalRLAgent(state_dim=10, action_dim=3)
            hrl_agent.load(hrl_path)
            results["Hierarchical RL"] = compute_metrics(env, hrl_agent, n_episodes=n_episodes)
            episode_data["Hierarchical RL"] = collect_episode_data(env, hrl_agent, n_episodes=1)
            print(f"  ✓ HRL loaded from {hrl_path}")
        except ImportError:
            pass

    # ── Generate Comparison Table ──
    print("\n[4/4] Generating comparison table and plots...")
    comparison_df = create_comparison_table(results)
    print("\n" + "=" * 70)
    print("  COMPARISON TABLE")
    print("=" * 70)
    print(comparison_df.to_string())
    print("=" * 70)

    # Save table to CSV
    table_path = os.path.join(PLOTS_DIR, "comparison_table.csv")
    comparison_df.to_csv(table_path)
    print(f"\n  [SAVED] {table_path}")

    # ── Generate Plots ──
    print("\nGenerating plots...")

    plot_comparison_bar_chart(
        results, os.path.join(PLOTS_DIR, "1_method_comparison.png"))

    plot_sla_violation_timeline(
        episode_data, os.path.join(PLOTS_DIR, "2_sla_violation_timeline.png"))

    plot_cost_timeline(
        episode_data, os.path.join(PLOTS_DIR, "3_cost_over_time.png"))

    plot_scaling_decisions(
        episode_data, os.path.join(PLOTS_DIR, "4_scaling_decisions.png"))

    plot_reward_comparison(
        episode_data, os.path.join(PLOTS_DIR, "5_cumulative_reward.png"))

    print(f"\n✅ All plots saved to {PLOTS_DIR}/")
    print("✅ Evaluation complete!")

    return results, comparison_df


if __name__ == "__main__":
    main()
