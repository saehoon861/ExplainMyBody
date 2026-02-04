"""
LLM 입력/출력 스키마
backend/schemas/llm.py에서 필요한 부분만 추출
"""

from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime


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
    record_id: Optional[int] = None  # 테스트 시 선택적
    user_id: Optional[int] = None  # 테스트 시 선택적
    measured_at: Optional[datetime] = None  # 테스트 시 선택적
    measurements: Optional[Dict[str, Any]] = None  # 테스트 시 선택적
    status_analysis_result: Optional[str] = None
    status_analysis_id: Optional[int] = None
    
    
    # 추가 필드 (backend에는 없지만 weekly_plan_graph_rag.py에서 사용)
    main_goal: Optional[str] = None
    target_weight: Optional[float] = None
    target_date: Optional[str] = None  # datetime -> str (유연성)
    preferred_exercise_types: Optional[list] = None
    available_days_per_week: Optional[int] = None
    available_time_per_session: Optional[int] = None
    restrictions: Optional[list] = None
