# Workload analysis and project review evidence

## Status

| Responsibility | Status | Evidence / remaining work |
|---|---|---|
| Analyze workload patterns and identify peaks | COMPLETE | Selected continuous Alibaba 2018 segment is 53,082 ten-second observations. The saved plot and threshold analysis identify relative high-utilization periods. |
| Train/evaluate forecasting model | COMPLETE | Reproducible chronological train/validation/test results saved under `data/alibaba2018/processed/*triple_split.csv`. Persistence remains the practical baseline. |
| Use Alibaba, with no second dataset | COMPLETE | Uses the existing Alibaba Cluster Trace v2018 machine usage data only for this analysis. It is a datacenter workload proxy, not sales or transaction data. |
| Connect results to the existing scaling project | COMPLETE | Forecast/threshold evidence is offline; the frontend and backend policy integration is evaluated separately. No Alibaba result is represented as live AWS performance. |
| Frontend/backend scenario integration | COMPLETE | All five UI buttons were run against the local FastAPI service; request metrics, policy responses, projected/current/desired capacity, decision history, mock bypass status, and browser console were checked. |
| Final review evidence capture | INCOMPLETE | Functional checks are complete. Capture the screenshots listed below for the presentation; live AWS screenshots remain blocked by credentials. |
| Real AWS authenticated integration | BLOCKED | Code and safe configuration path are implemented. Read-only preflight returned `NoCredentialsError`; no AWS identity, group capacity, health, or IAM permissions could be verified. No live tests were attempted. |

## Dataset and preprocessing

The analysis uses Alibaba's official [Cluster Trace v2018 description](https://github.com/alibaba/clusterdata/blob/master/cluster-trace-v2018/trace_2018.md) and [machine usage schema](https://github.com/alibaba/clusterdata/blob/master/cluster-trace-v2018/schema.txt). The upstream trace covers roughly 4,000 machines over eight days and contains both online services and batch workloads. `machine_usage.csv` provides machine ID, timestamp in seconds, CPU utilization percent, memory utilization percent, memory bandwidth, cache-miss rate, normalized network in/out, and disk I/O. This project uses timestamp, CPU, and memory; it averages machine utilization across records at each timestamp.

The prepared file has 67,242 aggregate timestamps. The timestamp differences include two irregularities (one 20-second interval and one 18,780-second gap). The evaluation deliberately selects the larger continuous segment from timestamp 160,380 through 691,190: 53,082 observations at regular 10-second intervals (about 147.45 hours). This avoids forming lag/target pairs across the gap. After lag/target creation, the model comparison has 53,076 usable rows and uses the chronological split below.

Utilization values are cluster-wide means across machines at a timestamp. They are not request rates, transaction counts, response times, or the load of one EC2 instance. The trace is a workload proxy and does not contain e-commerce festival-sale labels.

## Workload pattern and high-utilization periods

In the selected segment, CPU mean is 38.57% (standard deviation 9.94 percentage points), p95 55.89%, and maximum 79.85%. Memory mean is 88.65% (standard deviation 2.25 points), p95 92.20%, and maximum 95.38%. The CPU maximum occurs at trace-relative timestamp 626,000 seconds; the memory maximum occurs at 666,160 seconds. These are trace-relative seconds, not wall-clock dates.

Training-only p95 thresholds for the original 60% training period are 56.43% CPU and 91.38% memory. Across the selected segment, 7,273 observations (13.70%) exceed either threshold. The longest consecutive run above either threshold is 520 observations (about 86.7 minutes), from timestamp 675,220 to 680,410. Other long runs occur at 668,150–672,830 (about 78.2 minutes) and 672,890–675,170 (about 38.2 minutes). These are relative statistical flags, not validated production capacity limits.

Plot: `results/alibaba2018_workload_overview.png`, reproducible with `py -3.12 scripts/plot_alibaba2018_workload.py`.

### Reproducible peak episode identification

The dataset-wide peak scan uses the verified local `data/alibaba2018/processed/machine_timeseries.csv`, produced by `scripts/preprocess_alibaba2018.py` from the Alibaba 2018 `machine_usage.csv` schema (`timestamp`, `cpu_util_percent`, and `mem_util_percent`, aggregated to `cpu_mean` and `memory_mean`). The source archive and extracted raw CSV are present at the documented ignored paths. The scan reads the processed aggregate directly and does not create synthetic workload rows. Its timestamps remain trace-relative seconds, not wall-clock dates.

The reproducible default method computes separate full-series p95 thresholds and identifies each maximal consecutive run at or above the threshold. Any non-median-cadence timestamp gap splits runs. Event duration is sample count times the 10-second median cadence; each CSV row reports start/end, peak timestamp/intensity, mean intensity, threshold/method, duration and sample count. This is a descriptive full-series scan; do not use its full-series threshold to claim held-out policy performance. Outputs are `data/alibaba2018/processed/peak_events.csv` and `results/alibaba2018_detected_peaks.png`.

On the current 67,242-row processed input (timestamps 0–691,190 seconds), p95 is 55.5225% CPU and 91.9324% memory. The scan found 443 CPU and 231 memory peak episodes. The strongest CPU sample is 79.8485% at trace timestamp 626,000 seconds; the strongest memory sample is 95.3831% at 666,160 seconds. Longest episodes are 1,310 seconds for CPU (540,370–541,670) and 2,320 seconds for memory (670,490–672,800). These are cluster-wide utilization patterns, not e-commerce demand, AWS telemetry, or capacity requirements.

Run from the repository root with the project Python environment:

```powershell
py -3.12 scripts/analyze_alibaba2018_peaks.py
py -3.12 -m pytest -p no:cacheprovider src/backend/tests/test_alibaba2018_peaks.py -q
```

To relate peaks to the existing Alibaba-trained Q-learning policy, match each event’s trace-relative start/end timestamps to the rows in `data/alibaba2018/processed/alibaba2018_rl_evaluation.csv`, then compare the policy’s `action`, `instances_before/after`, and proxy reward with the threshold and persistence actions over the same peak windows. For an honest held-out result, only count events overlapping the Q-learning test segment and report them separately from whole-test metrics. That evaluation remains an offline simulation with assumed rewards and capacity bounds; it says nothing about live AWS scaling. The application’s regular Q-table is a separate model and must not be described as Alibaba-trained.

### Peak-window Q-learning comparison

The existing `alibaba2018_rl_evaluation.csv` records the Q-learning, threshold, and persistence policies on the same 7,962 held-out trace timestamps from 611,570 through 691,180 seconds at 10-second cadence. These are trace-relative seconds, matching the `timestamp` and peak-event timestamps; they are not UTC times. The comparison script additionally joins every saved policy observation to `machine_timeseries.csv` and verifies both CPU and memory values before using it. All 7,962 Q-learning rows aligned successfully. Of those, 2,760 timestamps (34.67%) overlap at least one detected full-series p95 event; 509 overlap CPU events and 2,513 overlap memory events (262 timestamps overlap both).

Reproduce the comparison after regenerating the peak events and Q-learning evaluation CSV:

```powershell
py -3.12 scripts/analyze_alibaba2018_peaks.py
py -3.12 scripts/train_alibaba2018_rl.py
py -3.12 scripts/compare_alibaba2018_peaks_to_policy.py
py -3.12 -m pytest -p no:cacheprovider src/backend/tests/test_alibaba2018_peak_policy.py -q
```

The comparison is saved at `data/alibaba2018/processed/peak_policy_comparison.csv`. Action counts below are ordered scale-up / hold / scale-down; capacity changes are ordered increase / unchanged / decrease.

| Policy | Peak N | Peak actions | Peak capacity changes | Peak mean reward | Non-peak N | Non-peak actions | Non-peak capacity changes | Non-peak mean reward |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Q-learning | 2,760 | 2,760 / 0 / 0 | 0 / 2,760 / 0 | 2.0000 | 5,202 | 3,278 / 1,815 / 109 | 7 / 5,189 / 6 | 1.9994 |
| Threshold | 2,760 | 2,760 / 0 / 0 | 0 / 2,760 / 0 | 2.0000 | 5,202 | 3,278 / 1,815 / 109 | 7 / 5,189 / 6 | 1.9994 |
| Persistence | 2,760 | 0 / 2,760 / 0 | 0 / 2,760 / 0 | -1.0000 | 5,202 | 0 / 5,202 / 0 | 0 / 5,202 / 0 | 0.0886 |

Thus, during every detected peak sample, Q-learning and the threshold policy chose scale-up, but the capacity count increased zero times: both were already at the simulated maximum of 3 instances. Q-learning averaged 3 instances before and after peak actions, compared with 2.873 before and after non-peak actions. During non-peak samples it chose scale-up 3,278 times (63.01%), hold 1,815 times (34.89%), and scale-down 109 times (2.10%); capacity increased 7 times, stayed unchanged 5,189 times, and decreased 6 times. This separates scale-up action intent from an actual capacity change at the simulator’s upper bound.

Across the entire 7,962-row held-out segment, the saved Q-learning and threshold action sequences match at every timestamp. The comparison CSV reports per-window action matches against Q-learning so this agreement is reproducible; persistence matches only at held-out rows where Q-learning also holds.

Mean proxy reward was 2.0000 during peak samples and 1.9994 outside them. These are values from the experiment’s assumption-based reward function, not measured cloud cost, service performance, or an independent quality metric. The observed policy frequently requests scale-up during detected peaks but is already at its maximum in every such row; this comparison does not demonstrate that more capacity would improve outcomes. It also does not test live AWS or the application’s separately configured Q-table. Peak windows use thresholds computed on the full series for descriptive pattern identification, so peak/non-peak labels here are not a held-out threshold-selection experiment.

## Forecast method and results

The one-step horizon is 10 seconds. Persistence predicts the next observation using the most recently observed CPU/memory value. Random Forest uses lag features 1, 2, 3, and 6 for both signals, with 100 trees, max depth 12, minimum leaf size 5, and random seed 42. Evaluation rows are chronologically divided 60% train, 20% validation, and 20% test. Fixed Random Forest settings are evaluated on validation; the final model is refit on train plus validation and evaluated once on the untouched final test segment. MAE and RMSE are in percentage points.

| Target | Validation RF MAE | Validation persistence MAE | Held-out RF MAE / RMSE | Held-out persistence MAE / RMSE | RF test MAE change |
|---|---:|---:|---:|---:|---:|
| CPU | 1.4426 | 1.4594 | 1.3909 / 1.8546 | 1.3929 / 1.8584 | 0.14% lower |
| Memory | 0.1471 | 0.1426 | 0.1513 / 0.2141 | 0.1495 / 0.2051 | 1.21% higher |

The Random Forest's CPU gain is very small and it loses on memory. Keep persistence as the baseline; the current evidence does not justify claiming that Random Forest materially improves forecasting. The older `forecast_model_comparison.csv` and `forecast_baseline_results.csv` are preserved earlier 80/20 outputs; use the new `*_triple_split.csv` files for the three-way evaluation.

Reproduction commands from the repository root:

```powershell
py -3.12 scripts/evaluate_forecast_baseline.py
py -3.12 scripts/evaluate_ml_forecast.py
```

## Threshold policy and offline scaling evidence

The threshold sweep computes CPU and memory percentile thresholds from training observations only. A one-step scale-up alert is predicted when the current CPU **or** memory is at/above its threshold. A high-utilization label is true when the next observation's CPU **or** memory crosses that same training-derived threshold. Threshold percentile selection is based on validation F1; test results are reported afterward and do not select the threshold.

The validation-selected candidate is the 75th percentile: CPU 44.9461%, memory 89.7344%, validation F1 90.89%. On the untouched test segment, the rule triggers at 61.77% of observations; precision is 96.28%, recall 96.25%, and F1 96.26% (6,313 true positives, 244 false positives, 246 false negatives, 3,812 true negatives). The high trigger rate is a tradeoff, not evidence that this threshold minimizes cost or avoids unnecessary instances. Threshold 95% triggers less often (33.25%) but has lower test precision/recall (93.57% / 93.52%).

The separate existing Alibaba-trained Q-learning experiment records the same held-out actions for its Q-learning and threshold policies: 7,962 observations each, with 6,038 scale-up, 1,815 maintain, and 109 scale-down actions. This is an offline policy simulation using its own proxy reward and assumptions. It is not evidence that Q-learning is superior.

The revised forecast-driven scaling evaluation uses the same 60/20/20 chronological split and a multi-output Random Forest. On the held-out test data, persistence has CPU MAE/RMSE 1.9344/2.6135 and memory 0.2562/0.3521; Random Forest has CPU 1.9409/2.6197 and memory 0.4453/0.6702. With training-derived upper quartile triggers (CPU 44.946%, memory 89.734%), persistence selects scale-up/maintain/scale-down 6,557/3,239/819 times; Random Forest selects 6,539/3,323/753 times. CPU and memory exceedance detection are reported separately in the script output. These offline action counts do not establish capacity or cost benefit. Neither artifact measures actual AWS cost, latency, instance health, or production capacity.

Reproduce the threshold sensitivity output with:

```powershell
py -3.12 scripts/analyze_alibaba2018_thresholds.py
```

The existing Alibaba-trained experimental policy is separate from the root `models/q_table.pkl` used by the frontend backend. Do not claim the frontend Q-table was trained on Alibaba data.

## Frontend/backend integration and test evidence

All five workload scenario buttons call `evaluateTrafficSimulation()`. That handler sends `cpu_percent`, `memory_percent = min(cpu + 5, 95)`, `request_rate`, `response_time_ms`, `current_instances=2`, and `apply_to_aws=false`. The manual evaluation handler also sends false. `src/backend/scripts/simulate_traffic.py` now sends false. The request schema defaults to false. Only explicit API callers can request mock mutation; live writes additionally require both backend environment gates and an individual request opt-in.

Full backend suite: `py -3.12 -m pytest -p no:cacheprovider tests/ -q` from `src/backend`; 29 tests passed in 11.36 seconds. Coverage includes all five UI workload scenarios, simulation-only behavior, history logging, mock bounds, mock/live preflight behavior, missing AWS clients, and rejection of live writes without both environment gates. These are mock/unit tests, not authenticated AWS evidence.

The local application was served at `http://127.0.0.1:5501/src/frontend/index.html`; the frontend returned HTTP 200 and `GET http://127.0.0.1:8000/api/v1/health` returned HTTP 200. After each actual UI-button click, the visible request metrics, decision, current count, desired count, projected count, bypass message, and refreshed history were checked. Results were:

| Scenario | CPU / memory | Requests/s / latency | Current → desired | Backend decision |
|---|---:|---:|---:|---|
| Low | 25% / 30% | 30 / 110 ms | 2 → 1 | `scale_down` |
| Normal | 45% / 50% | 60 / 150 ms | 2 → 2 | `maintain` |
| Medium | 65% / 70% | 100 / 210 ms | 2 → 3 | `scale_up` |
| High | 82% / 87% | 150 / 310 ms | 2 → 3 | `scale_up` |
| Festival Peak | 94% / 95% | 240 / 520 ms | 2 → 3 | `scale_up` |

Every result showed `AWS ASG execution bypassed (apply_to_aws=False)`, and each decision appeared at the top of history. The read-only preflight endpoint reported `mode=mock`, `ready=true`; it did not authenticate or call a live AWS account. The browser console contained only expected dashboard-update log entries and no warnings or errors. The main card was corrected to say **Projected EC2 Instances**, since its count represents the policy target while the separate live-control panel shows current and desired counts. A focused Node VM concurrency check passed for both an older failed request arriving after a newer success and an older successful response arriving late: stale responses no longer invoke fallback or overwrite the latest UI state.

The Windows startup commands verified for this project are in the PowerShell demo section below. The backend entry point is `src/backend/run.py`; the frontend is static and is served from the repository root with Python's HTTP server.

## AWS integration status

Read [the AWS integration guide](../src/backend/AWS_INTEGRATION_GUIDE.md) for modes, IAM, the read-only endpoint, approval gates, staged live procedure, rollback, and AWS screenshots. A local read-only SDK preflight was attempted in `ap-south-1` against `rl-autoscaling-group`; it returned `NoCredentialsError`. Identity, group, launch template, bounds, instance health, and permissions therefore remain unverified. Live scaling is not complete under the project acceptance criteria. No AWS write was attempted, and a live scale-out/scale-in must each be explicitly approved before execution.

## Limitations and next work

- Alibaba infrastructure utilization is a proxy, not e-commerce sales demand.
- Averaging machine metrics hides per-machine peaks and the changing population of machines.
- The 10-second trace and 10-second forecast horizon may not match the frontend's request-rate/latency features.
- CPU and memory percentile thresholds are data-dependent and do not encode cost, startup delay, SLA, or minimum healthy capacity.
- The Q-table's proxy reward and experiment dynamics are not an AWS simulator and do not prove RL superiority.
- Live AWS validation remains blocked until valid temporary/profile/role credentials are available, read access succeeds, the write policy is confirmed by an AWS administrator, and the user explicitly approves each live action.

## Revised Alibaba Q-learning objective experiment

The earlier `alibaba2018_rl_evaluation.csv` and `peak_policy_comparison.csv` are preserved historical artifacts. The revised experiment is separate and writes `alibaba2018_objective_evaluation.csv`, `alibaba2018_objective_summary.csv`, and `models/alibaba2018_q_table_objective_v2.pkl`; it does not overwrite the historical outputs, `models/alibaba2018_q_table.pkl`, or the frontend/backend application Q table.

Run from the repository root with the project Python environment:

```powershell
py -3.12 scripts/evaluate_alibaba2018_objective.py
py -3.12 -m pytest -p no:cacheprovider src/backend/tests/test_alibaba2018_objective_eval.py -q
```

The script reuses the existing chronological Alibaba split: the Q learner is trained on training data, threshold candidates are formed only from training CPU/memory quantiles, and the threshold candidate minimizing the validation objective is selected before either policy is evaluated on the same untouched test interval. Evaluation tie-breaking is deterministic. The local random generator uses seed 42 for training. The held-out comparison also includes persistence as a reference.

The objective is intentionally labeled as an offline proxy, with relative cost units per 10-second trace sample:

- A utilization-constraint violation is an observed sample at/above CPU or memory p95 computed on the training segment. This is a statistical utilization boundary, **not a measured service-level objective or a known production SLA**.
- Capacity cost is one normalized unit per simulated instance per sample (`instances_after`); it is not an AWS price estimate.
- An infeasible scale request at min/max incurs five units. It does not change capacity and is reported separately from a feasible capacity change.
- A feasible capacity change incurs 0.25 units. The reward is the negative sum of these costs, including ten units for an observed utilization-boundary violation.

Each CSV row reports requested action, resulting simulated capacity, feasible capacity change, infeasible request, observed utilization-boundary violation, each cost component, total objective cost, and reward. Summary output separately totals reward/cost, capacity instance-samples, violations, requested action counts, feasible changes, and infeasible actions.

Critical limitation: the Alibaba trace has no post-scaling counterfactuals, service latency, application demand, or causal relationship between changing the simulated instance count and subsequent cluster CPU/memory. The replay therefore keeps observed trace values fixed after actions. The violation count is the same exogenous workload trace observed by each policy; it cannot establish that Q-learning or threshold scaling reduces violations. The comparison can establish reproducible policy behavior and simulated capacity occupancy under the stated bounds/objective only. It cannot demonstrate production SLA attainment, financial savings, scale effectiveness, or AWS performance. Do not describe this as an AWS result or as an outcome-validated RL advantage.

### Current objective-run results

The reproducible run on the current processed Alibaba trace selected training-only p95 proxy limits of CPU 55.6684% and memory 91.3679%. The validation-selected threshold rule used CPU low/high 29.3952/51.6174 and memory low/high 86.9513/90.8177. All policies were evaluated on the same 7,962 held-out samples, with initial capacity 2 and bounds 1–3.

| Policy | Total proxy reward | Capacity cost (instance-samples) | Observed utilization-boundary violations | Requested down / hold / up | Feasible down / up changes | Infeasible requests | Ending instances |
|---|---:|---:|---:|---:|---:|---:|---:|
| Q-learning | -51,724.50 | 15,020 | 3,547 | 2,469 / 3,024 / 2,469 | 2,469 / 2,469 | 0 | 2 |
| Threshold | -82,013.25 | 23,155 | 3,547 | 98 / 3,272 / 4,592 | 6 / 7 | 4,677 | 3 |
| Persistence | -51,394.00 | 15,924 | 3,547 | 0 / 7,962 / 0 | 0 / 0 | 0 | 2 |

The identical violation count is expected: violations come from the fixed observed trace, not from an estimated response to capacity. Under this accounting objective, Q-learning has 904 fewer capacity instance-samples than persistence, but its total proxy cost is 330.50 higher because its 4,938 feasible transitions incur transition cost. It has 30,288.75 lower cost than the validation-tuned threshold policy, largely because that policy repeatedly requests scale-up at the upper bound and incurs infeasible-action penalties. These are comparisons of this implementation and proxy objective, not evidence that Q-learning serves users better or saves real money. They also do not demonstrate the threshold policy is generally inferior: its rule family/grid and this objective define the comparison.

The Q learner's requested scale-down/up actions each produced 2,469 feasible changes; it requested no infeasible action in this run. The threshold requested 4,592 scale-ups but only seven feasible increases, and made 4,677 infeasible requests in total. The detail CSV separates requests, changes, and costs so this behavior can be inspected per timestamp.

## Existing PPO checkpoint on the Alibaba held-out interval

The saved PPO checkpoint was evaluated separately using the same chronological
Alibaba test interval and proxy objective as the Alibaba Q-learning experiment.
Reproduce it from the repository root with:

```powershell
py -3.12 evaluation/compare_ppo_alibaba.py
py -3.12 -m pytest -p no:cacheprovider src/backend/tests/test_ppo_alibaba_evaluation.py -q
```

The run used seed 42, 7,962 held-out samples per policy, bounds 1–3, CPU p95
55.6684% and memory p95 91.3679% derived from training only, and a threshold
selected on validation only. It created
`evaluation/results/alibaba2018_ppo_holdout.csv` and
`evaluation/results/alibaba2018_ppo_holdout_summary.csv`. PPO inference was
deterministic; the PPO checkpoint was not retrained.

| Policy | Proxy reward | Capacity instance-samples | Observed boundary violations | Requested down / hold / up | Feasible changes | Infeasible actions |
|---|---:|---:|---:|---:|---:|---:|
| PPO checkpoint | -99,161.25 | 23,886 | 3,547 | 0 / 0 / 7,962 | 1 | 7,961 |
| Alibaba Q-learning | -51,724.50 | 15,020 | 3,547 | 2,469 / 3,024 / 2,469 | 4,938 | 0 |
| Validation-tuned threshold | -82,013.25 | 23,155 | 3,547 | 98 / 3,272 / 4,592 | 13 | 4,677 |
| Persistence | -51,394.00 | 15,924 | 3,547 | 0 / 7,962 / 0 | 0 | 0 |

PPO requested scale-up on every sample, reached three instances after one
feasible increase, and then made 7,961 infeasible requests. Its objective score
was worst among these policies. This replay demonstrates the checkpoint's
behavior under the explicitly stated model, and is a reason not to promote it
to the 1–3 instance controller. CPU and memory are trace observations; request
rate and latency in the PPO observations are estimates from the existing
`WorkloadSimulator` formulas. The violation count is exogenous and identical
across policies. None of these values are measured AWS service outcomes, and
this does not verify live PPO scaling.

## Short presentation outline

1. **Problem and contribution:** workload analysis, prediction, frontend/backend integration, safety-focused cloud control.
2. **Data:** Alibaba Cluster Trace v2018 machine usage; what CPU/memory mean and why it is only a workload proxy.
3. **Pipeline:** 10-second per-timestamp aggregation, continuous-segment selection, lag features, chronological 60/20/20 split.
4. **Forecast results:** persistence vs Random Forest table; tiny CPU gain and weaker memory result; persistence remains the baseline.
5. **Scaling analysis:** training-derived threshold sweep, validation selection, test results, and the difference between offline policy simulation and actual AWS.
6. **Application demonstration:** start backend/frontend, select Normal then Festival Peak, show decision, DB history, and `aws_applied=false`.
7. **AWS safety/status:** mock default, read-only preflight, live gates, and honest `NoCredentialsError` blocker; do not present mock as a real scale test.
8. **Limitations and next step:** obtain AWS role/profile access, verify preflight, get per-action approval, then capture actual AWS post-action capacity/health.

## PowerShell demo commands

Open two PowerShell terminals from the project. For a local demo, keep the backend in its default mock mode; do not enable live scaling.

Terminal 1, backend:

```powershell
cd C:\Users\khush\Desktop\IntelligentCloudAutoScaling_Cloud_Project_2026\src\backend
$env:AWS_MOCK_MODE = 'true'
$env:AWS_LIVE_SCALING_ENABLED = 'false'
$env:AWS_LIVE_SCALING_PERMISSION_CONFIRMED = 'false'
py -3.12 run.py
```

Terminal 2, frontend static server:

```powershell
cd C:\Users\khush\Desktop\IntelligentCloudAutoScaling_Cloud_Project_2026
py -3.12 -m http.server 5501
```

Open `http://127.0.0.1:5501/src/frontend/index.html`, click Normal and Festival Peak, and confirm the latest decision plus history entry while AWS Status says the request was bypassed. To rerun analysis, return to the repository root and run the four commands above for persistence, Random Forest comparison, threshold sweep, and workload plot.

## Screenshots to prepare (priority order)

1. Frontend Normal and Festival Peak metrics with latest backend decision and history refreshed; show AWS execution bypassed.
2. Alibaba workload overview plot with train/validation/test boundaries and training p95 lines.
3. Forecast CSV or terminal output showing both validation and held-out test metrics.
4. Threshold sweep validation-selected percentile and held-out test confusion counts/rates.
5. Mock test run showing passing tests; label it mock.
6. Once credentials work, read-only preflight with expected group/template/bounds/health. Redact account-sensitive fields as needed.
7. Only after separate approvals, AWS Console before/after ASG desired/current capacity and healthy instances plus backend logged response. Label these approved live AWS evidence.
## PPO training and evaluation audit (2026-10-21)

The historical `models/best_ppo_model.zip` has 10 float observation features
and `Discrete(3)` actions. It stores an active-instance observation high bound
of 50, while current `training/hyperparams.yaml` constructs max capacity 20.
The checkpoint contains no recoverable historical environment config or
normalizer. Low, normal, and high deterministic sample inputs all selected
scale-up. The exact historical training cause is unknown, so that artifact was
not modified.

A new reproducible Alibaba trainer and a separate normalized checkpoint were
added. The new config sets capacity 1–3, uses the existing PPOAgent wrapper,
trains for 100,000 steps on 37,157 chronological training rows, and selects its
checkpoint on three fixed validation windows. The 7,962-row test segment is
used only by the final comparison. The new model uses fixed feature scaling
to [0,1]; the backend adapter applies it only when the selected checkpoint
stores a [0,1] observation space. The original PPO checkpoint retains its raw
feature contract.

Reproduce with:

```powershell
py -3.12 training/train_alibaba2018_ppo.py
py -3.12 evaluation/compare_retrained_ppo_alibaba.py
py -3.12 -m pytest -p no:cacheprovider src/backend/tests/test_alibaba_ppo_v2.py src/backend/tests/test_ppo_alibaba_evaluation.py src/backend/tests/test_ppo_policy.py src/backend/tests/test_rl_agents.py -q
```

The final normalized run had validation mean return -3,456 at every 10,000-step
checkpoint. On the same held-out interval, PPO held at two instances on all
7,962 samples and matched persistence exactly: proxy reward -95,544, capacity
cost 15,924 instance-samples, zero feasible changes, and zero infeasible
requests. It did not improve on the Q baseline's proxy reward -87,582.25 (one
feasible scale-down to one instance, then hold). The validation-tuned threshold
had proxy reward -126,163.25 and 4,677 infeasible requests.

| Policy | Estimated latency SLA violations | Mean / p95 estimated latency after action | Observed CPU/memory boundary violations | Capacity steps at 1 / 2 / 3 | Requested down / hold / up |
|---|---:|---:|---:|---:|---:|
| Retrained PPO | 7,962 (100%) | 3,541.43 / 4,664 ms | 3,547 | 0 / 7,962 / 0 | 0 / 7,962 / 0 |
| Q-learning baseline | 7,962 (100%) | 4,986.17 / 5,000 ms | 3,547 | 7,962 / 0 / 0 | 1 / 7,961 / 0 |
| Threshold | 7,962 (100%) | 2,519.66 / 3,855.39 ms | 3,547 | 343 / 45 / 7,574 | 98 / 3,272 / 4,592 |
| Persistence | 7,962 (100%) | 3,541.43 / 4,664 ms | 3,547 | 0 / 7,962 / 0 | 0 / 7,962 / 0 |

The CPU/memory boundary count is fixed from observed trace percentiles and is
identical by definition. The latency estimate is also 100% violating because
the existing CPU-to-request-rate mapping estimates every held-out sample above
the capacity of even three 100-request/second instances. This reveals a
calibration limitation in the simulator assumptions; it does not establish an
actual application SLA failure. Request rate and latency are estimates, not
Alibaba trace columns or measured AWS outcomes. The model remains an offline
candidate and has no demonstrated held-out improvement. Live Q-learning
behavior and all AWS settings were left unchanged.
