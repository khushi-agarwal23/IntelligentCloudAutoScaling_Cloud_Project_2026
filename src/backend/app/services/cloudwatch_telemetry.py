
"""Read-only CloudWatch/ASG/ALB telemetry collector.
Never changes AWS resources.
"""
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from ..config import settings

logger = logging.getLogger(__name__)


class TelemetryUnavailable(RuntimeError):
    def __init__(self, code: str, message: str, diagnostics: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.code = code
        self.diagnostics = diagnostics or {}


class CloudWatchTelemetryClient:
    REQUIRED_METRICS = ("cpu_percent", "request_rate", "response_time_ms")

    def __init__(self, session=None):
        self._session = session

    def _get_session(self):
        if settings.AWS_MOCK_MODE:
            raise TelemetryUnavailable(
                "MockMode",
                "CloudWatch telemetry is disabled while AWS mock mode is enabled.",
            )

        if self._session is not None:
            return self._session

        try:
            import boto3

            kwargs = {"region_name": settings.AWS_REGION}
            if settings.AWS_PROFILE:
                kwargs["profile_name"] = settings.AWS_PROFILE

            self._session = boto3.Session(**kwargs)
            return self._session

        except Exception as exc:
            response = getattr(exc, "response", {}) or {}
            error_code = (
                (response.get("Error") or {}).get("Code")
                or exc.__class__.__name__
            )
            raise TelemetryUnavailable(
                str(error_code),
                "AWS credentials or SDK session could not be initialized.",
            ) from exc

    @staticmethod
    def _error_code(exc: Exception) -> str:
        response = getattr(exc, "response", {}) or {}
        return str(
            (response.get("Error") or {}).get("Code")
            or exc.__class__.__name__
        )

    @staticmethod
    def _latest(
        result: Dict[str, Any],
    ) -> Optional[tuple[datetime, float]]:
        points = list(
            zip(
                result.get("Timestamps", []),
                result.get("Values", []),
            )
        )

        if not points:
            return None

        timestamp, value = max(points, key=lambda pair: pair[0])
        return timestamp, float(value)

    def collect(self, now: Optional[datetime] = None) -> Dict[str, Any]:
        """Return recent measurements for the expected healthy ASG and ALB."""
        session = self._get_session()
        now = now or datetime.now(timezone.utc)

        period = max(60, int(settings.AWS_CLOUDWATCH_PERIOD_SECONDS))
        alb_period = 60

        try:
            sts = session.client("sts")
            autoscaling = session.client("autoscaling")
            elbv2 = session.client("elbv2")
            cloudwatch = session.client("cloudwatch")

            identity = sts.get_caller_identity()

            if not settings.AWS_EXPECTED_ACCOUNT_ID:
                raise TelemetryUnavailable(
                    "ExpectedAccountNotConfigured",
                    "Set AWS_EXPECTED_ACCOUNT_ID after verifying the intended AWS account.",
                )

            if str(identity.get("Account")) != str(
                settings.AWS_EXPECTED_ACCOUNT_ID
            ):
                raise TelemetryUnavailable(
                    "WrongAwsAccount",
                    "Authenticated AWS account does not match the configured expected account.",
                )

            groups = autoscaling.describe_auto_scaling_groups(
                AutoScalingGroupNames=[settings.AWS_ASG_NAME]
            ).get("AutoScalingGroups", [])

            if len(groups) != 1:
                raise TelemetryUnavailable(
                    "AutoScalingGroupNotFound",
                    "Expected exactly one configured Auto Scaling Group.",
                )

            group = groups[0]
            template = group.get("LaunchTemplate") or {}
            template_name = template.get("LaunchTemplateName")
            desired = int(group.get("DesiredCapacity", 0))
            minimum = int(group.get("MinSize", 0))
            maximum = int(group.get("MaxSize", 0))

            if group.get("AutoScalingGroupName") != settings.AWS_ASG_NAME:
                raise TelemetryUnavailable(
                    "AutoScalingGroupMismatch",
                    "AWS returned a different Auto Scaling Group.",
                )

            if template_name != settings.AWS_EXPECTED_LAUNCH_TEMPLATE:
                raise TelemetryUnavailable(
                    "LaunchTemplateMismatch",
                    "Auto Scaling Group launch template does not match the configured target.",
                )

            if (minimum, maximum) != (
                settings.AWS_EXPECTED_MIN_SIZE,
                settings.AWS_EXPECTED_MAX_SIZE,
            ):
                raise TelemetryUnavailable(
                    "CapacityBoundsMismatch",
                    "Auto Scaling Group bounds do not match the configured safety bounds.",
                )

            healthy = [
                instance
                for instance in group.get("Instances", [])
                if instance.get("LifecycleState") == "InService"
                and instance.get("HealthStatus") == "Healthy"
            ]

            if (
                not healthy
                or len(healthy) != desired
                or not minimum <= desired <= maximum
            ):
                raise TelemetryUnavailable(
                    "AsgNotHealthy",
                    "Current healthy InService instance count does not match desired capacity or configured bounds.",
                )

            lbs = elbv2.describe_load_balancers(
                Names=[settings.AWS_ALB_NAME]
            ).get("LoadBalancers", [])

            if (
                len(lbs) != 1
                or lbs[0].get("State", {}).get("Code") != "active"
            ):
                raise TelemetryUnavailable(
                    "LoadBalancerUnavailable",
                    "Expected ALB is missing or not active.",
                )

            targets = elbv2.describe_target_groups(
                Names=[settings.AWS_TARGET_GROUP_NAME]
            ).get("TargetGroups", [])

            if (
                len(targets) != 1
                or lbs[0]["LoadBalancerArn"]
                not in targets[0].get("LoadBalancerArns", [])
            ):
                raise TelemetryUnavailable(
                    "TargetGroupMismatch",
                    "Expected target group is missing or not attached to the expected ALB.",
                )

            if targets[0].get("TargetType", "instance") != "instance":
                raise TelemetryUnavailable(
                    "TargetTypeMismatch",
                    "Expected target group must register EC2 instance IDs for ASG health verification.",
                )

            target_group_arn = targets[0]["TargetGroupArn"]

            target_health = elbv2.describe_target_health(
                TargetGroupArn=target_group_arn
            ).get("TargetHealthDescriptions", [])

            healthy_targets = [
                item
                for item in target_health
                if item.get("TargetHealth", {}).get("State") == "healthy"
            ]

            asg_instance_ids = {
                item["InstanceId"] for item in healthy
            }
            target_instance_ids = {
                item.get("Target", {}).get("Id")
                for item in healthy_targets
            }

            if target_instance_ids != asg_instance_ids:
                raise TelemetryUnavailable(
                    "TargetHealthMismatch",
                    "Healthy ALB target instance IDs do not exactly match the healthy ASG instance IDs.",
                    diagnostics={
                        "load_balancer_arn": lbs[0]["LoadBalancerArn"],
                        "target_group_arn": target_group_arn,
                        "target_group_load_balancer_arns": targets[0].get("LoadBalancerArns", []),
                        "asg_healthy_instance_ids": sorted(asg_instance_ids),
                        "alb_healthy_target_ids": sorted(
                            (instance_id for instance_id in target_instance_ids if instance_id is not None)
                        ),
                        "asg_only_healthy_ids": sorted(asg_instance_ids - target_instance_ids),
                        "alb_only_healthy_ids": sorted(
                            target_instance_ids - asg_instance_ids,
                            key=lambda instance_id: "" if instance_id is None else instance_id,
                        ),
                        "asg_instances": [
                            {
                                "instance_id": instance.get("InstanceId"),
                                "lifecycle_state": instance.get("LifecycleState"),
                                "asg_health_status": instance.get("HealthStatus"),
                            }
                            for instance in group.get("Instances", [])
                        ],
                        "alb_targets": [
                            {
                                "instance_id": item.get("Target", {}).get("Id"),
                                "port": item.get("Target", {}).get("Port"),
                                "state": item.get("TargetHealth", {}).get("State"),
                                "reason": item.get("TargetHealth", {}).get("Reason"),
                                "description": item.get("TargetHealth", {}).get("Description"),
                            }
                            for item in target_health
                        ],
                    },
                )

            lb_dimension = lbs[0]["LoadBalancerArn"].split(
                ":loadbalancer/", 1
            )[-1]
            # CloudWatch's TargetGroup dimension value includes the literal
            # "targetgroup/" resource prefix from the ARN.
            tg_dimension = target_group_arn.rsplit(":", 1)[-1]

            queries = []

            # EC2 CPU and memory metrics.
            for index, instance in enumerate(healthy):
                instance_id = instance["InstanceId"]

                queries.append(
                    self._query(
                        f"cpu{index}",
                        "AWS/EC2",
                        "CPUUtilization",
                        [{"Name": "InstanceId", "Value": instance_id}],
                        "Average",
                        period,
                    )
                )

                queries.append(
                    self._query(
                        f"mem{index}",
                        "CWAgent",
                        "mem_used_percent",
                        [{"Name": "InstanceId", "Value": instance_id}],
                        "Average",
                        period,
                    )
                )

            # ALB metrics use a 60-second period.
            queries.extend([
                self._query(
                    "requests",
                    "AWS/ApplicationELB",
                    "RequestCount",
                    [{"Name": "LoadBalancer", "Value": lb_dimension}],
                    "Sum",
                    alb_period,
                ),
                self._query(
                    "latency",
                    "AWS/ApplicationELB",
                    "TargetResponseTime",
                    [
                        {"Name": "LoadBalancer", "Value": lb_dimension},
                        {"Name": "TargetGroup", "Value": tg_dimension},
                    ],
                    "Average",
                    alb_period,
                ),
                self._query(
                    "errors",
                    "AWS/ApplicationELB",
                    "HTTPCode_Target_5XX_Count",
                    [
                        {"Name": "LoadBalancer", "Value": lb_dimension},
                        {"Name": "TargetGroup", "Value": tg_dimension},
                    ],
                    "Sum",
                    alb_period,
                ),
            ])

            # Use completed minute boundaries and a three-hour history window.
            now_utc = now.astimezone(timezone.utc)
            end_time = now_utc.replace(second=0, microsecond=0)
            start_time = end_time - timedelta(hours=3)

            response = cloudwatch.get_metric_data(
                MetricDataQueries=queries,
                StartTime=start_time,
                EndTime=end_time,
                ScanBy="TimestampDescending",
            )

            data = {
                item["Id"]: item
                for item in response.get("MetricDataResults", [])
            }
            max_age = int(settings.AWS_CLOUDWATCH_MAX_AGE_SECONDS)

            def point(metric_id: str, required: bool = True):
                found = self._latest(data.get(metric_id, {}))

                if found is None:
                    if required:
                        raise TelemetryUnavailable(
                            "CloudWatchMetricMissing",
                            f"Required CloudWatch metric {metric_id} has no datapoint in the collection window.",
                        )
                    return None

                timestamp, value = found

                if timestamp.tzinfo is None:
                    timestamp = timestamp.replace(tzinfo=timezone.utc)

                age = (now_utc - timestamp.astimezone(timezone.utc)).total_seconds()

                if age < -60 or age > max_age:
                    logger.warning(
                        "CloudWatch metric failed freshness validation: metric_id=%s "
                        "timestamp_utc=%s now_utc=%s age_seconds=%.1f "
                        "max_age_seconds=%s query_start_utc=%s query_end_utc=%s",
                        metric_id,
                        timestamp.astimezone(timezone.utc).isoformat(),
                        now_utc.isoformat(),
                        age,
                        max_age,
                        start_time.isoformat(),
                        end_time.isoformat(),
                    )
                    if required:
                        raise TelemetryUnavailable(
                            "CloudWatchMetricStale",
                            f"Required CloudWatch metric {metric_id} is outside the freshness limit.",
                        )
                    return None

                return {
                    "timestamp": timestamp.astimezone(timezone.utc).isoformat(),
                    "value": value,
                    "age_seconds": round(max(0.0, age), 1),
                }

            cpu_points = [
                point(f"cpu{index}")
                for index in range(len(healthy))
            ]
            memory_points = [
                point(f"mem{index}", required=False)
                for index in range(len(healthy))
            ]

            request_point = point("requests")
            latency_point = point("latency")
            error_point = point("errors", required=False)

            request_rate = request_point["value"] / alb_period

            error_rate = (
                error_point["value"] / request_point["value"] * 100.0
                if error_point and request_point["value"] > 0
                else 0.0
            )

            memory_values = [
                item["value"]
                for item in memory_points
                if item
            ]

            metrics = {
                "cpu_percent": (
                    sum(item["value"] for item in cpu_points)
                    / len(cpu_points)
                ),
                "memory_percent": (
                    sum(memory_values) / len(memory_values)
                    if len(memory_values) == len(healthy)
                    else None
                ),
                "request_rate": request_rate,
                "response_time_ms": latency_point["value"] * 1000.0,
                "error_rate": error_rate,
                "current_instances": desired,
                "minimum": minimum,
                "maximum": maximum,
                "desired_instances": desired,
            }

            provenance = {
                "source": "aws_cloudwatch",
                "simulated": False,
                "region": settings.AWS_REGION,
                "asg": settings.AWS_ASG_NAME,
                "alb": settings.AWS_ALB_NAME,
                "target_group": settings.AWS_TARGET_GROUP_NAME,
                "period_seconds": period,
                "alb_period_seconds": alb_period,
                "cloudwatch": {
                    "cpu_per_instance": cpu_points,
                    "memory_per_instance": memory_points,
                    "request_count": request_point,
                    "target_response_time_seconds": latency_point,
                    "target_5xx_count": error_point,
                },
                "memory_available": len(memory_values) == len(healthy),
                "error_rate_note": (
                    "No 5xx datapoint in a window with observed requests is interpreted as zero errors."
                    if error_point is None
                    else "Derived from target 5xx count divided by ALB request count."
                ),
            }

            return {
                "ready": True,
                "metrics": metrics,
                "provenance": provenance,
            }

        except TelemetryUnavailable:
            raise

        except Exception as exc:
            code = self._error_code(exc)
            raise TelemetryUnavailable(
                code,
                "Read-only AWS telemetry collection failed; no scaling action was attempted.",
            ) from exc

    @staticmethod
    def _query(
        metric_id,
        namespace,
        metric_name,
        dimensions,
        statistic,
        period,
    ):
        return {
            "Id": metric_id,
            "MetricStat": {
                "Metric": {
                    "Namespace": namespace,
                    "MetricName": metric_name,
                    "Dimensions": dimensions,
                },
                "Period": period,
                "Stat": statistic,
            },
            "ReturnData": True,
        }


cloudwatch_telemetry = CloudWatchTelemetryClient()
