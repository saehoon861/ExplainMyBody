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
    body_type1 = Column(String(100), nullable=True)  # stage2: 근육 보정 체형 (비만형, 표준형, 근육형 등)
    body_type2 = Column(String(100), nullable=True)  # stage3: 최종 체형 (상체발달형, 하체비만형, 밸런스형 등)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 관계 설정
    user = relationship("User", back_populates="health_records")
    analysis_reports = relationship("AnalysisReport", back_populates="health_record", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<HealthRecord(id={self.id}, user_id={self.user_id}, measured_at={self.measured_at})>"
