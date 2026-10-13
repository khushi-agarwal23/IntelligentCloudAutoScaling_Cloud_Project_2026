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
