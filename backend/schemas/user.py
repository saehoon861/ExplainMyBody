"""
User Pydantic 스키마
"""

from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional


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
