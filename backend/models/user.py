"""
User 테이블 ORM 모델
"""

from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base


class User(Base):
    """사용자 테이블"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=True)  # 비밀번호 해시 (추후 인증 구현 시)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # 관계 설정
    health_records = relationship("HealthRecord", back_populates="user", cascade="all, delete-orphan")
    inbody_analysis_reports = relationship("InbodyAnalysisReport", back_populates="user", cascade="all, delete-orphan")
    user_details = relationship("UserDetail", back_populates="user", cascade="all, delete-orphan")
    weekly_plans = relationship("WeeklyPlan", back_populates="user", cascade="all, delete-orphan")
    llm_interactions = relationship("LLMInteraction", back_populates="user", cascade="all, delete-orphan")
    human_feedback_received = relationship("HumanFeedback", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"

    @property
    def active_detail(self):
        """활성 상태의 최신 UserDetail 반환"""
        if not self.user_details:
            return None
        # is_active=1 이고 ended_at이 None인 것 중 가장 최근 것
        active = [d for d in self.user_details if d.is_active == 1 and d.ended_at is None]
        if not active:
            return None
        # ID 역순 or started_at 역순
        return sorted(active, key=lambda x: x.id, reverse=True)[0]

    @property
    def goal_type(self):
        return self.active_detail.goal_type if self.active_detail else None

    @property
    def goal_description(self):
        """JSON 파싱 후 description 반환"""
        if not self.active_detail or not self.active_detail.goal_description:
            return None
        try:
            import json
            data = json.loads(self.active_detail.goal_description)
            if isinstance(data, dict):
                return data.get("description")
        except:
            pass
        return self.active_detail.goal_description

    @property
    def target_weight(self):
        """JSON 파싱 후 target_weight 반환"""
        if not self.active_detail or not self.active_detail.goal_description:
            return None
        try:
            import json
            data = json.loads(self.active_detail.goal_description)
            if isinstance(data, dict):
                return data.get("target_weight")
        except:
            pass
        return None

    @property
    def start_weight(self):
        """JSON 파싱 후 start_weight 반환 (목표 설정 시점의 시작 체중)"""
        if not self.active_detail or not self.active_detail.goal_description:
            return None
        try:
            import json
            data = json.loads(self.active_detail.goal_description)
            if isinstance(data, dict):
                return data.get("start_weight")
        except:
            pass
        return None
