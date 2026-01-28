"""
LLM Schemas - LLM 팀원 전담
AnalysisReport, UserGoal, LLM 입출력 (상태 분석 + 주간 계획) 관련 모든 스키마
"""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any


# ============================================================================
# AnalysisReport Schemas
# ============================================================================

class AnalysisReportBase(BaseModel):
    """분석 리포트 기본 스키마"""
    llm_output: str
    model_version: Optional[str] = None
    analysis_type: Optional[str] = None  # "status_analysis" 또는 "goal_plan"


class AnalysisReportCreate(AnalysisReportBase):
    """분석 리포트 생성 요청 스키마"""
    record_id: int


class AnalysisReportResponse(AnalysisReportBase):
    """분석 리포트 응답 스키마"""
    id: int
    user_id: int
    record_id: int
    generated_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# UserGoal Schemas
# ============================================================================

class UserGoalBase(BaseModel):
    """사용자 목표 기본 스키마"""
    goal_type: Optional[str] = None
    goal_description: Optional[str] = None


class UserGoalCreate(UserGoalBase):
    """사용자 목표 생성 요청 스키마"""
    pass


class UserGoalUpdate(BaseModel):
    """사용자 목표 수정 요청 스키마"""
    goal_type: Optional[str] = None
    goal_description: Optional[str] = None
    weekly_plan: Optional[str] = None
    ended_at: Optional[datetime] = None


class UserGoalResponse(UserGoalBase):
    """사용자 목표 응답 스키마"""
    id: int
    user_id: int
    weekly_plan: Optional[str] = None
    started_at: datetime
    ended_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# ============================================================================
# LLM Input/Output Schemas - 상태 분석 (LLM1)
# ============================================================================

class StatusAnalysisInput(BaseModel):
    """
    LLM1: 건강 상태 분석용 Input 스키마
    - LLM 팀원이 API 연동 시 이 데이터를 사용
    """
    record_id: int
    user_id: int
    measured_at: datetime
    measurements: Dict[str, Any]  # 인바디 측정 데이터 전체
    body_type1: Optional[str] = None  # stage2: 근육 보정 체형
    body_type2: Optional[str] = None  # stage3: 최종 체형

    class Config:
        from_attributes = True


class StatusAnalysisResponse(BaseModel):
    """LLM1 응답: 프론트엔드에서 LLM API 호출에 사용할 input 반환"""
    success: bool = True
    message: str = "LLM input 데이터 준비 완료. 프론트엔드에서 LLM API를 호출하세요."
    input_data: StatusAnalysisInput


# ============================================================================
# LLM Input/Output Schemas - 주간 계획 (LLM2)
# ============================================================================

class GoalPlanInput(BaseModel):
    """
    LLM2: 주간 계획서 생성용 Input 스키마
    - LLM 팀원이 API 연동 시 이 데이터를 사용
    """
    # 사용자 요구사항
    user_goal_type: Optional[str] = None
    user_goal_description: Optional[str] = None

    # 최신 건강 기록
    record_id: int
    user_id: int
    measured_at: datetime
    measurements: Dict[str, Any]  # 인바디 측정 데이터 전체
    body_type1: Optional[str] = None  # stage2: 근육 보정 체형
    body_type2: Optional[str] = None  # stage3: 최종 체형

    # LLM1(status_analysis)의 분석 결과
    status_analysis_result: Optional[str] = None
    status_analysis_id: Optional[int] = None

    class Config:
        from_attributes = True


class GoalPlanResponse(BaseModel):
    """LLM2 응답: 프론트엔드에서 LLM API 호출에 사용할 input 반환"""
    success: bool = True
    message: str = "LLM input 데이터 준비 완료. 프론트엔드에서 LLM API를 호출하세요."
    input_data: GoalPlanInput


class GoalPlanRequest(BaseModel):
    """LLM2 요청: 주간 계획서 생성을 위한 사용자 입력"""
    record_id: int  # 프론트에서 선택한 건강 기록 ID
    user_goal_type: Optional[str] = None  # 목표 타입 (다이어트, 근육 증가 등)
    user_goal_description: Optional[str] = None  # 상세 목표 설명
