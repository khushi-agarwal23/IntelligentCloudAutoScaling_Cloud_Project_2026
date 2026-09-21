from .health import router as health_router
from .auth import router as auth_router
from .transactions import router as transactions_router
from .workload import router as workload_router
from .scaling import router as scaling_router

__all__ = [
    "health_router",
    "auth_router",
    "transactions_router",
    "workload_router",
    "scaling_router",
]
