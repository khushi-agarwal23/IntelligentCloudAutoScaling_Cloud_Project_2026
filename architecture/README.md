# Architecture

The Intelligent Cloud Auto Scaling system uses a Q-learning based reinforcement learning agent to make scaling decisions based on CPU utilization, request workload, and current instance count.

## Current Flow

Workload (CPU + Requests)
        ↓
FastAPI
        ↓
Trained Q-Learning Agent
        ↓
Scaling Action
        ↓
Mock AWS Auto Scaling Group

## Scaling Actions

- 0 → Scale In
- 1 → Maintain
- 2 → Scale Out

## RL Components

- `rl_environment.py` - Auto-scaling environment, states, actions and rewards
- `q_learning_agent.py` - Q-learning algorithm
- `train_rl.py` - Agent training
- `evaluate_rl.py` - Testing trained decisions
- `models/q_table.pkl` - Saved trained Q-table
- `main.py` - FastAPI endpoint
- `mock_aws.py` - Mock AWS Auto Scaling implementation

## Tested Behavior

- High workload → Scale Out
- Normal workload → Maintain
- Low workload → Scale In

The current implementation uses mock AWS Auto Scaling for demonstration. Real AWS Auto Scaling integration can be added later.
