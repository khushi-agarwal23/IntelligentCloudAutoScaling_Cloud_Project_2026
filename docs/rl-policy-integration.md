# Teammate RL policy integration status

The existing implementations from `mybnranch` are present on this feature branch
without rewriting their agent code: PPO, DQN, HRL, the Gymnasium workload
environment, training scripts, evaluation scripts, comparison CSV/plots, and
their checkpoints. The Q-learning policy already used by the backend remains the
default. No model is silently substituted when loading or predicting fails.

## PPO contract verified from source and checkpoint

`models/best_ppo_model.zip` loads with Stable-Baselines3 2.9.0. Its spaces are a
10-float observation and `Discrete(3)`. The source observation order is:

1. CPU utilization percent
2. Memory utilization percent
3. Request rate (requests/second)
4. Response time (milliseconds)
5. Active instance count
6. Queue length
7. Time of day / normalized episode progress
8. SLA violation flag
9. Cost per step
10. Utilization ratio

Action IDs are exactly `0=hold`, `1=scale out by one`, and `2=scale in by one`.
The inference adapter in `src/backend/app/services/ppo_policy.py` keeps this
order and mapping. It derives queue/cost/utilization using the training config's
100 requests/second per instance and 2 cost units per instance. Missing memory
telemetry is rejected. The inference adapter uses UTC wall-clock fraction for
the time feature because live data does not have the simulator's episode-relative
step; this is an approximation, not an equivalence.

## Policy selection and safety

- Default: `SCALING_POLICY=q_learning` (existing backend behavior).
- To evaluate PPO in simulation/manual inference only: set
  `SCALING_POLICY=ppo_candidate`. The checkpoint defaults to
  `models/best_ppo_model.zip`; override with `PPO_MODEL_PATH` if needed.
- PPO load/prediction failure returns a service error; there is no Q/heuristic
  fallback under this explicit selection.
- Live AWS scaling refuses any configured policy other than `q_learning`.
  Existing live-write gates remain independently disabled by default. This PPO
  checkpoint has not been approved for real scaling.

## Why PPO is not the live primary yet

The repository's PPO training YAML says `max_instances=20`, but the checkpoint's
observation-space upper bound for active instances is 50. The exact environment
settings used to produce this checkpoint cannot be established from those
conflicting artifacts. Sample deterministic predictions for low, normal, and
high telemetry all returned action 1 (scale out). This is compatible at the
tensor/action-space level but insufficient evidence of a safe/effective policy.
The saved offline comparisons are simulated evaluation only and are not
evidence of AWS behavior. PPO stays an explicit candidate until a representative
offline comparison validates behavior under the 1–3 instance constraints,
feature units, workload distribution, and hold/scale-in cases.

## Reproduce checks

From `src/backend`, install dependencies and run tests:

```powershell
python -m pip install -r requirements.txt
python -m pytest -q
```

From the repository root, compare the existing Q table, PPO, DQN, novelty HRL,
and threshold baseline on the same deterministic 288-step simulated workload:

```powershell
py -3.12 evaluation/compare_existing_agents.py
```

The command prints metrics to stdout and does not overwrite saved tables or
plots. The workload is the environment's synthetic e-commerce simulator, not
the Alibaba trace and not production telemetry.

## Same-seed local smoke comparison

Run on 2026-10-19: seed 42, one 288-step synthetic episode per policy, capacity
1–3, 100 req/s per instance, 200 ms SLA, and the reward weights mapped by the
training factory (`alpha=1.0`, `beta=0.5`, `gamma=0.5`, `delta=0.1`). The
training YAML's `gamma_cost` key is not an environment constructor parameter,
so the factory does not pass it; `gamma` stays at the environment default 0.5.
These are small smoke metrics, not statistically reliable benchmarks or proof
that one agent is superior.

| Policy | Avg reward | SLA violation | Avg cost | Scaling events | Avg throughput | Avg response time |
|---|---:|---:|---:|---:|---:|---:|
| Q table + existing heuristic fallback | -1242.08 | 91.67% | 1728 | 1 | 285.17 req/s | 1830.89 ms |
| PPO checkpoint | -1242.08 | 91.67% | 1728 | 1 | 285.17 req/s | 1830.89 ms |
| DQN checkpoint | -1632.79 | 98.96% | 1318 | 11 | 226.74 req/s | 2396.26 ms |
| HRL checkpoint (`novelty` implementation) | -1242.87 | 93.06% | 1708 | 19 | 284.90 req/s | 1832.71 ms |
| Threshold baseline | -2071.66 | 100.00% | 898 | 5 | 155.90 req/s | 3031.68 ms |

Q and PPO produced identical aggregate metrics in this one episode, which is
consistent with both taking the same decisions on these observations. It does
not establish that their policies are equivalent. All policies saw the same
seeded synthetic trace; the Q row uses the backend's existing heuristic only
when its local table has no entry. Alibaba 2018 experiments remain separate and
are documented in [data/README.md](../data/README.md).

To request candidate simulation decisions, set `SCALING_POLICY=ppo_candidate`
for that process and ensure the checkpoint is present. The training entry
points now first import the checked-in `environment.*` package and retain their
historical import fallback. Local tests verify environment construction, not
model retraining or equivalence with the checkpoint's unknown training setup.

## Verified in this integration

- Checkpoint load and `10` observation / `Discrete(3)` action-space validation.
- Deterministic predictions on sample states; each returned action ID 1.
- Unit coverage for feature order and derivations, all three action mappings,
  invalid telemetry, missing checkpoints and no implicit fallback.
- Backend test suite: see [project readiness](project-readiness.md) for the
  current full-suite command and result.
- No real AWS scaling mutation was run. The PPO candidate has not been used for
  live telemetry or live scaling.

## Alibaba held-out PPO replay

Run from the repository root to compare the existing PPO checkpoint against
the in-memory Alibaba Q learner, a threshold baseline tuned on the chronological
training/validation partitions, and persistence:

```powershell
py -3.12 evaluation/compare_ppo_alibaba.py
py -3.12 -m pytest -p no:cacheprovider src/backend/tests/test_ppo_alibaba_evaluation.py -q
```

The command writes new detail and summary files under
`evaluation/results/alibaba2018_ppo_holdout*.csv`; it does not overwrite the
PPO checkpoint, the backend Q table, or the prior Alibaba objective results.
Training of the separate Alibaba Q learner and threshold tuning use only the
training and validation intervals. Every policy is then evaluated on the same
held-out timestamps and the same existing relative objective. PPO inference is
deterministic, and this evaluation does not retrain PPO.

The processed Alibaba file contains timestamp, mean CPU, mean memory, and
machine-count summary; it does not contain request rate or application latency.
The evaluator preserves timestamp/CPU/memory as observed trace values. It
derives only PPO-required request rate and latency through the already existing
`WorkloadSimulator` assumptions: when network input is absent, request rate is
`100 + CPU_fraction * (8000 - 100)` requests/second; latency is
`50 + request_rate / (instances * 100) * 200 ms`, capped at 5000 ms. Episode
progress wraps every 288 samples to match the training environment. These
derived fields are explicitly emitted as estimates. They are not Alibaba
measurements, production demand, measured latency, or AWS outcomes.

The shared objective still scores observed CPU/memory boundary exceedance,
simulated capacity cost, infeasible actions, and capacity changes. Since the
trace contains no post-scaling counterfactual, utilization violations remain
exogenous and cannot show that PPO prevented an SLA breach. Results support
only reproducible policy behavior under this stated replay model. The known
checkpoint/YAML maximum-instance discrepancy remains unresolved, and PPO
remains blocked from live AWS scaling.

### Recorded Alibaba PPO replay (2026-10-20)

The default command completed on the verified processed Alibaba trace: seed 42,
7,962 held-out samples per policy, capacity bounds 1–3, with threshold tuning
and CPU/memory p95 limits derived without using the test interval. The outputs
are `evaluation/results/alibaba2018_ppo_holdout.csv` and
`evaluation/results/alibaba2018_ppo_holdout_summary.csv`.

| Policy | Proxy reward | Capacity instance-samples | Observed utilization-boundary violations | Requested down / hold / up | Feasible changes | Infeasible requests |
|---|---:|---:|---:|---:|---:|---:|
| PPO checkpoint | -99,161.25 | 23,886 | 3,547 | 0 / 0 / 7,962 | 1 | 7,961 |
| Alibaba Q-learning | -51,724.50 | 15,020 | 3,547 | 2,469 / 3,024 / 2,469 | 4,938 | 0 |
| Validation-tuned threshold | -82,013.25 | 23,155 | 3,547 | 98 / 3,272 / 4,592 | 13 | 4,677 |
| Persistence | -51,394.00 | 15,924 | 3,547 | 0 / 7,962 / 0 | 0 | 0 |

On this replay the PPO checkpoint requested scale-up at every held-out sample;
after the one feasible increase to three instances, the remaining 7,961
requests were infeasible. Its proxy reward was worse than all three references.
The violation count is identical because it measures fixed observed trace CPU
and memory, not policy-controlled service outcomes. This is evidence that the
checkpoint is not suitable for promotion to the current 1–3 capacity controller
under this replay contract. It is not evidence of AWS behavior or causal
service-level improvement. The CSVs contain the derived request-rate and
latency estimates separately from observed Alibaba fields.

## Separate Alibaba PPO training attempt (2026-10-21)

The original `models/best_ppo_model.zip` could not be tied to a recoverable
historical training config. Source YAML currently constructs max capacity 20,
while the checkpoint stores observation high=50. Its feature/action shapes do
match the adapter (10 float features, `Discrete(3)`), but deterministic
predictions for representative low, normal, and high inputs all returned
scale-up. There is no `VecNormalize` state; the old checkpoint uses raw units.
The exact reason it collapsed to scale-up is not recoverable from the saved ZIP
alone. Its configuration and checkpoint were left unchanged.

The new, separate trainer is reproducible with:

```powershell
py -3.12 training/train_alibaba2018_ppo.py
py -3.12 evaluation/compare_retrained_ppo_alibaba.py
py -3.12 -m pytest -p no:cacheprovider src/backend/tests/test_alibaba_ppo_v2.py src/backend/tests/test_ppo_alibaba_evaluation.py src/backend/tests/test_ppo_policy.py src/backend/tests/test_rl_agents.py -q
```

It reuses the existing PPOAgent wrapper and chronological Alibaba split, trains
only on 37,157 training rows, chooses a checkpoint with three fixed 288-sample
validation windows, and leaves 7,962 test samples untouched until the final
comparison. It writes a separate checkpoint and manifest at
`models/alibaba2018_ppo_normalized_best.zip` and
`models/alibaba2018_ppo_normalized_best.json`; it did not overwrite the
teammate PPO files or the earlier first-pass candidate. The new checkpoint
uses fixed per-feature scaling to [0,1] (no data-fitted normalizer), which the
backend PPO adapter detects from its stored observation space. The offline
evaluation uses that same adapter and scaling.

The normalized run completed 100,000 timesteps, but validation mean return was
exactly -3,456 at every 10,000-step checkpoint. On the held-out test interval,
the retrained PPO requested hold all 7,962 samples and exactly matched
persistence: reward -95,544, capacity cost 15,924 instance-samples, and zero
feasible changes. It did not improve on the re-trained Q baseline's proxy
reward -87,582.25; Q requested one feasible scale-down, then held at one
instance. The validation-tuned threshold scored -126,163.25 and made 4,677
infeasible requests. No policy reduced modeled latency-SLA violations: all
policies had 7,962/7,962 (100%) under the test assumptions. Mean estimated
latency after policy actions was 3,541.43 ms for PPO/persistence, 4,986.17 ms
for Q, and 2,519.66 ms for threshold; these remain simulator values.

Two counts are invariant for different reasons. The CPU/memory p95 boundary
count is exogenous by definition and remains 3,547 for every policy. The
modeled latency violation count is also 100% for every policy because the
existing CPU-to-request-rate mapping implies demand above what 1–3 instances
at 100 requests/second each can serve for every test sample. Thus the latency
proxy cannot discriminate service performance here. Do not treat these metrics
as measured AWS results or use this PPO checkpoint for live scaling. The result
is a negative/inconclusive offline experiment, not evidence of improvement.

The detailed normalized comparison file also records each row's before/after
capacity and estimated latency, so capacity trajectories can be reconstructed.
Held-out capacity occupancy (steps after action at 1 / 2 / 3 instances) was
PPO `0 / 7,962 / 0`, Q `7,962 / 0 / 0`, threshold `343 / 45 / 7,574`, and
persistence `0 / 7,962 / 0`. The common observed trace CPU/memory summary was
CPU mean/p95 `43.09% / 57.14%`, memory mean/p95 `90.65% / 93.77%`.

The first unnormalized Alibaba PPO candidate is retained separately at
`models/alibaba2018_ppo_best.zip` for auditability; it also had flat validation
return (-3,456) and matched persistence on the held-out objective. The
normalized candidate is the final training attempt, but neither candidate
beats the baselines. The action tests verify that the implementation supports
hold, scale-up, scale-down, and boundary handling; they do not force action
frequencies or establish policy quality.
