"""
User 테이블 ORM 모델
"""

from models_rev import user_details
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base


class User(Base):
    """사용자 테이블"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), unique=True, nullable=False)
# unique=True 추가
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=True)  # 비밀번호 해시 (추후 인증 구현 시)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
# nullable=False 추가 
# 위 func.now()로는 한국시간 반영이 안됨(DB시간은 표준UTC)
# from zoneinfo import ZoneInfo
# kst_time = created_at.astimezone(ZoneInfo("Asia/Seoul"))
# 추후 웹서비스에서 생성시간 표시할 경우 한국시간 반영된 시간 변수 생성 함수 추가 필요


# 관계 설정
    health_records = relationship("HealthRecord", back_populates="user", cascade="all, delete-orphan")
    inbody_analysis_reports = relationship("AnalysisReport", back_populates="user", cascade="all, delete-orphan")
# analysis_reports -> inbody_analysis_reports
    user_details = relationship("UserGoal", back_populates="user", cascade="all, delete-orphan")
# goals -> user_details  
    weekly_plans = relationship("WeeklyPlan", back_populates="user", cascade="all, delete-orphan")
# weekly_plans (WeeklyPlan 관계 추가)
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"
