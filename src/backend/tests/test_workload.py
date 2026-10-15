def test_workload_metric_ingestion(client):
    payload = {
        "cpu_percent": 78.5,
        "memory_percent": 82.0,
        "request_rate": 320.0,
        "response_time_ms": 650.0,
        "instance_count": 3,
        "error_rate": 0.5
    }
    response = client.post("/api/v1/workload/metrics", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["cpu_percent"] == payload["cpu_percent"]
    assert data["instance_count"] == 3
    assert "timestamp" in data


def test_batch_workload_metric_ingestion(client):
    batch = {
        "metrics": [
            {
                "cpu_percent": 45.0,
                "memory_percent": 50.0,
                "request_rate": 100.0,
                "response_time_ms": 150.0,
                "instance_count": 2,
                "error_rate": 0.0
            },
            {
                "cpu_percent": 85.0,
                "memory_percent": 88.0,
                "request_rate": 450.0,
                "response_time_ms": 950.0,
                "instance_count": 2,
                "error_rate": 1.2
            }
        ]
    }
    response = client.post("/api/v1/workload/batch", json=batch)
    assert response.status_code == 201
    data = response.json()
    assert data["ingested_count"] == 2


def test_workload_latest_and_history(client):
    client.post("/api/v1/workload/metrics", json={
        "cpu_percent": 55.0,
        "memory_percent": 60.0,
        "request_rate": 200.0,
        "response_time_ms": 300.0,
        "instance_count": 2,
        "error_rate": 0.0
    })

    latest_res = client.get("/api/v1/workload/latest")
    assert latest_res.status_code == 200
    assert latest_res.json()["cpu_percent"] == 55.0

    history_res = client.get("/api/v1/workload/history?limit=10")
    assert history_res.status_code == 200
    assert len(history_res.json()) >= 1


def test_smoothed_workload_state_computation(client):
    # Insert multiple metrics to test rolling average
    for cpu in [40.0, 60.0, 80.0]:
        client.post("/api/v1/workload/metrics", json={
            "cpu_percent": cpu,
            "memory_percent": 50.0,
            "request_rate": 150.0,
            "response_time_ms": 250.0,
            "instance_count": 2,
            "error_rate": 0.0
        })

    state_res = client.get("/api/v1/workload/state")
    assert state_res.status_code == 200
    data = state_res.json()
    assert "cpu_percent" in data
    assert data["instance_count"] == 2
