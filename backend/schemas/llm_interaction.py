from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class LLMInteractionBase(BaseModel):
    """LLMInteraction 기본 스키마"""
    llm_stage: str
    source_type: Optional[str] = None
    source_id: Optional[int] = None
    category_type: Optional[str] = None
    output_text: str
    model_version: Optional[str] = None

class LLMInteractionCreate(LLMInteractionBase):
    """LLMInteraction 생성 요청 스키마"""
    pass

class LLMInteractionResponse(LLMInteractionBase):
    """LLMInteraction 응답 스키마"""
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True
