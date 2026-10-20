# Project readiness and verification status

Status snapshot: 2026-10-19. This report separates local code/tests from AWS
validation. No AWS CLI, SDK, console, remote deployment, schedule, or live
capacity mutation was used during this local closeout.

## Local application

- Backend entry point: from `src/backend`, run `py -3.12 run.py`. It binds to
  `127.0.0.1` by default; `PORT` and `HOST` can override the address.
- Frontend: from the repository root, run
  `py -3.12 -m http.server 5500 --bind 127.0.0.1 -d src/frontend` and open
  `http://127.0.0.1:5500`.
- The frontend reads the backend base URL from the `api-base-url` meta tag and
  defaults to `http://127.0.0.1:8000`.
- Local `.env.example` defaults to SQLite, AWS mock mode, and disabled live
  scaling. Do not replace these with live settings for normal simulations.
- Browser/manual workload inputs and Alibaba replay are `manual_simulated` or
  explicitly synthetic; only the dedicated CloudWatch collector may label
  telemetry as AWS-derived.

## Policy and artifacts

The existing Q-learning policy remains the backend default. PPO, DQN, two HRL
implementations, training scripts, and evaluation code are retained for
simulation/benchmark use. The PPO checkpoint loads with the verified 10-value
observation and 3-action shape, but the committed training YAML says
`max_instances=20` while the checkpoint observation bound is 50. Its precise
training configuration is therefore unknown; predictions on three example
workloads all selected scale-out, so this is not approved as the live policy.
Saved simulated charts/results do not demonstrate production latency, costs,
instance health, or AWS scaling behavior.

Alibaba raw inputs stay out of ordinary Git history. See [data README](../data/README.md)
for source, expected layout, preprocessing and experiment commands. Use
`requirements-rl.txt` for the local RL/evaluation toolchain and
`src/backend/requirements.txt` for the API.

## Local verification

The baseline recorded before this closeout was **55 passed in 15.37s**. The
final full backend command was run from `src/backend`:

```powershell
$env:AWS_EC2_METADATA_DISABLED='true'
py -3.12 -m pytest -p no:cacheprovider tests -q
```

Final result: **94 passed in 16.58s**. All pytest fixtures force mock AWS and
use in-memory SQLite. Mocked AWS client actions are covered; no AWS API call
occurred.

`node --check src/frontend/script.js` passed. I also served the UI and backend
temporarily on loopback ports 18080/18000, with mock AWS forced, an in-memory
database, and matching CORS. Browser results from the five real UI button
flows:

| Preset | UI metrics: req/s, CPU, latency | API metrics sent: CPU, memory, req/s, latency | Backend decision | Current → desired | History |
|---|---:|---:|---|---:|---|
| Low | 30, 25%, 110 ms | 25%, 30%, 30, 110 ms | scale down | 2 → 1 | saved |
| Normal | 60, 45%, 150 ms | 45%, 50%, 60, 150 ms | maintain | 2 → 2 | saved |
| Medium | 100, 65%, 210 ms | 65%, 70%, 100, 210 ms | scale up | 2 → 3 | saved |
| High | 150, 82%, 310 ms | 82%, 87%, 150, 310 ms | scale up | 2 → 3 | saved |
| Festival peak | 240, 94%, 520 ms | 94%, 95%, 240, 520 ms | scale up | 2 → 3 | saved |

Every request used `current_instances=2` and `apply_to_aws=false`; these are
independent decisions, so the displayed current capacity remained 2. Backend
logs show all five POSTs and history GETs returned HTTP 200, all CORS OPTIONS
checks returned 200, and every controller result logged `aws_applied=false`.
The local API showed the five accumulated decisions in history. The browser's
developer-console log API is not exposed through the available UI control, so I
cannot certify a full console-log sweep; no frontend fallback/error state was
displayed, and the JavaScript syntax check passed. The initial page load also
requested a missing default favicon (404); the HTML now supplies an empty data
favicon to prevent that request. The final page reload after this small change
was not repeated.

Alibaba replay carries the CSV's integer trace-relative seconds as
`source_timestamp_seconds` provenance. Database `timestamp` remains server
receipt time. Tests cover both fields distinctly; malformed or non-integral
source timestamp values are rejected row-by-row instead of silently converted.

## AWS validation status: owner action required

The deployment owner must perform and record the AWS-side steps. The application
defaults remain mock-only, and this work intentionally does not authenticate or
mutate AWS.

1. Confirm AWS account identity and region `ap-south-1` in the AWS console/CLI.
2. Confirm the existing `rl-autoscaling-group`, launch template, ALB and target
   group; verify min/max bounds and healthy instance targets.
3. Confirm a least-privilege identity can read STS identity, ASG group/activity,
   EC2 instance status, ELB target health and required CloudWatch metrics.
4. Configure the deployment environment explicitly; keep the test/UI simulation
   path on `AWS_MOCK_MODE=true` and all live write gates false.
5. Capture read-only preflight output and establish a rollback capacity value.
6. If a real scaling demonstration is needed, get explicit approval for each
   action before setting live gates. Scale only the named ASG within its
   configured 1–3 range, wait for activity completion, and verify desired/running
   capacity and target health after each action.
7. Restore the original desired capacity, confirm no scheduled action or replay
   event can keep changing capacity, and save console screenshots as evidence.

Until the owner completes an authenticated read and an explicitly approved,
verified scale-out and scale-in, real AWS integration is **not verified**.
