"""
UserGoal 테이블 ORM 모델
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base


class UserGoal(Base):
    """사용자 목표 테이블"""
    __tablename__ = "user_goals"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    goal_type = Column(String(255), nullable=True)  # 목표 유형 (체중 감량, 근육 증가 등)
    goal_description = Column(Text, nullable=True)  # 사용자가 입력한 목표 설명
    weekly_plan = Column(Text, nullable=True)  # LLM이 생성한 주간 계획서
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    ended_at = Column(DateTime(timezone=True), nullable=True)  # NULL이면 진행 중
    
    # 관계 설정
    user = relationship("User", back_populates="goals")
    
    def __repr__(self):
        return f"<UserGoal(id={self.id}, user_id={self.user_id}, goal_type='{self.goal_type}')>"
