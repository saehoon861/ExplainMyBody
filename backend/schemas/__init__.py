"""
Pydantic Schemas

팀 분담:
- common.py: 공통 팀 전담 (User, HealthRecord)
- llm.py: LLM 팀 전담 (InbodyAnalysisReport, UserDetail, WeeklyPlan, LLM 입출력)
- inbody.py: OCR 팀 전담 (InBodyData)
- body_type.py: OCR 팀 전담 (BodyTypeAnalysis)
"""

from .common import (
    UserCreate, UserResponse, UserLogin, UserSignupRequest, EmailCheckRequest,
    HealthRecordCreate, HealthRecordResponse, HealthRecordUpdate
)

from .llm import (
    # InbodyAnalysisReport
    AnalysisReportCreate, AnalysisReportResponse,
    # UserDetail (구 UserGoal)
    UserDetailCreate, UserDetailResponse, UserDetailUpdate,
    # WeeklyPlan
    WeeklyPlanCreate, WeeklyPlanResponse, WeeklyPlanUpdate,
    # LLM Input/Output
    StatusAnalysisInput, StatusAnalysisResponse,
    GoalPlanInput, GoalPlanResponse, GoalPlanRequest,
    # Chat
    AnalysisChatRequest, AnalysisChatResponse
)

from .inbody import InBodyData
from .body_type import BodyTypeAnalysisInput, BodyTypeAnalysisOutput
from .temp_goal_update import UserGoalUpdateRequest

__all__ = [
    # User
    "UserCreate", "UserResponse", "UserLogin", "UserSignupRequest", "EmailCheckRequest",
    # HealthRecord
    "HealthRecordCreate", "HealthRecordResponse", "HealthRecordUpdate",
    # InbodyAnalysisReport
    "AnalysisReportCreate", "AnalysisReportResponse",
    # UserDetail
    "UserDetailCreate", "UserDetailResponse", "UserDetailUpdate",
    # WeeklyPlan
    "WeeklyPlanCreate", "WeeklyPlanResponse", "WeeklyPlanUpdate",
    # LLM
    "StatusAnalysisInput", "StatusAnalysisResponse",
    "GoalPlanInput", "GoalPlanResponse", "GoalPlanRequest",
    "AnalysisChatRequest", "AnalysisChatResponse",
    # Goal Update
    "UserGoalUpdateRequest",
    # InBody
    "InBodyData",
    # BodyType
    "BodyTypeAnalysisInput", "BodyTypeAnalysisOutput"
]
