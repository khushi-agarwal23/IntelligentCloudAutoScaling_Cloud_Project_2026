def test_scaling_decision_endpoint(client):
    payload = {
        "cpu_percent": 88.0,
        "memory_percent": 85.0,
        "request_rate": 350.0,
        "response_time_ms": 1100.0,
        "instance_count": 2,
        "error_rate": 1.0
    }
    response = client.post("/api/v1/scaling/decision", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["action"] == "scale_up"
    assert data["desired_instances"] > 2
    assert "reason" in data
    assert data["confidence"] >= 0
    assert data["triggered_by"] in {"q_learning_local", "heuristic_fallback", "rl_agent"}


def test_scaling_evaluate_and_act_orchestrator(client):
    payload = {
        "cpu_percent": 92.0,
        "memory_percent": 89.0,
        "request_rate": 450.0,
        "response_time_ms": 1250.0,
        "current_instances": 2,
        "apply_to_aws": True
    }
    response = client.post("/api/v1/scaling/evaluate-and-act", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["aws_applied"] is True
    assert "decision" in data
    assert data["decision"]["action"] == "scale_up"
    assert data["db_logged"] is True


def test_scaling_feedback_and_reward(client):
    # First create a decision
    dec_res = client.post("/api/v1/scaling/decision", json={
        "cpu_percent": 80.0,
        "memory_percent": 80.0,
        "request_rate": 300.0,
        "response_time_ms": 900.0,
        "instance_count": 2,
        "error_rate": 0.0
    })
    dec_id = dec_res.json()["id"]

    # Now post feedback
    feedback_payload = {
        "decision_id": dec_id,
        "observed_response_time_ms": 250.0,
        "observed_cpu_percent": 60.0,
        "reward": 0.85
    }
    feedback_res = client.post("/api/v1/scaling/feedback", json=feedback_payload)
    assert feedback_res.status_code == 200
    assert feedback_res.json()["calculated_reward"] == 0.85


def test_scaling_history(client):
    client.post("/api/v1/scaling/decision", json={
        "cpu_percent": 20.0,
        "memory_percent": 25.0,
        "request_rate": 10.0,
        "response_time_ms": 120.0,
        "instance_count": 3,
        "error_rate": 0.0
    })

    hist_res = client.get("/api/v1/scaling/history?limit=10")
    assert hist_res.status_code == 200
    assert len(hist_res.json()) >= 1


def test_evaluate_and_act_defaults_to_no_aws_mutation(client, monkeypatch):
    from app.services.aws_asg_client import aws_client

    def unexpected_mutation(*args, **kwargs):
        raise AssertionError("AWS mutation API must not be called without explicit opt-in")

    monkeypatch.setattr(aws_client, "set_desired_capacity", unexpected_mutation)
    response = client.post("/api/v1/scaling/evaluate-and-act", json={
        "cpu_percent": 94,
        "memory_percent": 95,
        "request_rate": 240,
        "response_time_ms": 520,
        "current_instances": 1,
    })
    assert response.status_code == 200
    assert response.json()["aws_applied"] is False
    assert response.json()["aws_message"] == "AWS ASG execution bypassed (apply_to_aws=False)."


def test_mock_preflight_reports_bounds_and_simulated_identity(client):
    from app.services.aws_asg_client import aws_client

    aws_client.set_desired_capacity(2)
    response = client.get("/api/v1/scaling/aws/preflight?requested_action=scale_up")
    assert response.status_code == 200
    data = response.json()
    assert data["mode"] == "mock"
    assert data["identity"]["verified"] is False
    assert data["capacity"]["minimum"] == 1
    assert data["capacity"]["maximum"] == 3
    assert data["capacity"]["action_allowed"] is True


def test_live_preflight_reports_live_unavailable_without_mock_fallback(client, monkeypatch):
    from app.config import settings
    from app.services.aws_asg_client import aws_client

    monkeypatch.setattr(settings, "AWS_MOCK_MODE", False)
    monkeypatch.setattr(aws_client, "mock_mode", False)
    monkeypatch.setattr(aws_client, "_client", None)
    monkeypatch.setattr(aws_client, "_sts_client", None)
    monkeypatch.setattr(aws_client, "_initialization_error", "NoCredentialsError")

    response = client.get("/api/v1/scaling/aws/preflight")

    assert response.status_code == 200
    data = response.json()
    assert data["mode"] == "live"
    assert data["ready"] is False
    assert data["identity"]["verified"] is False
    assert data["errors"] == ["NoCredentialsError"]
    assert data["health"].get("simulated") is not True
    assert data["runtime"]["configured_mock_mode"] is False
    assert data["runtime"]["client_mock_mode"] is False


def test_preflight_fails_closed_when_initialized_client_mode_is_stale(client, monkeypatch):
    from app.config import settings
    from app.services.aws_asg_client import aws_client

    monkeypatch.setattr(settings, "AWS_MOCK_MODE", False)
    monkeypatch.setattr(aws_client, "mock_mode", True)

    response = client.get("/api/v1/scaling/aws/preflight")

    assert response.status_code == 200
    data = response.json()
    assert data["mode"] == "configuration_error"
    assert data["ready"] is False
    assert data["errors"] == ["AWSModeConfigurationMismatch"]
    assert data["runtime"]["configured_mock_mode"] is False
    assert data["runtime"]["client_mock_mode"] is True


def test_live_mutation_requires_backend_opt_in(client, monkeypatch):
    from app.config import settings
    from app.services.aws_asg_client import aws_client

    monkeypatch.setattr(aws_client, "mock_mode", False)
    monkeypatch.setattr(settings, "AWS_LIVE_SCALING_ENABLED", False)
    response = client.post("/api/v1/scaling/evaluate-and-act", json={
        "cpu_percent": 94,
        "memory_percent": 95,
        "request_rate": 240,
        "response_time_ms": 520,
        "current_instances": 1,
        "apply_to_aws": True,
    })
    assert response.status_code == 403
    assert "Live AWS scaling is disabled" in response.json()["detail"]


def test_live_mutation_requires_confirmed_write_permission(client, monkeypatch):
    from app.config import settings
    from app.services.aws_asg_client import aws_client

    monkeypatch.setattr(aws_client, "mock_mode", False)
    monkeypatch.setattr(settings, "AWS_LIVE_SCALING_ENABLED", True)
    monkeypatch.setattr(settings, "AWS_LIVE_SCALING_PERMISSION_CONFIRMED", False)
    response = client.post("/api/v1/scaling/evaluate-and-act", json={
        "cpu_percent": 94,
        "memory_percent": 95,
        "request_rate": 240,
        "response_time_ms": 520,
        "current_instances": 1,
        "apply_to_aws": True,
    })
    assert response.status_code == 403
    assert "permission has not been confirmed" in response.json()["detail"]


def test_traffic_scenarios_log_decisions_without_aws_mutation(client, monkeypatch):
    from app.services.aws_asg_client import aws_client

    def unexpected_mutation(*args, **kwargs):
        raise AssertionError("Frontend traffic scenarios must never mutate AWS")

    monkeypatch.setattr(aws_client, "set_desired_capacity", unexpected_mutation)
    scenarios = [
        (25, 30, 30, 110),
        (45, 50, 60, 150),
        (65, 70, 100, 210),
        (82, 87, 150, 310),
        (94, 95, 240, 520),
    ]
    ids = []
    for cpu, memory, request_rate, latency in scenarios:
        response = client.post("/api/v1/scaling/evaluate-and-act", json={
            "cpu_percent": cpu,
            "memory_percent": memory,
            "request_rate": request_rate,
            "response_time_ms": latency,
            "current_instances": 2,
            "apply_to_aws": False,
        })
        assert response.status_code == 200
        result = response.json()
        assert result["db_logged"] is True
        assert result["aws_applied"] is False
        assert result["aws_message"] == "AWS ASG execution bypassed (apply_to_aws=False)."
        ids.append(result["decision"]["id"])

    history = client.get("/api/v1/scaling/history?limit=20")
    assert history.status_code == 200
    assert set(ids).issubset({row["id"] for row in history.json()})
