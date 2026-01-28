"""
Pydantic 스키마

팀 담당 기준 분류:
- common.py: 공통 스키마 (User, HealthRecord)
- llm.py: LLM 팀 전담 (AnalysisReport, UserGoal, LLM 입출력)
- inbody.py: OCR 팀 전담 (InBody 데이터 검증)
- body_type.py: OCR 팀 전담 (체형 분석)
"""

# 공통 스키마 (양 팀 모두 사용)
from .common import (
    UserCreate, UserResponse, UserLogin,
    HealthRecordCreate, HealthRecordResponse, HealthRecordUpdate
)

# LLM 팀 전담 스키마
from .llm import (
    # AnalysisReport
    AnalysisReportCreate, AnalysisReportResponse,
    # UserGoal
    UserGoalCreate, UserGoalResponse, UserGoalUpdate,
    # LLM 입출력
    StatusAnalysisInput, StatusAnalysisResponse,
    GoalPlanInput, GoalPlanResponse, GoalPlanRequest
)

# OCR 팀 전담 스키마
from .inbody import InBodyData
from .body_type import BodyTypeAnalysisInput, BodyTypeAnalysisOutput

__all__ = [
    # Common
    "UserCreate", "UserResponse", "UserLogin",
    "HealthRecordCreate", "HealthRecordResponse", "HealthRecordUpdate",
    # LLM Team
    "AnalysisReportCreate", "AnalysisReportResponse",
    "UserGoalCreate", "UserGoalResponse", "UserGoalUpdate",
    "StatusAnalysisInput", "StatusAnalysisResponse",
    "GoalPlanInput", "GoalPlanResponse", "GoalPlanRequest",
    # OCR Team
    "InBodyData", "BodyTypeAnalysisInput", "BodyTypeAnalysisOutput"
]
