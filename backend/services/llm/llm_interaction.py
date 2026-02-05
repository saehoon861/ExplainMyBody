from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class LLMInteraction(Base):
    __tablename__ = "llm_interactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    llm_stage = Column(String, nullable=False)  # "llm1", "llm2"
    source_type = Column(String)  # "health_record", "inbody_analysis", "weekly_plan_initial"
    source_id = Column(Integer)
    category_type = Column(String)  # "exercise_plan", "diet_plan", etc.
    output_text = Column(Text, nullable=False)
    model_version = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # NOTE: The 'User' model in 'models/user.py' should be updated with:
    # llm_interactions = relationship("LLMInteraction", back_populates="user")
    user = relationship("User", back_populates="llm_interactions")
    human_feedbacks = relationship("HumanFeedback", back_populates="llm_interaction", cascade="all, delete-orphan")
