import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


_backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_env_file_path = os.path.join(_backend_dir, ".env")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(_env_file_path, ".env"),
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
    SECRET_KEY: str = "super-secret-festival-key-change-in-production-2026"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    # AI / RL Integration
    AI_SERVICE_URL: str = ""
    AI_TIMEOUT_SECONDS: float = 3.0

    # AWS Auto Scaling Group Integration
    AWS_REGION: str = "ap-south-1"
    AWS_ASG_NAME: str = "ecommerce-festival-asg"
    AWS_MOCK_MODE: bool = True
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None

    def get_database_url(self) -> str:
        """
        Returns the active SQLAlchemy database URL.
        Falls back to local SQLite if USE_SQLITE is True or no RDS config is present.
        """
        if self.USE_SQLITE:
            if self.SQLITE_PATH == ":memory:":
                return "sqlite:///:memory:"
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            db_path = os.path.join(base_dir, self.SQLITE_PATH)
            return f"sqlite:///{db_path}"

        if self.DATABASE_URL:
            url = self.DATABASE_URL
            if url.startswith("postgres://"):
                url = url.replace("postgres://", "postgresql+psycopg2://", 1)
            elif url.startswith("postgresql://") and "+psycopg2" not in url:
                url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
            return url

        # Default RDS PostgreSQL connection string
        return (
            f"postgresql+psycopg2://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )


settings = Settings()
