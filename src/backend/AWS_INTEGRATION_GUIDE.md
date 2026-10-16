# AWS Auto Scaling integration and safe verification

## Verified code behavior

- `AWS_MOCK_MODE=true` is the default. Mock mode keeps an in-memory group with bounds 1–3 and does not authenticate to AWS.
- Live AWS access is selected only with `AWS_MOCK_MODE=false`. Boto3 uses its normal credential chain: an attached IAM role, AWS environment credentials, or the optional `AWS_PROFILE`. This project does not require access keys in `.env`.
- A live capacity change requires `apply_to_aws: true` in that individual API request, `AWS_LIVE_SCALING_ENABLED=true`, and `AWS_LIVE_SCALING_PERMISSION_CONFIRMED=true` after an AWS administrator confirms the write policy. Both environment gates default to false. The request schema defaults to false. Frontend scenario and manual evaluation requests explicitly send false.
- `apply_to_aws=false` bypasses `set_desired_capacity`; it may still run read-only workload/ASG reads and stores the decision in the configured database.
- The backend refuses a live action if preflight fails, the expected ASG/region/template/bounds do not match, instances are not all `InService` and `Healthy`, another scaling activity is active, the action direction conflicts with current desired capacity, or the target is outside ASG min/max.
- A successful `SetDesiredCapacity` response means AWS accepted the desired-capacity request. It does not prove new instances have launched or become healthy. Run preflight again and verify actual instance health before another test.

## Expected target

| Setting | Expected value |
|---|---|
| Region | `ap-south-1` |
| Auto Scaling Group | `rl-autoscaling-group` |
| Launch template | `autoscaling-launch-template` |
| Minimum / maximum | 1 / 3 |
| Expected AWS account | Must be set after comparing `GetCallerIdentity` to the intended account |

The read-only check is `GET /api/v1/scaling/aws/preflight?requested_action=maintain` (or `scale_up` / `scale_down`). It reports caller account and ARN, expected-account match, target match, current and desired capacity, min/max, instance lifecycle/health, active scaling activities and whether the requested direction is allowed. It does not mutate capacity. `ready` stays false until `AWS_EXPECTED_ACCOUNT_ID` is configured and the account, group, template and expected bounds match.

`GetCallerIdentity` plus successful `DescribeAutoScalingGroups` and `DescribeScalingActivities` verifies the read path. AWS does not provide a safe way to prove `SetDesiredCapacity` permission without IAM policy simulation permission or attempting a mutation; preflight marks that permission unverified. A read-only preflight never tests it.

## IAM permissions

Use a dedicated role/profile restricted to this project. Read-only preflight needs:

- `sts:GetCallerIdentity`
- `autoscaling:DescribeAutoScalingGroups`
- `autoscaling:DescribeScalingActivities`

Live testing additionally needs `autoscaling:SetDesiredCapacity` scoped to the existing group ARN, using the actual account ID:

```text
arn:aws:autoscaling:ap-south-1:<ACCOUNT_ID>:autoScalingGroup:*:autoScalingGroupName/rl-autoscaling-group
```

The describe actions generally require `Resource: "*"`. Do not grant create/delete group, launch template, EC2 instance, IAM, billing, or account-management permissions for this project. Have an AWS administrator configure permissions; this project does not create or change IAM policies.

## Configure safe local access

From PowerShell, use a previously configured SSO or named AWS CLI profile. Do not place access keys in the repository or paste credentials into chat.

```powershell
cd C:\Users\khush\Desktop\IntelligentCloudAutoScaling_Cloud_Project_2026\src\backend
aws sso login --profile <YOUR_PROFILE>
$env:AWS_PROFILE = '<YOUR_PROFILE>'
$env:AWS_REGION = 'ap-south-1'
$env:AWS_ASG_NAME = 'rl-autoscaling-group'
$env:AWS_EXPECTED_ACCOUNT_ID = '<EXPECTED_ACCOUNT_ID>'
$env:AWS_EXPECTED_LAUNCH_TEMPLATE = 'autoscaling-launch-template'
$env:AWS_EXPECTED_MIN_SIZE = '1'
$env:AWS_EXPECTED_MAX_SIZE = '3'
$env:AWS_MOCK_MODE = 'false'
$env:AWS_LIVE_SCALING_ENABLED = 'false'
$env:AWS_LIVE_SCALING_PERMISSION_CONFIRMED = 'false'
python run.py
```

If the profile uses long-lived IAM user keys, prefer migrating it to AWS IAM Identity Center/SSO or temporary credentials. Never commit `src/backend/.env`; it is ignored by Git. `.env.example` contains non-secret defaults only.

## Stage A: mock tests

Run from `src/backend`:

```powershell
$env:AWS_MOCK_MODE = 'true'
$env:AWS_LIVE_SCALING_ENABLED = 'false'
python -m pytest tests/test_scaling.py tests/test_services.py -q
```

These tests exercise mock-only behavior and must not be represented as AWS evidence.

## Stage B: read-only AWS preflight

With the backend running in the terminal above and live scaling still disabled:

```powershell
aws sts get-caller-identity --profile $env:AWS_PROFILE
Invoke-RestMethod 'http://127.0.0.1:8000/api/v1/scaling/aws/preflight?requested_action=maintain' | ConvertTo-Json -Depth 8
```

Set `AWS_EXPECTED_ACCOUNT_ID` only after the displayed identity has been compared with the intended AWS account. Proceed only if `mode` is `live`, `identity.verified`, `target.account_matches_expected`, `target.matches_expected`, and `ready` are true; bounds are 1 and 3; and every listed instance is `InService` / `Healthy`. For the action to be tested, call preflight again with `requested_action=scale_up` or `scale_down` and confirm `action_allowed=true`. Access denied, missing credentials, wrong account/group/template/region, active activity, or unhealthy/pending instances block live tests.

Preflight proves the read permissions only. If write permission is uncertain, ask the AWS administrator to inspect the role policy. Do not “test” write access by sending a live request without explicit approval.

## Stages C and D: controlled live tests (approval required per action)

No live scaling tests are authorized by this guide. Before each individual scale-out or scale-in test, obtain explicit approval for that specific action. Keep the frontend at `apply_to_aws=false` throughout. Run only against `rl-autoscaling-group` in `ap-south-1`.

For each approved action:

1. Record preflight output and baseline desired/healthy capacity; do not continue unless the target and health checks pass.
2. Use `POST /api/v1/scaling/decision` first with the same workload and current count to confirm that the policy recommends the intended direction and a target within 1–3. This endpoint logs a decision but does not mutate AWS.
3. Obtain approval for the specific action and target. After an AWS administrator confirms the role's scoped `SetDesiredCapacity` permission, set `AWS_LIVE_SCALING_PERMISSION_CONFIRMED=true`; set `AWS_LIVE_SCALING_ENABLED=true` only in the backend process for that one approved test.
4. Send one `/api/v1/scaling/evaluate-and-act` request with identical policy inputs, `apply_to_aws=true`, and the approved current count. Do not automate retries.
5. Immediately set the live flag back to false, then rerun preflight. Confirm desired capacity, actual InService/Healthy count, and absence of an in-progress activity before considering the test complete or requesting approval for the next action.
6. For rollback, request an explicitly approved scale-in to the recorded baseline. Verify it in AWS with preflight. Do not terminate individual instances or alter any other resource.

The API accepts the live request only when both opt-ins are true. `SetDesiredCapacity` is serialized in this backend process and checks for in-progress ASG activities; these controls do not replace AWS-side monitoring or approval. Avoid running multiple backend workers during controlled tests.

## Stage E: frontend no-mutation check

With `AWS_LIVE_SCALING_ENABLED=false`, click Normal and Festival Peak. Both frontend call sites send `apply_to_aws=false`; the API response must show `aws_applied=false` and the bypass message. History should update. The frontend cannot turn on the backend live flag. Never use the mock indicator as evidence that real capacity changed.

## Failure handling and rollback

Missing credentials and AWS errors are reported by error code (for example `NoCredentialsError`, `AccessDenied`, `Throttling`, or a service error) without returning credential material. Correct profile/role access or wait for throttling to clear; do not retry a capacity mutation automatically. A failed or timed-out request may have an uncertain outcome, so inspect read-only preflight before any retry. If health degrades or desired capacity is unexpected, leave live scaling disabled and use the approved rollback procedure through the same ASG only.

## Review evidence to capture

Capture screenshots with secrets and account-sensitive details redacted:

1. Read-only preflight JSON showing region, group, template, min/max, desired/current capacity, healthy count, `ready`, and the stated write-permission limitation.
2. AWS Console Auto Scaling Group details for `rl-autoscaling-group` showing min/max/desired capacity.
3. AWS Console instance management showing instance lifecycle and health before and after each approved test.
4. Backend response and scaling history row showing action, desired count, `aws_applied`, database log state and timestamp.
5. Frontend Normal and Festival Peak decision panels showing the backend policy result while live scaling is disabled.

Label screenshots as **mock**, **read-only AWS**, or **approved live AWS test**. A mock test or code path is not live AWS evidence.
