import logging
import threading
from typing import Dict, Any
from ..config import settings

logger = logging.getLogger("backend.services.aws_asg_client")

# In-memory mock state for local testing without AWS credentials
_mock_asg_state = {
    "desired_capacity": 2,
    "min_size": 1,
    "max_size": 3,
    "name": settings.AWS_ASG_NAME
}


class AWSAutoScalingClient:
    def __init__(self):
        # Mock mode is explicit and remains the default. Live mode uses the
        # standard boto3 credential chain (role, environment, or CLI profile).
        self.mock_mode = settings.AWS_MOCK_MODE
        self.region = settings.AWS_REGION
        self.asg_name = settings.AWS_ASG_NAME
        self._client = None
        self._sts_client = None
        self._initialization_error = None
        self._mutation_lock = threading.Lock()

        if not self.mock_mode:
            try:
                import boto3
                session_kwargs = {"region_name": self.region}
                if settings.AWS_PROFILE:
                    session_kwargs["profile_name"] = settings.AWS_PROFILE
                session = boto3.Session(**session_kwargs)
                self._client = session.client("autoscaling")
                self._sts_client = session.client("sts")
                logger.info("AWS Auto Scaling client configured for region %s", self.region)
            except Exception as exc:
                self._initialization_error = self._error_code(exc)
                logger.warning("AWS client initialization failed (%s); live mode remains unavailable.", self._initialization_error)

    @staticmethod
    def _error_code(exc: Exception) -> str:
        if isinstance(exc, LookupError):
            return "AutoScalingGroupNotFound"
        response = getattr(exc, "response", {})
        return str(response.get("Error", {}).get("Code", exc.__class__.__name__))

    def _describe_group(self) -> Dict[str, Any]:
        response = self._client.describe_auto_scaling_groups(
            AutoScalingGroupNames=[self.asg_name]
        )
        groups = response.get("AutoScalingGroups", [])
        if not groups:
            raise LookupError("AutoScalingGroupNotFound")
        return groups[0]

    def _active_activities(self):
        response = self._client.describe_scaling_activities(
            AutoScalingGroupName=self.asg_name,
            MaxRecords=20,
        )
        return [
            {
                "activity_id": item.get("ActivityId"),
                "status_code": item.get("StatusCode"),
                "description": item.get("Description"),
            }
            for item in response.get("Activities", [])
            if item.get("StatusCode") in {"InProgress", "PreInService", "WaitingForInstanceId"}
        ]

    def _mock_preflight(self, requested_action=None):
        current = _mock_asg_state["desired_capacity"]
        minimum = _mock_asg_state["min_size"]
        maximum = _mock_asg_state["max_size"]
        allowed = self._action_allowed(requested_action, current, minimum, maximum)
        return {
            "mode": "mock",
            "ready": allowed,
            "identity": {"verified": False, "note": "Mock mode does not authenticate to AWS."},
            "target": {
                "region": self.region,
                "auto_scaling_group": self.asg_name,
                "launch_template": settings.AWS_EXPECTED_LAUNCH_TEMPLATE,
                "matches_expected": self.region == "ap-south-1" and self.asg_name == "rl-autoscaling-group",
            },
            "capacity": {
                "current": current,
                "desired": current,
                "minimum": minimum,
                "maximum": maximum,
                "requested_action": requested_action,
                "action_allowed": allowed,
            },
            "health": {"healthy_instances": current, "total_instances": current, "all_healthy": True, "simulated": True},
            "in_progress_activities": [],
            "permissions": {"read_only_preflight": "simulated", "set_desired_capacity": "not applicable in mock mode"},
            "errors": [],
        }

    @staticmethod
    def _action_allowed(action, current, minimum, maximum):
        if action is None or action == "maintain":
            return True
        if action == "scale_up":
            return current < maximum
        if action == "scale_down":
            return current > minimum
        return False

    def preflight(self, requested_action=None) -> Dict[str, Any]:
        """Read-only identity, ASG, capacity, health, activity and action check."""
        if self.mock_mode:
            return self._mock_preflight(requested_action)

        result = {
            "mode": "live",
            "ready": False,
            "identity": {"verified": False},
            "target": {"region": self.region, "auto_scaling_group": self.asg_name},
            "capacity": {"requested_action": requested_action, "action_allowed": False},
            "health": {"all_healthy": False},
            "in_progress_activities": [],
            "permissions": {
                "read_only_preflight": "not verified",
                "set_desired_capacity": "not verifiable without an IAM policy simulation or a live mutation; no mutation attempted",
            },
            "errors": [],
        }
        if self._client is None or self._sts_client is None:
            code = self._initialization_error or "AWSClientUnavailable"
            result["errors"].append(code)
            logger.warning("AWS read-only preflight unavailable (%s).", code)
            return result

        try:
            identity = self._sts_client.get_caller_identity()
            result["identity"] = {
                "verified": True,
                "account": identity.get("Account"),
                "arn": identity.get("Arn"),
            }
            group = self._describe_group()
            launch_template = group.get("LaunchTemplate") or {}
            group_template_name = launch_template.get("LaunchTemplateName")
            if not group_template_name:
                mixed_policy = group.get("MixedInstancesPolicy") or {}
                template_spec = (
                    (mixed_policy.get("LaunchTemplate") or {})
                    .get("LaunchTemplateSpecification") or {}
                )
                group_template_name = template_spec.get("LaunchTemplateName")
            minimum = int(group.get("MinSize", 0))
            maximum = int(group.get("MaxSize", 0))
            desired = int(group.get("DesiredCapacity", 0))
            in_service_healthy = [
                item for item in group.get("Instances", [])
                if item.get("LifecycleState") == "InService" and item.get("HealthStatus") == "Healthy"
            ]
            all_instances = group.get("Instances", [])
            activities = self._active_activities()
            target_matches = (
                self.region == "ap-south-1"
                and self.asg_name == "rl-autoscaling-group"
                and settings.AWS_EXPECTED_ACCOUNT_ID is not None
                and str(identity.get("Account")) == str(settings.AWS_EXPECTED_ACCOUNT_ID)
                and group.get("AutoScalingGroupName") == "rl-autoscaling-group"
                and group_template_name == settings.AWS_EXPECTED_LAUNCH_TEMPLATE
                and minimum == settings.AWS_EXPECTED_MIN_SIZE
                and maximum == settings.AWS_EXPECTED_MAX_SIZE
            )
            allowed = self._action_allowed(requested_action, desired, minimum, maximum)
            healthy = len(in_service_healthy) == len(all_instances) == desired
            result["target"] = {
                "region": self.region,
                "auto_scaling_group": group.get("AutoScalingGroupName"),
                "launch_template": group_template_name,
                "account_matches_expected": (
                    settings.AWS_EXPECTED_ACCOUNT_ID is not None
                    and str(identity.get("Account")) == str(settings.AWS_EXPECTED_ACCOUNT_ID)
                ),
                "matches_expected": target_matches,
            }
            result["capacity"] = {
                "current": len(in_service_healthy),
                "desired": desired,
                "minimum": minimum,
                "maximum": maximum,
                "expected_minimum": settings.AWS_EXPECTED_MIN_SIZE,
                "expected_maximum": settings.AWS_EXPECTED_MAX_SIZE,
                "requested_action": requested_action,
                "action_allowed": allowed,
            }
            result["health"] = {
                "healthy_instances": len(in_service_healthy),
                "total_instances": len(all_instances),
                "all_healthy": healthy,
                "instances": [
                    {"instance_id": item.get("InstanceId"), "lifecycle": item.get("LifecycleState"), "health": item.get("HealthStatus")}
                    for item in all_instances
                ],
            }
            result["in_progress_activities"] = activities
            result["permissions"] = {
                "read_only_preflight": "verified for sts:GetCallerIdentity, autoscaling:DescribeAutoScalingGroups, autoscaling:DescribeScalingActivities",
                "set_desired_capacity": (
                    "user/admin-confirmed by configuration; not independently verified by read-only API"
                    if settings.AWS_LIVE_SCALING_PERMISSION_CONFIRMED
                    else "not verified; AWS administrator confirmation required"
                ),
            }
            result["ready"] = target_matches and healthy and not activities and allowed
            if not target_matches:
                result["errors"].append("Configured target, launch template, or capacity bounds do not match expected values.")
            if not healthy:
                result["errors"].append("Not all desired instances are InService and Healthy.")
            if activities:
                result["errors"].append("A scaling activity is already in progress.")
            if not allowed:
                result["errors"].append("Configured bounds do not allow the requested action.")
        except Exception as exc:
            code = self._error_code(exc)
            logger.warning("AWS read-only preflight failed (%s).", code)
            result["errors"].append(code)
        return result

    def get_current_capacity(self) -> int:
        """Retrieves the current desired capacity of the ASG."""
        if self.mock_mode:
            return _mock_asg_state["desired_capacity"]

        try:
            return int(self._describe_group().get("DesiredCapacity", 1))
        except Exception as exc:
            logger.error("AWS ASG describe failed (%s); refusing to use simulated capacity.", self._error_code(exc))
            raise

    def set_desired_capacity(self, desired_capacity: int, honor_cooldown: bool = True, expected_action=None) -> Dict[str, Any]:
        """
        Adjusts the desired capacity of the AWS Auto Scaling Group.
        Safe mock mode simulates the change when running locally.
        """
        desired_capacity = int(desired_capacity)
        if self.mock_mode:
            if not _mock_asg_state["min_size"] <= desired_capacity <= _mock_asg_state["max_size"]:
                return {"success": False, "mode": "mock", "message": "Requested capacity is outside mock ASG bounds."}
            prev = _mock_asg_state["desired_capacity"]
            if expected_action == "scale_up" and desired_capacity <= prev:
                return {"success": False, "mode": "mock", "message": "Scale-up target must exceed current capacity."}
            if expected_action == "scale_down" and desired_capacity >= prev:
                return {"success": False, "mode": "mock", "message": "Scale-down target must be below current capacity."}
            _mock_asg_state["desired_capacity"] = desired_capacity
            msg = f"[MOCK AWS] ASG '{self.asg_name}' capacity updated: {prev} -> {desired_capacity} instances."
            logger.info(msg)
            return {
                "success": True,
                "mode": "mock",
                "previous_capacity": prev,
                "desired_capacity": desired_capacity,
                "message": msg
            }

        if not settings.AWS_LIVE_SCALING_ENABLED or not settings.AWS_LIVE_SCALING_PERMISSION_CONFIRMED:
            return {
                "success": False,
                "mode": "aws_boto3",
                "desired_capacity": desired_capacity,
                "message": "Live AWS scaling is disabled or write permission has not been confirmed.",
            }

        with self._mutation_lock:
            try:
                group = self._describe_group()
                current = int(group.get("DesiredCapacity", 0))
                minimum = int(group.get("MinSize", 0))
                maximum = int(group.get("MaxSize", 0))
                if not minimum <= desired_capacity <= maximum:
                    return {"success": False, "mode": "aws_boto3", "message": "Requested capacity is outside the configured ASG bounds."}
                if desired_capacity == current:
                    return {"success": False, "mode": "aws_boto3", "message": "Requested capacity already matches the ASG desired capacity."}
                if expected_action == "scale_up" and desired_capacity <= current:
                    return {"success": False, "mode": "aws_boto3", "message": "Scale-up target must exceed current capacity."}
                if expected_action == "scale_down" and desired_capacity >= current:
                    return {"success": False, "mode": "aws_boto3", "message": "Scale-down target must be below current capacity."}
                if self._active_activities():
                    return {"success": False, "mode": "aws_boto3", "message": "Another ASG scaling activity is in progress."}
                self._client.set_desired_capacity(
                    AutoScalingGroupName=self.asg_name,
                    DesiredCapacity=desired_capacity,
                    HonorCooldown=honor_cooldown,
                )
                msg = f"AWS accepted desired capacity {current} -> {desired_capacity} for ASG '{self.asg_name}'. Verify actual capacity and health with preflight."
                logger.info("AWS ASG action=%s result=accepted group=%s previous=%s desired=%s", expected_action or "unspecified", self.asg_name, current, desired_capacity)
                return {"success": True, "mode": "aws_boto3", "previous_capacity": current, "desired_capacity": desired_capacity, "message": msg}
            except Exception as exc:
                code = self._error_code(exc)
                logger.error("AWS ASG mutation failed action=%s group=%s error=%s", expected_action or "unspecified", self.asg_name, code)
                return {"success": False, "mode": "aws_boto3", "desired_capacity": desired_capacity, "error_code": code, "message": f"AWS request failed safely ({code})."}


aws_client = AWSAutoScalingClient()
