"""
API 라우터
"""

from .common import auth_router, users_router
from .ocr import health_records_router
from .llm import analysis_router, goals_router #, weekly_plans_router
# from .chatbot import router as chatbot_router

__all__ = [
    "auth_router",
    "users_router",
    "health_records_router",
    "analysis_router",
    "goals_router",
    # "weekly_plans_router",
    # "chatbot_router"
]
