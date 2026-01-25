"""
HealthRecord 테이블 ORM 모델
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base


class HealthRecord(Base):
    """건강 기록 테이블"""
    __tablename__ = "health_records"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    source = Column(String(100), default="manual")  # manual, ocr, api 등
    measured_at = Column(DateTime(timezone=True), server_default=func.now())
    measurements = Column(JSON, nullable=False)  # JSONB 형태로 저장
    body_type = Column(String(100), nullable=True)  # 체형 분류 결과 (rule_based_bodytype)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 관계 설정
    user = relationship("User", back_populates="health_records")
    analysis_reports = relationship("AnalysisReport", back_populates="health_record", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<HealthRecord(id={self.id}, user_id={self.user_id}, measured_at={self.measured_at})>"
