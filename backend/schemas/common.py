"""
Common Schemas - 공통 스키마
User, HealthRecord 등 양 팀 모두 사용하는 기본 CRUD 스키마
"""

from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, Dict, Any


# ============================================================================
# User Schemas
# ============================================================================

class UserBase(BaseModel):
    """사용자 기본 스키마"""
    username: str
    email: EmailStr


class UserCreate(UserBase):
    """사용자 생성 요청 스키마"""
    password: Optional[str] = None  # 추후 인증 구현 시 사용


class UserLogin(BaseModel):
    """로그인 요청 스키마"""
    email: EmailStr
    password: str


class UserResponse(UserBase):
    """사용자 응답 스키마"""
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True  # ORM 모델과 호환


# ============================================================================
# HealthRecord Schemas
# ============================================================================

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
