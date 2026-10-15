import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import StaticPool, QueuePool
from .config import settings

logger = logging.getLogger("backend.database")


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy declarative models."""
    pass


db_url = settings.get_database_url()
is_sqlite = db_url.startswith("sqlite")

connect_args = {}
pool_kwargs = {}

if is_sqlite:
    connect_args["check_same_thread"] = False
    if ":memory:" in db_url:
        pool_kwargs["poolclass"] = StaticPool
else:
    # Amazon RDS PostgreSQL / MySQL connection parameters
    connect_args["connect_timeout"] = 10
    if settings.DB_SSL_MODE and settings.DB_SSL_MODE != "disable":
        if "postgresql" in db_url:
            connect_args["sslmode"] = settings.DB_SSL_MODE
        elif "mysql" in db_url:
            connect_args["ssl"] = {"ssl_mode": settings.DB_SSL_MODE}

    pool_kwargs["poolclass"] = QueuePool
    pool_kwargs["pool_size"] = settings.DB_POOL_SIZE
    pool_kwargs["max_overflow"] = settings.DB_MAX_OVERFLOW
    pool_kwargs["pool_pre_ping"] = settings.DB_POOL_PRE_PING
    pool_kwargs["pool_recycle"] = settings.DB_POOL_RECYCLE
    pool_kwargs["pool_timeout"] = settings.DB_POOL_TIMEOUT

engine = create_engine(
    db_url,
    connect_args=connect_args,
    **pool_kwargs
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False
)


def get_db():
    """FastAPI dependency for yielding database sessions per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initializes database schema and registers all models."""
    from . import models  # noqa: F401
    logger.info("Initializing database schema on %s...", db_url.split("@")[-1])
    Base.metadata.create_all(bind=engine)
    logger.info("Database schema initialized successfully.")
