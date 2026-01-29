"""
User 테이블 ORM 모델
"""

from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base


class User(Base):
    """사용자 테이블"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=True)  # 비밀번호 해시 (추후 인증 구현 시)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # 관계 설정
    health_records = relationship("HealthRecord", back_populates="user", cascade="all, delete-orphan")
    inbody_analysis_reports = relationship("InbodyAnalysisReport", back_populates="user", cascade="all, delete-orphan")
    user_details = relationship("UserDetail", back_populates="user", cascade="all, delete-orphan")
    weekly_plans = relationship("WeeklyPlan", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"
