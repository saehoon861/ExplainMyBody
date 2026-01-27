"""
SQLAlchemy ORM 모델 정의 (pgvector 지원)
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    Text,
    Float,
    Date,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import declarative_base, relationship
from pgvector.sqlalchemy import Vector

Base = declarative_base()


class User(Base):
    """사용자 테이블"""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    health_records = relationship(
        "HealthRecord", back_populates="user", cascade="all, delete-orphan"
    )
    analysis_reports = relationship(
        "AnalysisReport", back_populates="user", cascade="all, delete-orphan"
    )
    user_goals = relationship(
        "UserGoal", back_populates="user", cascade="all, delete-orphan"
    )
    weekly_plans = relationship(
        "WeeklyPlan", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"


class HealthRecord(Base):
    """건강 기록 테이블 (InBody 측정 데이터)"""

    __tablename__ = "health_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    record_date = Column(DateTime, default=datetime.utcnow)
    measurements = Column(JSONB, nullable=False)  # InBody 측정 데이터 (JSONB)
    source = Column(String(50), default="manual")  # manual, inbody_ocr, etc.

    # Relationships
    user = relationship("User", back_populates="health_records")
    analysis_reports = relationship(
        "AnalysisReport", back_populates="health_record", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<HealthRecord(id={self.id}, user_id={self.user_id}, record_date={self.record_date})>"


class AnalysisReport(Base):
    """분석 리포트 테이블 (LLM 분석 결과 + 임베딩)"""

    __tablename__ = "analysis_reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    record_id = Column(
        Integer, ForeignKey("health_records.id", ondelete="CASCADE"), nullable=False
    )
    report_date = Column(DateTime, default=datetime.utcnow)
    llm_output = Column(Text, nullable=False)  # LLM 생성 분석 텍스트
    model_version = Column(String(100))  # 사용된 LLM 모델
    embedding_1536 = Column(Vector(1536))  # OpenAI text-embedding-3-small (1536 차원)
    embedding_1024 = Column(Vector(1024))  # Ollama bge-m3 (1024 차원)

    # Relationships
    user = relationship("User", back_populates="analysis_reports")
    health_record = relationship("HealthRecord", back_populates="analysis_reports")

    def __repr__(self):
        return f"<AnalysisReport(id={self.id}, user_id={self.user_id}, record_id={self.record_id})>"


class UserGoal(Base):
    """사용자 목표 테이블"""

    __tablename__ = "user_goals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    goal_data = Column(JSONB, nullable=False)  # 목표 데이터 (JSONB)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Integer, default=1)  # 활성화 여부 (1=활성, 0=비활성)

    # Relationships
    user = relationship("User", back_populates="user_goals")

    def __repr__(self):
        return f"<UserGoal(id={self.id}, user_id={self.user_id}, is_active={self.is_active})>"


class WeeklyPlan(Base):
    """주간 계획 테이블"""

    __tablename__ = "weekly_plans"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    week_number = Column(Integer, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    plan_data = Column(JSONB, nullable=False)  # 주간 계획 데이터 (JSONB)
    model_version = Column(String(100))  # 사용된 LLM 모델
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="weekly_plans")

    def __repr__(self):
        return f"<WeeklyPlan(id={self.id}, user_id={self.user_id}, week={self.week_number})>"
