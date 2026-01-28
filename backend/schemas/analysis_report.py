"""
AnalysisReport Pydantic 스키마
"""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional


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
