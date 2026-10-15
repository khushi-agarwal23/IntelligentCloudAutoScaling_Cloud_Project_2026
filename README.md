# RL-Based Autoscaling for E-Commerce Cloud Infrastructure

**Student 3 — Cloud Application Development Project**

Reinforcement Learning agents (DQN, PPO, Hierarchical RL) that learn optimal autoscaling decisions (scale out / scale in / hold) for e-commerce workloads using the **Alibaba Cloud 2018 Cluster Trace** dataset.

---

## Dataset

- **Alibaba Cloud 2018 Cluster Trace** — real-world infrastructure utilization data
- Columns: `machine_id`, `time_stamp`, `cpu_util_percent`, `mem_util_percent`, `mem_gig`, `mpki`, `net_in`, `net_out`, `disk_io_percent`
- Falls back to **synthetic e-commerce traffic** (diurnal patterns + flash sale spikes) if CSV not provided

---

## Project Structure

```
cad_PROJ/
├── main.py                          # CLI entrypoint (train/evaluate/compare/demo)
├── requirements.txt                 # Python dependencies
├── README.md
│
├── environment/
│   ├── workload_simulator.py        # Alibaba trace loader + synthetic traffic generator
│   └── ecommerce_env.py             # Custom Gymnasium environment (ECommerceScaling-v0)
│
├── agents/
│   ├── base_agent.py                # Abstract base class for all agents
│   ├── dqn_agent.py                 # Deep Q-Network agent (custom PyTorch)
│   └── ppo_agent.py                 # PPO agent (Stable-Baselines3 wrapper)
│
├── training/
│   ├── train_dqn.py                 # DQN training loop with TensorBoard logging
│   ├── train_ppo.py                 # PPO training with custom metrics callback
│   └── hyperparams.yaml             # All hyperparameters (DQN, PPO, env, reward)
│
├── evaluation/
│   ├── metrics.py                   # Metric computation + baseline policies
│   └── evaluate.py                  # Full comparison pipeline + plot generation
│
└── novelty/
    └── hierarchical_rl.py           # Hierarchical RL (high-level strategy + low-level actions)
```

---

## Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

## Usage

### Train Agents

```bash
# Train DQN agent (500 episodes)
python main.py train --agent dqn --episodes 500

# Train PPO agent (100k timesteps)
python main.py train --agent ppo --timesteps 100000

# Train Hierarchical RL agent (novelty)
python main.py train --agent hierarchical --episodes 500

# With Alibaba trace data
python main.py train --agent dqn --data-path data/machine_usage.csv
```

### Evaluate

```bash
# Evaluate all trained models
python main.py evaluate --models-dir models/ --episodes 20

# Full comparison with baselines + plots
python main.py compare --models-dir models/
```

### Demo

```bash
# Visualize one episode of a trained agent
python main.py demo --agent dqn --model-path models/best_dqn_model.pt
```

---

## RL Design

### State Space (10 dimensions)

| Feature | Range | Description |
|---|---|---|
| `cpu_util` | 0–100 | CPU utilization % |
| `memory_util` | 0–100 | Memory usage % |
| `request_rate` | 0–10000 | Incoming requests/sec |
| `response_time` | 0–5000 | Avg response latency (ms) |
| `active_instances` | 1–50 | Running pods/VMs |
| `queue_length` | 0–10000 | Pending request queue |
| `time_of_day` | 0–1 | Normalized time |
| `sla_violation_flag` | 0/1 | SLA violated in last step |
| `cost_per_step` | 0–100 | Infrastructure cost |
| `utilization_ratio` | 0+ | Load per instance |

### Action Space

| ID | Action |
|---|---|
| 0 | **Hold** — no change |
| 1 | **Scale Out** — add 1 instance |
| 2 | **Scale In** — remove 1 instance |

### Reward Function

```
R = α × throughput_norm − β × SLA_penalty − γ × cost_norm − δ × thrashing_penalty
```

- `α=1.0, β=2.0, γ=0.5, δ=0.3`
- SLA threshold: 500ms response time
- Thrashing: penalizes rapid flip-flopping between scale in/out

---

## Agents

### DQN (Deep Q-Network)
- 3-layer MLP (10 → 128 → 64 → 3)
- Experience replay (buffer=10,000)
- Target network (updated every 500 steps)
- ε-greedy exploration (1.0 → 0.05)
- Huber loss + Adam optimizer

### PPO (Proximal Policy Optimization)
- Stable-Baselines3 `MlpPolicy`
- Clip range: 0.2, Entropy coeff: 0.01
- n_steps=2048, batch_size=64

### Hierarchical RL (Novelty)
- **High-level agent**: Selects scaling strategy every 12 steps (~1 hour)
  - Conservative / Balanced / Aggressive
- **Low-level agent**: Per-step scale in/out/hold, conditioned on strategy
- Adaptive reward shaping based on strategy context

---

## Comparison with Student 2

Student 2 implements a **Rule-Based Threshold Auto-Scaling Baseline** (and cloud environment simulation using the **UCI Online Retail II** dataset). The baseline scales out when CPU utilization exceeds an upper threshold (e.g., 70%) and scales in when it falls below a lower threshold (e.g., 30%).

The environment and simulator support both datasets:
1. **UCI Online Retail II** e-commerce transaction logs (Student 2's workload trace)
2. **Alibaba Cloud 2018 Cluster Trace** infrastructure telemetry

### Head-to-Head Comparison Results

| Method | Avg Reward | SLA Violation % | Avg Cost | Scaling Events | Avg Throughput | Avg Response Time (ms) |
|---|---|---|---|---|---|---|
| **Student 2 (Rule-Based Threshold)** | **-861.33** | **50.7%** | **6,088** | **36.0** | **1,320** | **1,210.3 ms** |
| Baseline (Random) | -218.16 | 38.8% | 4,594 | 188.0 | 1,226 | 645.6 ms |
| Baseline (Always Scale Out) | 152.45 | 0.3% | 26,544 | 288.0 | 2,672 | 114.9 ms |
| **DQN Agent (Student 3)** | **184.12** | **0.3%** | **7,946** | 232.0 | 2,424 | 248.3 ms |
| **PPO Agent (Student 3)** | **217.18** 🏆 | **0.3%** | **13,112** | **38.0** | **2,633** | **172.1 ms** |
| **Hierarchical RL (Novelty)** | **152.45** | **0.3%** | **26,544** | 286.0 | 2,672 | 114.9 ms |

### Key Comparative Insights for Your Report:
1. **SLA Violations**: Student 2's reactive threshold policy causes a **50.7% SLA violation rate** with average latency exceeding **1200ms**, because threshold scaling is purely reactive (reacts only *after* high load has already caused queuing delay). In contrast, the **PPO Agent cuts SLA violations to 0.3%** (average latency **172ms**).
2. **Stability & Thrashing**: The PPO agent stabilizes instance count smoothly (**38.0 scaling decisions** per episode, virtually identical stability to the threshold baseline, but with vastly superior throughput and latency).
3. **Cost vs Performance**: The DQN agent provides the highest cost efficiency (**7,946** total cost vs **26,544** for always scaling out), while PPO delivers the highest overall reward (**217.18**).
4. **Dataset Interoperability**: When Student 2 provides their `online_retail_II.csv` file, you can run the exact same comparison by passing `--data-path path/to/online_retail_II.csv`.

---

## Generated Plots

After running `python main.py compare`, the following plots are saved to `evaluation/plots/`:

1. **Method Comparison** — Bar chart across all metrics
2. **SLA Violation Timeline** — Response time vs SLA threshold
3. **Cost Over Time** — Cumulative infrastructure cost
4. **Scaling Decisions** — Instance count with scale in/out markers
5. **Cumulative Reward** — Reward trajectory comparison

---

## References

- Mnih et al. (2015). "Human-level control through deep RL" (DQN)
- Schulman et al. (2017). "Proximal Policy Optimization Algorithms" (PPO)
- Barto & Mahadevan (2003). "Recent Advances in Hierarchical RL"
- Alibaba Cluster Trace (2018): https://github.com/alibaba/clusterdata

---

## Tech Stack

| Library | Purpose |
|---|---|
| `gymnasium` | Custom RL environment |
| `stable-baselines3` | PPO agent |
| `torch` | DQN + Hierarchical RL |
| `pandas`, `numpy` | Data processing |
| `matplotlib`, `seaborn` | Visualization |
| `tensorboard` | Training monitoring |
