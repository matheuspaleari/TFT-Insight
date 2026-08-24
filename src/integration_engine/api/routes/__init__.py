from .analysis import router as analysis_router
from .benchmark import router as benchmark_router
from .health import router as health_router
from .integrated_analysis import (
    router as integrated_analysis_router,
)

__all__ = [
    "analysis_router",
    "benchmark_router",
    "health_router",
    "integrated_analysis_router",
]
