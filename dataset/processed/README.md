This folder will contain processed data.
# Dataset

This directory contains the workload data used for the Intelligent Cloud Auto Scaling project.

## Input Features

The workload data includes:

- CPU Utilization
- Request Count
- Instance Count

These values are used to create the state for the Q-learning agent and evaluate scaling decisions.

## Processed Data

The `processed/` directory is reserved for processed or transformed workload data used during experiments and analysis.

## Current Implementation

The current RL training environment generates simulated CPU utilization and request workloads for training and evaluation. The trained Q-table is stored separately in the `models/` directory.
