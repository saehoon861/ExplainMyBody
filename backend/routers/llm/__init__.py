from .analysis import router as analysis_router
from .goals import router as goals_router
from .weekly_plans import router as weekly_plans_router

__all__ = ["analysis_router", "goals_router", "weekly_plans_router"]
