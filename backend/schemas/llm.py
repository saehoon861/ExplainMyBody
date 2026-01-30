"""
LLM Schemas - LLM 팀원 전담
InbodyAnalysisReport, UserDetail, WeeklyPlan, LLM 입출력 (상태 분석 + 주간 계획) 관련 모든 스키마
"""

from pydantic import BaseModel
from datetime import datetime, date
from typing import Optional, Dict, Any, List


# ============================================================================
# InbodyAnalysisReport Schemas
# ============================================================================

class AnalysisReportBase(BaseModel):
    """분석 리포트 기본 스키마"""
    llm_output: str
    model_version: Optional[str] = None
    analysis_type: Optional[str] = None  # "status_analysis" 또는 "goal_plan"
    thread_id: Optional[str] = None      # LangGraph 대화 스레드 ID


class AnalysisReportCreate(AnalysisReportBase):
    """분석 리포트 생성 요청 스키마"""
    record_id: int
    embedding_1536: Optional[List[float]] = None  # OpenAI embedding (1536 차원)
    embedding_1024: Optional[List[float]] = None  # Ollama bge-m3 embedding 


# ============================================================================
# LLM Input Schemas
# ============================================================================

class StatusAnalysisInput(BaseModel):
    """LLM1: 건강 상태 분석 입력 스키마"""
    record_id: int
    user_id: int
    measured_at: datetime
    measurements: Dict[str, Any]
    body_type1: Optional[str] = None
    body_type2: Optional[str] = None


class GoalPlanInput(BaseModel):
    """LLM2: 주간 계획 생성 입력 스키마"""
    user_goal_type: Optional[str] = None
    user_goal_description: Optional[str] = None
    record_id: int
    user_id: int
    measured_at: datetime
    measurements: Dict[str, Any]
    status_analysis_result: Optional[str] = None
    status_analysis_id: Optional[int] = None
    body_type1: Optional[str] = None
    body_type2: Optional[str] = None