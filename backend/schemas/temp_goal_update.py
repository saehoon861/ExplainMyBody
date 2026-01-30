from pydantic import BaseModel
from typing import Optional

class UserGoalUpdateRequest(BaseModel):
    """목표 수정 요청 스키마"""
    start_weight: Optional[float] = None
    target_weight: Optional[float] = None
    goal_type: Optional[str] = None
    goal_description: Optional[str] = None
