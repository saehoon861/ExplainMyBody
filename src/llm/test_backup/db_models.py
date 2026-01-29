"""
SQLAlchemy ORM Models for ExplainMyBody
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, ForeignKey,
    func, Index
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all ORM models"""
    pass


class User(Base):
    """사용자 정보"""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        server_default=func.current_timestamp()
    )

    # Relationships
    health_records: Mapped[List["HealthRecord"]] = relationship(
        "HealthRecord",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    analysis_reports: Mapped[List["AnalysisReport"]] = relationship(
        "AnalysisReport",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    user_goals: Mapped[List["UserGoal"]] = relationship(
        "UserGoal",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"User(id={self.id}, username='{self.username}', email='{self.email}')"


class UserGoal(Base):
    """사용자 목표"""
    __tablename__ = "user_goals"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    goal_type: Mapped[Optional[str]] = mapped_column(String(255))
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        server_default=func.current_timestamp()
    )
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=False))

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="user_goals")

    def __repr__(self) -> str:
        return f"UserGoal(id={self.id}, user_id={self.user_id}, goal_type='{self.goal_type}')"


class HealthRecord(Base):
    """건강 측정 기록"""
    __tablename__ = "health_records"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    source: Mapped[str] = mapped_column(String(100), default="manual")
    measured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        server_default=func.current_timestamp()
    )
    measurements: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        server_default=func.current_timestamp()
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="health_records")
    analysis_reports: Mapped[List["AnalysisReport"]] = relationship(
        "AnalysisReport",
        back_populates="health_record",
        cascade="all, delete-orphan"
    )

    # Indexes
    __table_args__ = (
        Index("idx_health_records_user", "user_id"),
        Index("idx_health_records_user_measured", "user_id", "measured_at"),
        Index("idx_health_records_measurements_gin", "measurements", postgresql_using="gin"),
    )

    def __repr__(self) -> str:
        return f"HealthRecord(id={self.id}, user_id={self.user_id}, source='{self.source}')"


class AnalysisReport(Base):
    """LLM 생성 건강 분석 리포트"""
    __tablename__ = "analysis_reports"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    record_id: Mapped[int] = mapped_column(
        ForeignKey("health_records.id", ondelete="CASCADE"),
        nullable=False
    )
    llm_output: Mapped[str] = mapped_column(Text, nullable=False)
    model_version: Mapped[Optional[str]] = mapped_column(String(100))
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        server_default=func.current_timestamp()
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="analysis_reports")
    health_record: Mapped["HealthRecord"] = relationship(
        "HealthRecord",
        back_populates="analysis_reports"
    )

    # Indexes
    __table_args__ = (
        Index("idx_analysis_reports_user", "user_id"),
        Index("idx_analysis_reports_record", "record_id"),
    )

    def __repr__(self) -> str:
        return f"AnalysisReport(id={self.id}, user_id={self.user_id}, model='{self.model_version}')"
