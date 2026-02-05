"""
LLM 상호작용 테이블 ORM 모델
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base


class LLMInteraction(Base):
    """LLM 상호작용 테이블"""
    __tablename__ = "llm_interactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    llm_stage = Column(String, nullable=False)  # "llm1", "llm2"
    source_type = Column(String)  # "health_record", "inbody_analysis", "weekly_plan_initial"
    source_id = Column(Integer)
    category_type = Column(String)  # "exercise_plan", "diet_plan", etc.
    output_text = Column(Text, nullable=False)
    model_version = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # 관계 설정
    user = relationship("User", back_populates="llm_interactions")
    human_feedbacks = relationship("HumanFeedback", back_populates="llm_interaction", cascade="all, delete-orphan")

    def __repr__(self):
            return f"<LLMInteraction(id={self.id}, user_id={self.user_id}, stage='{self.llm_stage}')>"
