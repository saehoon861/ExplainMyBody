from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class HumanFeedbackBase(BaseModel):
    """HumanFeedback 기본 스키마"""
    llm_interaction_id: int
    feedback_category: Optional[str] = None
    feedback_text: str

class HumanFeedbackCreate(HumanFeedbackBase):
    """HumanFeedback 생성 요청 스키마"""
    pass

class HumanFeedbackResponse(HumanFeedbackBase):
    """HumanFeedback 응답 스키마"""
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True
