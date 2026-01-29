"""
Pydantic Schemas

팀 분담:
- common.py: 공통 팀 전담 (User, HealthRecord)
- llm.py: LLM 팀 전담 (InbodyAnalysisReport, UserDetail, WeeklyPlan, LLM 입출력)
- inbody.py: OCR 팀 전담 (InBodyData)
- body_type.py: OCR 팀 전담 (BodyTypeAnalysis)
"""

from .common import (
    UserCreate, UserResponse, UserLogin,
    HealthRecordCreate, HealthRecordResponse
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
    GoalPlanInput, GoalPlanResponse, GoalPlanRequest
)

from .inbody import InBodyData
from .body_type import BodyTypeAnalysisInput, BodyTypeAnalysisOutput

__all__ = [
    # User
    "UserCreate", "UserResponse", "UserLogin",
    # HealthRecord
    "HealthRecordCreate", "HealthRecordResponse",
    # InbodyAnalysisReport
    "AnalysisReportCreate", "AnalysisReportResponse",
    # UserDetail
    "UserDetailCreate", "UserDetailResponse", "UserDetailUpdate",
    # WeeklyPlan
    "WeeklyPlanCreate", "WeeklyPlanResponse", "WeeklyPlanUpdate",
    # LLM
    "StatusAnalysisInput", "StatusAnalysisResponse",
    "GoalPlanInput", "GoalPlanResponse", "GoalPlanRequest",
    # InBody
    "InBodyData",
    # BodyType
    "BodyTypeAnalysisInput", "BodyTypeAnalysisOutput"
]
