"""
SQLAlchemy ORM 모델 정의 (pgvector 지원)
"""

import json
from datetime import datetime
from typing import Optional, Any

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
from sqlalchemy.types import TypeDecorator
from pgvector.sqlalchemy import Vector

Base = declarative_base()


class _JSONText(TypeDecorator):
    """dict/list를 DB에는 JSON 문자열(Text)로 저장, 조회 시 다시 dict/list로 복원"""

    impl = Text
    cache_ok = True

    def process_bind_param(self, value: Any, dialect) -> Optional[str]:
        if value is None:
            return None
        if isinstance(value, str):
            return value
        return json.dumps(value, ensure_ascii=False)

    def process_result_value(self, value: Optional[str], dialect) -> Any:
        if value is None or (isinstance(value, str) and not value.strip()):
            return None
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return value


class User(Base):
    """사용자 테이블"""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=True)  # id에 대응하는 비밀번호 해시
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    health_records = relationship(
        "HealthRecord", back_populates="user", cascade="all, delete-orphan"
    )
    inbody_analysis_reports = relationship(
        "InbodyAnalysisReport", back_populates="user", cascade="all, delete-orphan"
    )
    user_details = relationship(
        "UserDetail", back_populates="user", cascade="all, delete-orphan"
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
    # InBody 측정 데이터 (JSONB). rule_based_bodytype 결과: body_type1(=stage2), body_type2(=stage3) 포함 가능
    measurements = Column(JSONB, nullable=False)
    source = Column(String(50), default="manual")  # manual, inbody_ocr, etc.

    # Relationships
    user = relationship("User", back_populates="health_records")
    inbody_analysis_reports = relationship(
        "InbodyAnalysisReport", back_populates="health_record", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<HealthRecord(id={self.id}, user_id={self.user_id}, record_date={self.record_date})>"


class InbodyAnalysisReport(Base):
    """인바디 분석 리포트 테이블 (LLM 분석 결과 + 임베딩)"""

    __tablename__ = "inbody_analysis_reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    record_id = Column(
        Integer, ForeignKey("health_records.id", ondelete="CASCADE"), nullable=False
    )
    report_date = Column(DateTime, default=datetime.utcnow)
    llm_output = Column(Text, nullable=False)  # LLM 생성 분석 텍스트
<<<<<<< HEAD
<<<<<<< HEAD
=======
    refined_output = Column(Text, nullable=True)  # 2차 LLM 생성 정제된 텍스트
>>>>>>> 7e539dd (branch이동중 불필요 egg파일삭제)
=======
    refined_output = Column(Text, nullable=True)  # 2차 LLM 생성 정제된 텍스트
>>>>>>> feature/llm2-new
    model_version = Column(String(100))  # 사용된 LLM 모델
    embedding_1536 = Column(Vector(1536))  # OpenAI text-embedding-3-small (1536 차원)
    embedding_1024 = Column(Vector(1024))  # Ollama bge-m3 (1024 차원)

    # Relationships
    user = relationship("User", back_populates="inbody_analysis_reports")
    health_record = relationship("HealthRecord", back_populates="inbody_analysis_reports")

    def __repr__(self):
        return f"<InbodyAnalysisReport(id={self.id}, user_id={self.user_id}, record_id={self.record_id})>"


class UserDetail(Base):
    """사용자 상세 테이블 (목표, 선호도, 건강 특이사항)"""

    __tablename__ = "user_details"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    goal_data = Column(_JSONText, nullable=True)  # 목표 데이터 (Text, JSON 문자열)
    preferences = Column(_JSONText, nullable=True)  # 선호도 (Text, JSON 문자열)
    health_specifics = Column(_JSONText, nullable=True)  # 건강 특이사항 (Text, JSON 문자열)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Integer, default=1)  # 활성화 여부 (1=활성, 0=비활성)

    # Relationships
    user = relationship("User", back_populates="user_details")

    def __repr__(self):
        return f"<UserDetail(id={self.id}, user_id={self.user_id}, is_active={self.is_active})>"


class WeeklyPlan(Base):
    """주간 계획 테이블"""

    __tablename__ = "weekly_plans"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    week_number = Column(Integer, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    plan_data = Column(JSONB, nullable=False)  # 주간 계획 데이터 (JSONB)
<<<<<<< HEAD
<<<<<<< HEAD
=======
    refined_output = Column(Text, nullable=True)  # 2차 LLM 생성 정제된 텍스트
>>>>>>> 7e539dd (branch이동중 불필요 egg파일삭제)
=======
    refined_output = Column(Text, nullable=True)  # 2차 LLM 생성 정제된 텍스트
>>>>>>> feature/llm2-new
    model_version = Column(String(100))  # 사용된 LLM 모델
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="weekly_plans")

    def __repr__(self):
        return f"<WeeklyPlan(id={self.id}, user_id={self.user_id}, week={self.week_number})>"
