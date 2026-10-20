import os
from pathlib import Path
from typing import Optional
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# Resolve the backend dotenv file from this module, not from the process's
# current working directory. Environment variables still take precedence.
BACKEND_ENV_FILE = Path(__file__).resolve().parent.parent / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_ENV_FILE,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    PROJECT_NAME: str = "Intelligent Cloud Auto-Scaling Backend"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False

    # Database Configuration (Amazon RDS / SQLite)
    USE_SQLITE: bool = True
    SQLITE_PATH: str = "cloud_autoscaling.db"
    DATABASE_URL: Optional[str] = None

    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "ecommerce_db"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = ""
    DB_SSL_MODE: str = "disable"  # "require", "verify-ca", "verify-full", or "disable"

    # Connection Pooling (tuned for festival-sale high concurrency)
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 30
    DB_POOL_PRE_PING: bool = True
    DB_POOL_RECYCLE: int = 1800
    DB_POOL_TIMEOUT: int = 30

    # JWT & Security
    SECRET_KEY: str = "development-only-insecure-key-change-before-deploy"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    CORS_ALLOWED_ORIGINS: str = "http://127.0.0.1:5500,http://localhost:5500"

    # AI / RL Integration
    AI_SERVICE_URL: str = ""
    AI_TIMEOUT_SECONDS: float = 3.0
    # Preserve the existing Q-learning policy as default. PPO is an explicit
    # offline/simulation candidate until deployment compatibility is approved.
    SCALING_POLICY: str = "q_learning"
    PPO_MODEL_PATH: Optional[str] = None

    # AWS Auto Scaling Group Integration
    AWS_REGION: str = "ap-south-1"
    AWS_ASG_NAME: str = "rl-autoscaling-group"
    # Keep local development and automated tests in mock mode by default.
    AWS_MOCK_MODE: bool = True
    AWS_LIVE_SCALING_ENABLED: bool = False
    AWS_LIVE_SCALING_PERMISSION_CONFIRMED: bool = False
    AWS_PROFILE: Optional[str] = None
    AWS_EXPECTED_ACCOUNT_ID: Optional[str] = None
    AWS_EXPECTED_LAUNCH_TEMPLATE: str = "autoscaling-launch-template"
    AWS_EXPECTED_MIN_SIZE: int = 1
    AWS_EXPECTED_MAX_SIZE: int = 3
    AWS_ALB_NAME: str = "autoscaling-alb"
    AWS_TARGET_GROUP_NAME: str = "rl-target-group"
    AWS_CLOUDWATCH_PERIOD_SECONDS: int = 300
    AWS_CLOUDWATCH_MAX_AGE_SECONDS: int = 900
    AWS_SCALING_COOLDOWN_SECONDS: int = 300

    # Workload replay callback. Secret is injected at runtime; never commit it.
    WORKLOAD_REPLAY_HMAC_SECRET: Optional[str] = None
    WORKLOAD_REPLAY_MAX_SKEW_SECONDS: int = 300
    WORKLOAD_REPLAY_ALLOW_LIVE_SCALING: bool = False

    @model_validator(mode="after")
    def require_production_secret(self):
        if self.ENVIRONMENT.strip().lower() in {"production", "prod"}:
            if not self.SECRET_KEY or self.SECRET_KEY == "development-only-insecure-key-change-before-deploy":
                raise ValueError("Set SECRET_KEY to a unique secret before using production mode.")
        return self

    def get_database_url(self) -> str:
        """
        Returns the active SQLAlchemy database URL.
        Falls back to local SQLite if USE_SQLITE is True or no RDS config is present.
        """
        if self.DATABASE_URL:
            url = self.DATABASE_URL
            if url.startswith("postgres://"):
                url = url.replace("postgres://", "postgresql+psycopg2://", 1)
            elif url.startswith("postgresql://") and "+psycopg2" not in url:
                url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
            return url

        if self.USE_SQLITE:
            if self.SQLITE_PATH == ":memory:":
                return "sqlite:///:memory:"
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            db_path = os.path.join(base_dir, self.SQLITE_PATH)
            return f"sqlite:///{db_path}"

        # Default RDS PostgreSQL connection string
        return (
            f"postgresql+psycopg2://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )


settings = Settings()
