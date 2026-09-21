import sys
import os
import argparse
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Ensure src/backend is on the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings


def ensure_postgres_database_exists():
    """If using RDS PostgreSQL, connects to default 'postgres' DB and creates the target DB if missing."""
    if settings.USE_SQLITE:
        return

    db_url = settings.get_database_url()
    if "postgresql" not in db_url:
        return

    target_db = settings.DB_NAME
    if not target_db or target_db == "postgres":
        return

    try:
        print(f"[*] Checking if database '{target_db}' exists on RDS host {settings.DB_HOST}...")
        conn = psycopg2.connect(
            dbname="postgres",
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            sslmode=settings.DB_SSL_MODE
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        cursor.execute(f"SELECT 1 FROM pg_catalog.pg_database WHERE datname = '{target_db}'")
        exists = cursor.fetchone()
        if not exists:
            print(f"[+] Database '{target_db}' not found. Creating it now on Amazon RDS...")
            cursor.execute(f'CREATE DATABASE "{target_db}"')
            print(f"[SUCCESS] Database '{target_db}' created successfully!")
        else:
            print(f"[+] Database '{target_db}' already exists.")
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"[!] Note on DB creation check: {e}")


def init_database(drop_first: bool = False):
    print("=" * 60)
    print("Intelligent Cloud Auto-Scaling: Database Initializer")
    print("=" * 60)

    # First ensure DB exists
    ensure_postgres_database_exists()

    # Import engine & models after DB exists
    from app.database import engine, Base
    import app.models  # noqa

    print(f"Target DB Dialect : {engine.dialect.name}")
    db_target = settings.get_database_url()
    safe_target = db_target.split("@")[-1] if "@" in db_target else db_target
    print(f"Target Endpoint   : {safe_target}")

    if drop_first:
        print("[!] Dropping all existing tables...")
        Base.metadata.drop_all(bind=engine)
        print("[+] Tables successfully dropped.")

    print("[*] Creating database schema tables...")
    Base.metadata.create_all(bind=engine)
    print("[+] Created tables:")
    for table_name in Base.metadata.tables.keys():
        print(f"    - {table_name}")

    print("=" * 60)
    print("[SUCCESS] Database initialization complete!")
    print("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Initialize database tables for Amazon RDS or SQLite.")
    parser.add_argument("--drop", action="store_true", help="Drop all existing tables before recreating")
    args = parser.parse_args()

    init_database(drop_first=args.drop)
