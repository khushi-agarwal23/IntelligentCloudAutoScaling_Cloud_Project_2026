from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .database import init_db
from .routers import (
    health_router,
    auth_router,
    transactions_router,
    workload_router,
    scaling_router,
)
from .utils.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for application startup and shutdown."""
    logger.info("Starting up %s v%s...", settings.PROJECT_NAME, settings.VERSION)
    # Initialize database tables on startup
    init_db()
    yield
    logger.info("Shutting down %s...", settings.PROJECT_NAME)


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="High-Performance Backend for Intelligent Cloud Auto-Scaling during E-Commerce Festival Sales.",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure Cross-Origin Resource Sharing (CORS) for Khushi's Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register v1 API Routers
api_v1_prefix = settings.API_V1_STR
app.include_router(health_router, prefix=api_v1_prefix)
app.include_router(auth_router, prefix=api_v1_prefix)
app.include_router(transactions_router, prefix=api_v1_prefix)
app.include_router(workload_router, prefix=api_v1_prefix)
app.include_router(scaling_router, prefix=api_v1_prefix)

# Also mount under /api for backward compatibility
app.include_router(health_router, prefix="/api")
app.include_router(auth_router, prefix="/api")
app.include_router(transactions_router, prefix="/api")
app.include_router(workload_router, prefix="/api")
app.include_router(scaling_router, prefix="/api")


@app.get("/")
def root():
    return {
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs": "/docs",
        "health": f"{api_v1_prefix}/health",
        "environment": settings.ENVIRONMENT
    }
