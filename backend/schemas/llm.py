from pydantic import BaseModel
from typing import Dict, Any, Optional
from datetime import datetime

class StatusAnalysisInput(BaseModel):
    """건강 상태 분석 요청 스키마"""
    record_id: int
    user_id: int
    measured_at: datetime
    measurements: Dict[str, Any]  # InBody 측정 데이터 (JSON)
    body_type1: Optional[str] = None
    body_type2: Optional[str] = None

class GoalPlanInput(BaseModel):
    """주간 계획 생성 요청 스키마"""
    user_goal_type: str
    user_goal_description: Optional[str] = None
    record_id: int
    user_id: int
    measured_at: datetime
    measurements: Dict[str, Any]
    status_analysis_result: Optional[str] = None
    status_analysis_id: Optional[int] = None
    # 프롬프트 생성을 위해 필요한 체형 정보
    body_type1: Optional[str] = None
    body_type2: Optional[str] = None

class ChatRequest(BaseModel):
    """Q&A 채팅 요청 스키마"""
    message: str

class LLMResponse(BaseModel):
    """공통 응답 스키마"""
    response: str