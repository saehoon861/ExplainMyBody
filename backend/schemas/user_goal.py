"""
UserGoal Pydantic 스키마
"""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional


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
