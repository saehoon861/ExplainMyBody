"""
AnalysisReport 테이블 ORM 모델
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base


class InbodyAnalysisReport(Base):
    """분석 리포트 테이블 (LLM 출력 결과)"""
    __tablename__ = "inbody_analysis_reports"
# 클래스명 analysis_report → inbody_analysis_report
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    record_id = Column(Integer, ForeignKey("health_records.id", ondelete="CASCADE"), nullable=False, index=True)
    llm_output = Column(Text, nullable=False)  # LLM 생성 텍스트
    model_version = Column(String(100), nullable=True)  # 사용된 모델 버전
    analysis_type = Column(String(50), nullable=True)  # "status_analysis" 또는 "goal_plan"
    generated_at = Column(DateTime(timezone=True), server_default=func.now())
    embedding_1536 = Column(Vector(1536))  # OpenAI text-embedding-3-small (1536 차원)
# embedding_1536 (Vector(1536)) 저장 컬럼 추가
    
# 관계 설정
    user = relationship("User", back_populates="inbody_analysis_reports")
    health_record = relationship("HealthRecord", back_populates="inbody_analysis_reports")
#relationship명 analysis_reports → inbody_analysis_reports
    
    def __repr__(self):
        return f"<InbodyAnalysisReport(id={self.id}, user_id={self.user_id}, record_id={self.record_id})>"
