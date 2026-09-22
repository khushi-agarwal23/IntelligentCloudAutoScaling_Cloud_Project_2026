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
    assert data["confidence"] > 0


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
        "instance_count": 4,
        "error_rate": 0.0
    })

    hist_res = client.get("/api/v1/scaling/history?limit=10")
    assert hist_res.status_code == 200
    assert len(hist_res.json()) >= 1
