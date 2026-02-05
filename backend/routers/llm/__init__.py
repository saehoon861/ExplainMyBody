from .analysis import router as analysis_router
from .details import router as details_router
from .weekly_plans import router as weekly_plans_router

__all__ = ["analysis_router", "details_router", "weekly_plans_router"]
