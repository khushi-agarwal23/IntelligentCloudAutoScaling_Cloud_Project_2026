import sys
import os
import argparse

# Ensure src/backend is on the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine, Base
from app.models import User, Transaction, WorkloadMetric, ScalingDecision
from app.config import settings


def init_database(drop_first: bool = False):
    print("=" * 60)
    print("Intelligent Cloud Auto-Scaling: Database Initializer")
    print("=" * 60)
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
