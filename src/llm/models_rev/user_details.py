"""
UserDetail 테이블 ORM 모델
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base


class UserDetail(Base):
    """사용자 목표 테이블"""
    __tablename__ = "user_details"
# user_goals -> UserDetail 명칭변경경
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    goal_type = Column(String(255), nullable=True)  # 목표 유형 (체중 감량, 근육 증가 등)
    goal_description = Column(Text, nullable=True)  # 사용자가 입력한 목표 설명
# weekly_plan = Column(Text, nullable=True)  # LLM이 생성한 주간 계획서
# (주간 계획은 db_models에서는 WeeklyPlan 테이블로 분리)
    preferences = Column(Text, nullable=True)  # 선호도 (Text)
    health_specifics = Column(Text, nullable=True)  # 건강 특이사항 (Text)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    ended_at = Column(DateTime(timezone=True), nullable=True)  # NULL이면 진행 중
    is_active = Column(Integer, default=1)  # 주간계획 활성화 여부 (1=활성, 0=비활성)
# preferences, health_specifics, is_active 컬럼 추가
  
# 관계 설정
    user = relationship("User", back_populates="user_details")
# back_populates relationship명 goals -> user_details
    
    def __repr__(self):
        return f"<UserGoal(id={self.id}, user_id={self.user_id}, goal_type='{self.goal_type}', is_active={self.is_active})>"
# is_active={self.is_active} 부분 추가
