from .analysis import router as analysis_router
from .details import router as details_router
from .weekly_plans import router as weekly_plans_router
from .analysis_rag import router as analysis_rag_router
from .weekly_plans_rag import router as weekly_plans_rag_router

__all__ = [
    "analysis_router",
    "goals_router",
    "weekly_plans_router",
    "analysis_rag_router",
    "weekly_plans_rag_router"
]
# __all__ = ["analysis_router", "details_router", "weekly_plans_router"]
