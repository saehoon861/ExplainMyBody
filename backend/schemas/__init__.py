"""
Pydantic 스키마
"""

from .user import UserCreate, UserResponse, UserLogin
from .health_record import HealthRecordCreate, HealthRecordResponse, HealthRecordUpdate
from .analysis_report import AnalysisReportCreate, AnalysisReportResponse
from .user_goal import UserGoalCreate, UserGoalResponse, UserGoalUpdate
from .llm_input import (
    StatusAnalysisInput,
    GoalPlanInput,
    StatusAnalysisResponse,
    GoalPlanResponse,
    GoalPlanRequest
)

__all__ = [
    "UserCreate", "UserResponse", "UserLogin",
    "HealthRecordCreate", "HealthRecordResponse", "HealthRecordUpdate",
    "AnalysisReportCreate", "AnalysisReportResponse",
    "UserGoalCreate", "UserGoalResponse", "UserGoalUpdate",
    "StatusAnalysisInput", "GoalPlanInput",
    "StatusAnalysisResponse", "GoalPlanResponse", "GoalPlanRequest"
]
