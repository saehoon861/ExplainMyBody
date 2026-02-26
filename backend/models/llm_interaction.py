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
    
    # 수정 이력 추적을 위한 자기 참조 관계
    parent_interaction_id = Column(Integer, ForeignKey("llm_interactions.id"), nullable=True)
    
    # 이 상호작용을 유발한 특정 사용자 피드백 ID
    triggering_feedback_id = Column(Integer, ForeignKey("human_feedbacks.id"), nullable=True)

    llm_stage = Column(String, nullable=False)  # "llm1", "llm2"
    source_type = Column(String)  # "health_record", "inbody_analysis", "weekly_plan_initial"
    source_id = Column(Integer)
    category_type = Column(String)  # "exercise_plan", "diet_plan", etc.
    output_text = Column(Text, nullable=False)
    model_version = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # --- 관계 설정 ---
    user = relationship("User", back_populates="llm_interactions")
    
    # 이 상호작용에 대해 사용자가 남긴 피드백들 (하나의 상호작용은 여러 피드백을 가질 수 있음)
    human_feedbacks = relationship("HumanFeedback", 
                                   back_populates="llm_interaction", 
                                   cascade="all, delete-orphan",
                                   foreign_keys="[HumanFeedback.llm_interaction_id]")

    # 이 상호작용을 유발한 단일 피드백 (하나의 상호작용은 하나의 트리거링 피드백을 가짐)
    triggering_feedback = relationship("HumanFeedback", 
                                       foreign_keys=[triggering_feedback_id],
                                       post_update=True) # 순환 종속성 방지

    # 부모-자식 관계 (수정 이력)
    parent = relationship("LLMInteraction", remote_side=[id], back_populates="children")
    children = relationship("LLMInteraction", back_populates="parent", cascade="all, delete-orphan")


    def __repr__(self):
            return f"<LLMInteraction(id={self.id}, user_id={self.user_id}, stage='{self.llm_stage}')>"
