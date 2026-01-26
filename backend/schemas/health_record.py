"""
HealthRecord Pydantic 스키마
"""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any


class HealthRecordBase(BaseModel):
    """건강 기록 기본 스키마"""
    measurements: Dict[str, Any]  # 인바디 측정 데이터
    source: str = "manual"


class HealthRecordCreate(HealthRecordBase):
    """건강 기록 생성 요청 스키마"""
    measured_at: Optional[datetime] = None


class HealthRecordUpdate(BaseModel):
    """건강 기록 수정 요청 스키마"""
    measurements: Optional[Dict[str, Any]] = None
    body_type1: Optional[str] = None
    body_type2: Optional[str] = None


class HealthRecordResponse(HealthRecordBase):
    """건강 기록 응답 스키마"""
    id: int
    user_id: int
    measured_at: datetime
    body_type1: Optional[str] = None  # stage2: 근육 보정 체형
    body_type2: Optional[str] = None  # stage3: 최종 체형
    created_at: datetime
    
    class Config:
        from_attributes = True
