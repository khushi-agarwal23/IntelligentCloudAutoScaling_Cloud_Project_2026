from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..database import get_db, engine
from ..config import settings

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("")
def health_check():
    """Basic health check endpoint."""
    return {
        "status": "ok",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT
    }


@router.get("/db")
def db_health_check(db: Session = Depends(get_db)):
    """Validates connectivity to Amazon RDS / SQLite database."""
    try:
        db.execute(text("SELECT 1"))
        pool = engine.pool
        pool_status = {
            "size": pool.size() if hasattr(pool, "size") else "static",
            "checked_in": pool.checkedin() if hasattr(pool, "checkedin") else "N/A",
            "checked_out": pool.checkedout() if hasattr(pool, "checkedout") else "N/A",
            "overflow": pool.overflow() if hasattr(pool, "overflow") else "N/A",
        }
        return {
            "status": "connected",
            "database_dialect": engine.dialect.name,
            "connection_pool": pool_status
        }
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Database connection failed: {str(exc)}"
        )
