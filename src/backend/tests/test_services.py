from app.services.ai_client import fallback_scaling_decision
from app.services.aws_asg_client import AWSAutoScalingClient


def test_ai_client_heuristic_fallback_rules():
    # Test High Pressure -> Scale Up
    high_pressure_state = {
        "cpu_percent": 85.0,
        "memory_percent": 82.0,
        "request_rate": 350.0,
        "response_time_ms": 1100.0,
        "instance_count": 2,
        "error_rate": 0.0
    }
    decision = fallback_scaling_decision(high_pressure_state)
    assert decision["action"] == "scale_up"
    assert decision["desired_instances"] > 2
    assert decision["confidence"] >= 0.90

    # Test Low Pressure -> Scale Down
    low_pressure_state = {
        "cpu_percent": 20.0,
        "memory_percent": 25.0,
        "request_rate": 15.0,
        "response_time_ms": 150.0,
        "instance_count": 4,
        "error_rate": 0.0
    }
    decision_down = fallback_scaling_decision(low_pressure_state)
    assert decision_down["action"] == "scale_down"
    assert decision_down["desired_instances"] == 3

    # Test Normal Pressure -> Maintain
    normal_state = {
        "cpu_percent": 50.0,
        "memory_percent": 55.0,
        "request_rate": 100.0,
        "response_time_ms": 300.0,
        "instance_count": 3,
        "error_rate": 0.0
    }
    decision_maintain = fallback_scaling_decision(normal_state)
    assert decision_maintain["action"] == "maintain"
    assert decision_maintain["desired_instances"] == 3


def test_aws_asg_mock_client():
    client = AWSAutoScalingClient()
    assert client.mock_mode is True

    res = client.set_desired_capacity(5)
    assert res["success"] is True
    assert res["mode"] == "mock"
    assert res["desired_capacity"] == 5

    current = client.get_current_capacity()
    assert current == 5
