from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class HumanFeedback(Base):
    __tablename__ = "human_feedbacks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    llm_interaction_id = Column(Integer, ForeignKey("llm_interactions.id"), nullable=False)
    feedback_category = Column(String)  # "question", "exercise_adjustment", etc.
    feedback_text = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # NOTE: The 'User' model in 'models/user.py' should be updated with:
    # human_feedbacks = relationship("HumanFeedback", back_populates="user")
    user = relationship("User", back_populates="human_feedbacks")
    llm_interaction = relationship("LLMInteraction", back_populates="human_feedbacks")
