"""
Human Feedback 테이블 ORM 모델
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base


class HumanFeedback(Base):
    """사용자 피드백 테이블"""
    __tablename__ = "human_feedbacks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    llm_interaction_id = Column(Integer, ForeignKey("llm_interactions.id"), nullable=False)
    feedback_category = Column(String)  # "question", "exercise_adjustment", etc.
    feedback_text = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # 관계 설정
    llm_interaction = relationship("LLMInteraction", back_populates="human_feedbacks")
    user = relationship("User", back_populates="human_feedback_received")

    def __repr__(self):
        return f"<HumanFeedback(id={self.id}, llm_interaction_id={self.llm_interaction_id})>"
