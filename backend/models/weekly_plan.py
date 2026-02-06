"""
WeeklyPlan 테이블 ORM 모델
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Date
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from database import Base


class WeeklyPlan(Base):
    """주간 계획 테이블"""
    __tablename__ = "weekly_plans"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    thread_id = Column(String, nullable=False, unique=True, index=True) # LangGraph 스레드 ID
    initial_llm_interaction_id = Column(Integer, ForeignKey("llm_interactions.id"), nullable=False) # 첫 LLM 상호작용 ID
    week_number = Column(Integer, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    plan_data = Column(JSONB, nullable=False)  # 주간 계획 데이터 (JSONB)
    model_version = Column(String(100))  # 사용된 LLM 모델
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="weekly_plans")
    initial_llm_interaction = relationship("LLMInteraction")

    def __repr__(self):
        return f"<WeeklyPlan(id={self.id}, user_id={self.user_id}, week={self.week_number})>"
