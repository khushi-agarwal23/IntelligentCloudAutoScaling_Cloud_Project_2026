import hashlib
import hmac
import json
import time

import pytest
from datetime import datetime, timedelta, timezone


def _signed(body, secret):
    stamp = str(int(time.time()))
    signature = hmac.new(secret.encode(), stamp.encode() + b"." + body, hashlib.sha256).hexdigest()
    return {"X-Replay-Timestamp": stamp, "X-Replay-Signature": signature}


def test_replay_hmac_and_idempotency(client, monkeypatch):
    from app.config import settings
    from app.routers import replay as replay_module

    secret = "test-only-secret"
    monkeypatch.setattr(settings, "WORKLOAD_REPLAY_HMAC_SECRET", secret)
    calls = []

    def controller(*args, **kwargs):
        calls.append(kwargs.get("event_id"))
        return {"decision": type("Decision", (), {"id": 1, "action": "maintain", "current_instances": 2,
                                                  "desired_instances": 2, "triggered_by": "q_learning_local"})(),
                "aws_applied": False, "aws_message": "AWS bypassed", "db_logged": True}

    monkeypatch.setattr(replay_module, "evaluate_and_apply", controller)
    payload = {"event_type": "metric", "event_id": "eb-1", "replay_id": "replay-1", "sequence": 1,
               "metric": {"cpu_percent": 40, "memory_percent": 50, "request_rate": 20,
                          "response_time_ms": 100, "instance_count": 2, "error_rate": 0,
                          "source_timestamp_seconds": 160380},
               "apply_to_aws": False}
    body = json.dumps(payload, separators=(",", ":")).encode()
    headers = _signed(body, secret)
    first = client.post("/api/v1/workload/replay/events", content=body, headers=headers)
    duplicate = client.post("/api/v1/workload/replay/events", content=body, headers=headers)
    assert first.status_code == 200
    assert duplicate.status_code == 200 and duplicate.json()["duplicate"] is True
    assert calls == ["eb-1"]
    metric = client.get("/api/v1/workload/history?limit=1").json()[0]
    provenance = json.loads(metric["data_provenance"])
    assert provenance["source_timestamp_seconds"] == 160380
    assert provenance["source_timestamp_unit"] == "trace_relative_seconds"


def test_replay_rejects_invalid_signature(client, monkeypatch):
    from app.config import settings
    monkeypatch.setattr(settings, "WORKLOAD_REPLAY_HMAC_SECRET", "test-only-secret")
    response = client.post("/api/v1/workload/replay/events", content=b"{}", headers={
        "X-Replay-Timestamp": str(int(time.time())), "X-Replay-Signature": "bad"})
    assert response.status_code == 401


def test_replay_requires_configuration_and_valid_event_schema(client, monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "WORKLOAD_REPLAY_HMAC_SECRET", None)
    unavailable = client.post("/api/v1/workload/replay/events", content=b"{}")
    assert unavailable.status_code == 503

    secret = "test-only-secret"
    monkeypatch.setattr(settings, "WORKLOAD_REPLAY_HMAC_SECRET", secret)
    payload = {"event_type": "metric", "event_id": "invalid-event", "replay_id": "r1", "sequence": 0}
    body = json.dumps(payload, separators=(",", ":")).encode()
    invalid = client.post("/api/v1/workload/replay/events", content=body, headers=_signed(body, secret))
    assert invalid.status_code == 422


def test_replay_event_id_conflict_and_live_flag_are_rejected(client, monkeypatch):
    from app.config import settings

    secret = "test-only-secret"
    monkeypatch.setattr(settings, "WORKLOAD_REPLAY_HMAC_SECRET", secret)
    monkeypatch.setattr(settings, "WORKLOAD_REPLAY_ALLOW_LIVE_SCALING", False)
    live_payload = {"event_type": "completed", "event_id": "live-disabled", "replay_id": "r1",
                    "apply_to_aws": True}
    live_body = json.dumps(live_payload, separators=(",", ":")).encode()
    live = client.post("/api/v1/workload/replay/events", content=live_body, headers=_signed(live_body, secret))
    assert live.status_code == 403

    first_payload = {"event_type": "completed", "event_id": "conflict-event", "replay_id": "r1"}
    first_body = json.dumps(first_payload, separators=(",", ":")).encode()
    first = client.post("/api/v1/workload/replay/events", content=first_body, headers=_signed(first_body, secret))
    changed_payload = {**first_payload, "replay_id": "different-replay"}
    changed_body = json.dumps(changed_payload, separators=(",", ":")).encode()
    conflict = client.post("/api/v1/workload/replay/events", content=changed_body, headers=_signed(changed_body, secret))
    assert first.status_code == 200
    assert conflict.status_code == 409


def test_replay_controller_failure_is_durable_and_not_repeated(client, monkeypatch):
    from fastapi import HTTPException
    from app.config import settings
    from app.routers import replay as replay_module

    secret = "test-only-secret"
    monkeypatch.setattr(settings, "WORKLOAD_REPLAY_HMAC_SECRET", secret)
    calls = []

    def fail(*args, **kwargs):
        calls.append(kwargs.get("event_id"))
        raise HTTPException(status_code=503, detail="local mocked service failure")

    monkeypatch.setattr(replay_module, "evaluate_and_apply", fail)
    payload = {"event_type": "metric", "event_id": "failed-event", "replay_id": "r1", "sequence": 1,
               "metric": {"cpu_percent": 40, "memory_percent": 50, "request_rate": 20,
                          "response_time_ms": 100, "instance_count": 2}}
    body = json.dumps(payload, separators=(",", ":")).encode()
    first = client.post("/api/v1/workload/replay/events", content=body, headers=_signed(body, secret))
    retry = client.post("/api/v1/workload/replay/events", content=body, headers=_signed(body, secret))
    assert first.status_code == 503
    assert retry.status_code == 409
    assert calls == ["failed-event"]


def test_live_cloudwatch_failure_is_read_only_503(client, monkeypatch):
    from app.routers import scaling as scaling_module
    from app.services.cloudwatch_telemetry import TelemetryUnavailable
    calls = []

    def fail():
        calls.append("read")
        raise TelemetryUnavailable("AccessDenied", "read denied")

    monkeypatch.setattr(scaling_module.cloudwatch_telemetry, "collect", fail)
    response = client.post("/api/v1/scaling/evaluate-cloudwatch", json={"apply_to_aws": True})
    assert response.status_code == 503
    assert response.json()["detail"]["aws_mutation_attempted"] is False
    assert calls == ["read"]


def test_controller_rejects_invalid_telemetry(db_session):
    from fastapi import HTTPException
    from app.services.scaling_controller import evaluate_and_apply
    with pytest.raises(HTTPException) as exc:
        evaluate_and_apply(db_session, {"cpu_percent": 120, "request_rate": 0,
                                        "response_time_ms": 1, "instance_count": 2},
                           telemetry_source="test", apply_to_aws=False)
    assert exc.value.status_code == 422


def test_manual_simulation_without_capacity_does_not_read_aws(client, monkeypatch):
    from app.services.aws_asg_client import aws_client

    def unexpected_read(*args, **kwargs):
        raise AssertionError("manual simulation must not read AWS capacity")

    monkeypatch.setattr(aws_client, "get_current_capacity", unexpected_read)
    monkeypatch.setattr(aws_client, "preflight", unexpected_read)
    response = client.post("/api/v1/scaling/evaluate-and-act", json={
        "cpu_percent": 40, "memory_percent": 50, "request_rate": 30,
        "response_time_ms": 100, "apply_to_aws": False,
    })
    assert response.status_code == 200
    assert response.json()["decision"]["telemetry_source"] == "manual_simulated"
    assert response.json()["aws_applied"] is False


def test_manual_simulation_rejects_partial_metrics(client):
    response = client.post("/api/v1/scaling/evaluate-and-act", json={
        "cpu_percent": 40, "request_rate": 30,
    })
    assert response.status_code == 422


def test_manual_metrics_cannot_request_real_aws_scaling(client, monkeypatch):
    from app.config import settings
    from app.services.aws_asg_client import aws_client

    monkeypatch.setattr(aws_client, "mock_mode", False)
    monkeypatch.setattr(settings, "AWS_LIVE_SCALING_ENABLED", True)
    monkeypatch.setattr(settings, "AWS_LIVE_SCALING_PERMISSION_CONFIRMED", True)
    monkeypatch.setattr(aws_client, "preflight", lambda **kwargs: pytest.fail("manual input must be rejected before AWS preflight"))
    response = client.post("/api/v1/scaling/evaluate-and-act", json={
        "cpu_percent": 95, "memory_percent": 90, "request_rate": 300,
        "response_time_ms": 800, "current_instances": 2, "apply_to_aws": True,
    })
    assert response.status_code == 403
    assert "CloudWatch telemetry" in response.json()["detail"]


def test_decision_endpoint_rejects_unsupported_policy_action(client, monkeypatch):
    from app.services import scaling_controller

    monkeypatch.setattr(scaling_controller, "query_rl_agent", lambda state: {
        "action": "terminate_everything", "desired_instances": 0,
    })
    response = client.post("/api/v1/scaling/decision", json={
        "cpu_percent": 40, "memory_percent": 50, "request_rate": 20,
        "response_time_ms": 100, "instance_count": 2,
    })
    assert response.status_code == 503


@pytest.mark.parametrize("field,value", [("memory_percent", 101), ("error_rate", -1), ("instance_count", float("nan"))])
def test_controller_rejects_out_of_range_optional_telemetry(db_session, field, value):
    from fastapi import HTTPException
    from app.services.scaling_controller import evaluate_and_apply
    state = {"cpu_percent": 40, "memory_percent": 50, "request_rate": 10,
             "response_time_ms": 100, "instance_count": 2, "error_rate": 0}
    state[field] = value
    with pytest.raises(HTTPException) as exc:
        evaluate_and_apply(db_session, state, telemetry_source="test", apply_to_aws=False)
    assert exc.value.status_code == 422


class FakeAwsSession:
    def __init__(self, account="123456789012", cloudwatch_error=None, stale=False):
        self.account = account
        self.cloudwatch_error = cloudwatch_error
        self.stale = stale
        self.queries = []

    def client(self, service):
        return {
            "sts": FakeSts(self), "autoscaling": FakeAsg(), "elbv2": FakeElb(),
            "cloudwatch": FakeCloudWatch(self),
        }[service]


class FakeSts:
    def __init__(self, session): self.session = session
    def get_caller_identity(self): return {"Account": self.session.account}


class FakeAsg:
    def describe_auto_scaling_groups(self, **kwargs):
        return {"AutoScalingGroups": [{
            "AutoScalingGroupName": "rl-autoscaling-group", "DesiredCapacity": 2,
            "MinSize": 1, "MaxSize": 3,
            "LaunchTemplate": {"LaunchTemplateName": "autoscaling-launch-template"},
            "Instances": [
                {"InstanceId": "i-a", "LifecycleState": "InService", "HealthStatus": "Healthy"},
                {"InstanceId": "i-b", "LifecycleState": "InService", "HealthStatus": "Healthy"},
            ],
        }]}


class FakeElb:
    def describe_load_balancers(self, **kwargs):
        return {"LoadBalancers": [{"LoadBalancerArn": "arn:aws:elasticloadbalancing:ap-south-1:123456789012:loadbalancer/app/autoscaling-alb/84d05b5264b0c729", "State": {"Code": "active"}}]}
    def describe_target_groups(self, **kwargs):
        return {"TargetGroups": [{"TargetGroupArn": "arn:aws:elasticloadbalancing:ap-south-1:123456789012:targetgroup/rl-target-group/2182a676fa52dc32", "TargetType": "instance", "LoadBalancerArns": ["arn:aws:elasticloadbalancing:ap-south-1:123456789012:loadbalancer/app/autoscaling-alb/84d05b5264b0c729"]}]}
    def describe_target_health(self, **kwargs):
        return {"TargetHealthDescriptions": [
            {"Target": {"Id": "i-a"}, "TargetHealth": {"State": "healthy"}},
            {"Target": {"Id": "i-b"}, "TargetHealth": {"State": "healthy"}},
        ]}


class FakeCloudWatch:
    def __init__(self, session): self.session = session
    def get_metric_data(self, **kwargs):
        from botocore.exceptions import ClientError
        if self.session.cloudwatch_error:
            raise ClientError({"Error": {"Code": self.session.cloudwatch_error, "Message": "mock denied"}}, "GetMetricData")
        self.session.queries = kwargs["MetricDataQueries"]
        timestamp = datetime.now(timezone.utc) - (timedelta(minutes=30) if self.session.stale else timedelta(seconds=30))
        values = {"cpu0": 40.0, "cpu1": 60.0, "mem0": 50.0, "mem1": 70.0,
                  "requests": 600.0, "latency": 0.2, "errors": 3.0}
        return {"MetricDataResults": [{"Id": key, "Timestamps": [timestamp], "Values": [value]}
                                       for key, value in values.items()]}


def test_cloudwatch_collector_returns_fresh_real_provenance(monkeypatch):
    from app.config import settings
    from app.services.cloudwatch_telemetry import CloudWatchTelemetryClient
    session = FakeAwsSession()
    monkeypatch.setattr(settings, "AWS_MOCK_MODE", False)
    monkeypatch.setattr(settings, "AWS_EXPECTED_ACCOUNT_ID", "123456789012")
    result = CloudWatchTelemetryClient(session=session).collect()
    assert result["ready"] is True
    assert result["metrics"]["cpu_percent"] == 50
    assert result["metrics"]["request_rate"] == 10
    assert result["metrics"]["response_time_ms"] == 200
    assert result["metrics"]["error_rate"] == 0.5
    assert result["provenance"]["simulated"] is False
    assert result["provenance"]["source"] == "aws_cloudwatch"
    assert len(session.queries) == 7


def test_cloudwatch_latency_query_preserves_targetgroup_dimension_prefix(monkeypatch):
    """A malformed TargetGroup dimension must not masquerade as missing traffic."""
    from app.config import settings
    from app.services.cloudwatch_telemetry import CloudWatchTelemetryClient

    now = datetime(2026, 1, 1, 12, 0, 30, tzinfo=timezone.utc)

    class WindowAwareCloudWatch(FakeCloudWatch):
        def get_metric_data(self, **kwargs):
            response = super().get_metric_data(**kwargs)
            self.session.start_time = kwargs["StartTime"]
            self.session.end_time = kwargs["EndTime"]
            latency_query = next(q for q in kwargs["MetricDataQueries"] if q["Id"] == "latency")
            latency_dimensions = latency_query["MetricStat"]["Metric"]["Dimensions"]
            # Model CloudWatch returning no series for the malformed TG value.
            tg_dimension = next(d["Value"] for d in latency_dimensions if d["Name"] == "TargetGroup")
            if not tg_dimension.startswith("targetgroup/"):
                for result in response["MetricDataResults"]:
                    if result["Id"] == "latency":
                        result["Timestamps"] = []
                        result["Values"] = []
            else:
                for result in response["MetricDataResults"]:
                    timestamp = now - (timedelta(minutes=1) if result["Id"] == "latency" else timedelta(minutes=5))
                    result["Timestamps"] = [timestamp]
            return response

    class WindowAwareSession(FakeAwsSession):
        def client(self, service):
            if service == "cloudwatch":
                return WindowAwareCloudWatch(self)
            return super().client(service)

    session = WindowAwareSession()
    monkeypatch.setattr(settings, "AWS_MOCK_MODE", False)
    monkeypatch.setattr(settings, "AWS_EXPECTED_ACCOUNT_ID", "123456789012")

    result = CloudWatchTelemetryClient(session=session).collect(now=now)

    assert result["metrics"]["response_time_ms"] == 200
    assert session.start_time == session.end_time - timedelta(hours=3)
    assert session.end_time == now.replace(second=0, microsecond=0)
    assert session.start_time.tzinfo == timezone.utc
    assert session.end_time.tzinfo == timezone.utc
    latency_query = next(query for query in session.queries if query["Id"] == "latency")
    metric_stat = latency_query["MetricStat"]
    assert metric_stat["Metric"]["Namespace"] == "AWS/ApplicationELB"
    assert metric_stat["Metric"]["MetricName"] == "TargetResponseTime"
    assert metric_stat["Metric"]["Dimensions"] == [
        {"Name": "LoadBalancer", "Value": "app/autoscaling-alb/84d05b5264b0c729"},
        {"Name": "TargetGroup", "Value": "targetgroup/rl-target-group/2182a676fa52dc32"},
    ]
    assert metric_stat["Stat"] == "Average"
    assert metric_stat["Period"] == 60


def test_cloudwatch_rejects_asg_healthy_instance_with_unhealthy_alb_target(monkeypatch):
    from app.config import settings
    from app.services.cloudwatch_telemetry import CloudWatchTelemetryClient, TelemetryUnavailable

    class OneUnhealthyTargetElb(FakeElb):
        def describe_target_health(self, **kwargs):
            return {"TargetHealthDescriptions": [
                {"Target": {"Id": "i-a", "Port": 80}, "TargetHealth": {"State": "healthy"}},
                {
                    "Target": {"Id": "i-b", "Port": 80},
                    "TargetHealth": {
                        "State": "unhealthy",
                        "Reason": "Target.FailedHealthChecks",
                        "Description": "Health checks failed",
                    },
                },
            ]}

    class OneUnhealthyTargetSession(FakeAwsSession):
        def client(self, service):
            if service == "elbv2":
                return OneUnhealthyTargetElb()
            return super().client(service)

    session = OneUnhealthyTargetSession()
    monkeypatch.setattr(settings, "AWS_MOCK_MODE", False)
    monkeypatch.setattr(settings, "AWS_EXPECTED_ACCOUNT_ID", "123456789012")

    with pytest.raises(TelemetryUnavailable) as exc:
        CloudWatchTelemetryClient(session=session).collect()

    assert exc.value.code == "TargetHealthMismatch"
    assert exc.value.diagnostics["asg_healthy_instance_ids"] == ["i-a", "i-b"]
    assert exc.value.diagnostics["alb_healthy_target_ids"] == ["i-a"]
    assert exc.value.diagnostics["asg_only_healthy_ids"] == ["i-b"]
    assert exc.value.diagnostics["alb_only_healthy_ids"] == []
    assert exc.value.diagnostics["alb_targets"][1] == {
        "instance_id": "i-b",
        "port": 80,
        "state": "unhealthy",
        "reason": "Target.FailedHealthChecks",
        "description": "Health checks failed",
    }
    assert session.queries == []


def test_current_aws_workload_endpoint_includes_health_mismatch_diagnostics(client, monkeypatch):
    from app.routers import workload as workload_module
    from app.services.cloudwatch_telemetry import TelemetryUnavailable

    diagnostics = {"asg_only_healthy_ids": ["i-b"], "alb_targets": [{"instance_id": "i-b", "state": "unhealthy"}]}

    def fail_with_health_mismatch():
        raise TelemetryUnavailable(
            "TargetHealthMismatch",
            "Healthy ALB target instance IDs do not exactly match the healthy ASG instance IDs.",
            diagnostics=diagnostics,
        )

    monkeypatch.setattr(workload_module.cloudwatch_telemetry, "collect", fail_with_health_mismatch)

    response = client.get("/api/v1/workload/aws/current")

    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "TargetHealthMismatch"
    assert response.json()["detail"]["diagnostics"] == diagnostics


@pytest.mark.parametrize("session,code", [
    (FakeAwsSession(account="000000000000"), "WrongAwsAccount"),
    (FakeAwsSession(cloudwatch_error="AccessDeniedException"), "AccessDeniedException"),
    (FakeAwsSession(stale=True), "CloudWatchMetricStale"),
])
def test_cloudwatch_collector_fails_closed(monkeypatch, session, code):
    from app.config import settings
    from app.services.cloudwatch_telemetry import CloudWatchTelemetryClient, TelemetryUnavailable
    monkeypatch.setattr(settings, "AWS_MOCK_MODE", False)
    monkeypatch.setattr(settings, "AWS_EXPECTED_ACCOUNT_ID", "123456789012")
    with pytest.raises(TelemetryUnavailable) as exc:
        CloudWatchTelemetryClient(session=session).collect()
    assert exc.value.code == code


class FakeAsgWriteClient:
    def __init__(self, error=None): self.error, self.calls = error, []
    def describe_auto_scaling_groups(self, **kwargs):
        return {"AutoScalingGroups": [{"DesiredCapacity": 2, "MinSize": 1, "MaxSize": 3}]}
    def describe_scaling_activities(self, **kwargs): return {"Activities": []}
    def set_desired_capacity(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            from botocore.exceptions import ClientError
            raise ClientError({"Error": {"Code": self.error, "Message": "mock failure"}}, "SetDesiredCapacity")


@pytest.mark.parametrize("desired,error,success,expected_calls", [
    (3, None, True, 1),
    (4, None, False, 0),
    (3, "AccessDenied", False, 1),
])
def test_mocked_asg_write_enforces_bounds_and_reports_failures(monkeypatch, desired, error, success, expected_calls):
    from app.config import settings
    from app.services.aws_asg_client import AWSAutoScalingClient
    monkeypatch.setattr(settings, "AWS_LIVE_SCALING_ENABLED", True)
    monkeypatch.setattr(settings, "AWS_LIVE_SCALING_PERMISSION_CONFIRMED", True)
    client = AWSAutoScalingClient()
    client.mock_mode = False
    client._client = FakeAsgWriteClient(error=error)
    result = client.set_desired_capacity(desired, expected_action="scale_up")
    assert result["success"] is success
    assert len(client._client.calls) == expected_calls
    if error:
        assert result["error_code"] == "AccessDenied"


@pytest.mark.parametrize("current,action", [(1, "scale_down"), (3, "scale_up")])
def test_controller_holds_policy_action_at_capacity_bounds(db_session, monkeypatch, current, action):
    from app.services import scaling_controller as controller
    from app.services.aws_asg_client import aws_client
    calls = []
    monkeypatch.setattr(aws_client, "mock_mode", True)
    monkeypatch.setattr(controller, "query_rl_agent", lambda state: {
        "action": action, "desired_instances": current - 1 if action == "scale_down" else current + 1,
        "reason": "mock policy", "confidence": 1.0,
    })
    monkeypatch.setattr(aws_client, "set_desired_capacity", lambda *a, **kw: calls.append((a, kw)))
    result = controller.evaluate_and_apply(
        db_session,
        {"cpu_percent": 50, "memory_percent": 50, "request_rate": 50,
         "response_time_ms": 100, "instance_count": current},
        telemetry_source="test", apply_to_aws=True,
    )
    assert result["decision"].action == "maintain"
    assert result["decision"].desired_instances == current
    assert result["aws_applied"] is False
    assert calls == []
