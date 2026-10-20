import logging
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import StaticPool, QueuePool
from .config import settings

logger = logging.getLogger("backend.database")


class Base(DeclarativeBase):
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
    connect_args["connect_timeout"] = 10
    if settings.DB_SSL_MODE and settings.DB_SSL_MODE != "disable":
        if "postgresql" in db_url:
            connect_args["sslmode"] = settings.DB_SSL_MODE
        elif "mysql" in db_url:
            connect_args["ssl"] = {"ssl_mode": settings.DB_SSL_MODE}
    pool_kwargs.update(
        poolclass=QueuePool,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_pre_ping=settings.DB_POOL_PRE_PING,
        pool_recycle=settings.DB_POOL_RECYCLE,
        pool_timeout=settings.DB_POOL_TIMEOUT,
    )

engine = create_engine(db_url, connect_args=connect_args, **pool_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def migrate_additive_columns():
    """Add provenance/audit columns without replacing existing user data."""
    additions = {
        "workload_metrics": {
            "telemetry_source": "VARCHAR(32) NOT NULL DEFAULT 'manual_simulated'",
            "source_event_id": "VARCHAR(128) NULL",
            "data_provenance": "TEXT NULL",
        },
        "scaling_decisions": {
            "telemetry_source": "VARCHAR(32) NOT NULL DEFAULT 'manual_simulated'",
            "event_id": "VARCHAR(128) NULL",
            "aws_applied": "BOOLEAN NOT NULL DEFAULT FALSE",
            "aws_result": "TEXT NULL",
            "data_provenance": "TEXT NULL",
        },
    }
    with engine.begin() as connection:
        inspector = inspect(connection)
        for table_name, columns in additions.items():
            if not inspector.has_table(table_name):
                continue
            present = {column["name"] for column in inspector.get_columns(table_name)}
            for column_name, ddl_type in columns.items():
                if column_name not in present:
                    connection.exec_driver_sql(
                        f"ALTER TABLE {table_name} ADD COLUMN {column_name} {ddl_type}"
                    )
                    logger.info("Added audit column %s.%s", table_name, column_name)
                    present.add(column_name)


def init_db():
    """Create new tables, then add backward-compatible metadata columns."""
    from . import models  # noqa: F401
    logger.info("Initializing database schema on %s...", db_url.split("@")[-1])
    Base.metadata.create_all(bind=engine)
    migrate_additive_columns()
    logger.info("Database schema initialized successfully.")
