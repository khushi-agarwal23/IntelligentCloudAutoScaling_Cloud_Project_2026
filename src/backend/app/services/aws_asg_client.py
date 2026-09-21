import logging
from typing import Dict, Any
from ..config import settings

logger = logging.getLogger("backend.services.aws_asg_client")

# In-memory mock state for local testing without AWS credentials
_mock_asg_state = {
    "desired_capacity": 2,
    "min_size": 1,
    "max_size": 10,
    "name": settings.AWS_ASG_NAME
}


class AWSAutoScalingClient:
    def __init__(self):
        self.mock_mode = settings.AWS_MOCK_MODE or not (settings.AWS_ACCESS_KEY_ID or settings.AWS_SECRET_ACCESS_KEY)
        self.region = settings.AWS_REGION
        self.asg_name = settings.AWS_ASG_NAME
        self._client = None

        if not self.mock_mode:
            try:
                import boto3
                kwargs = {"region_name": self.region}
                if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
                    kwargs["aws_access_key_id"] = settings.AWS_ACCESS_KEY_ID
                    kwargs["aws_secret_access_key"] = settings.AWS_SECRET_ACCESS_KEY
                self._client = boto3.client("autoscaling", **kwargs)
                logger.info("Connected to AWS Auto Scaling service in region %s", self.region)
            except Exception as exc:
                logger.warning("Boto3 AWS ASG client initialization failed (%s). Falling back to mock mode.", exc)
                self.mock_mode = True

    def get_current_capacity(self) -> int:
        """Retrieves the current desired capacity of the ASG."""
        if self.mock_mode:
            return _mock_asg_state["desired_capacity"]

        try:
            response = self._client.describe_auto_scaling_groups(
                AutoScalingGroupNames=[self.asg_name]
            )
            groups = response.get("AutoScalingGroups", [])
            if groups:
                return groups[0].get("DesiredCapacity", 1)
            return 1
        except Exception as exc:
            logger.error("AWS ASG describe failed: %s. Using mock fallback.", exc)
            return _mock_asg_state["desired_capacity"]

    def set_desired_capacity(self, desired_capacity: int, honor_cooldown: bool = False) -> Dict[str, Any]:
        """
        Adjusts the desired capacity of the AWS Auto Scaling Group.
        Safe mock mode simulates the change when running locally.
        """
        if self.mock_mode:
            prev = _mock_asg_state["desired_capacity"]
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

        try:
            self._client.set_desired_capacity(
                AutoScalingGroupName=self.asg_name,
                DesiredCapacity=desired_capacity,
                HonorCooldown=honor_cooldown
            )
            msg = f"AWS ASG '{self.asg_name}' capacity updated to {desired_capacity} instances."
            logger.info(msg)
            return {
                "success": True,
                "mode": "aws_boto3",
                "desired_capacity": desired_capacity,
                "message": msg
            }
        except Exception as exc:
            err_msg = f"Failed to update AWS ASG capacity: {exc}"
            logger.error(err_msg)
            return {
                "success": False,
                "mode": "aws_boto3",
                "desired_capacity": desired_capacity,
                "message": err_msg
            }


aws_client = AWSAutoScalingClient()
