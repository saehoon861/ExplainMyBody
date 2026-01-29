"""
HealthRecord 테이블 ORM 모델
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from database import Base


class HealthRecord(Base):
    """건강 기록 테이블"""
    __tablename__ = "health_records"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    source = Column(String(100), default="manual")  # manual, ocr, api 등
    measured_at = Column(DateTime(timezone=True), server_default=func.now())
    measurements = Column(JSONB, nullable=False)  # JSONB 형태로 저장 (body_type1, body_type2 포함)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # 관계 설정
    user = relationship("User", back_populates="health_records")
    inbody_analysis_reports = relationship("InbodyAnalysisReport", back_populates="health_record", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<HealthRecord(id={self.id}, user_id={self.user_id}, measured_at={self.measured_at})>"
