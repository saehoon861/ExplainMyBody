"""
PaperConceptRelation 테이블 ORM 모델 (Graph RAG용)
논문 ↔ 개념 관계 저장 (MENTIONS, INCREASES, SUPPORTS 등)
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Index
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from database import Base


class PaperConceptRelation(Base):
    """논문-개념 관계 테이블 (Graph RAG용)"""
    __tablename__ = "paper_concept_relations"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # 관계
    paper_id = Column(Integer, ForeignKey("paper_nodes.id", ondelete="CASCADE"), nullable=False, index=True)
    concept_id = Column(String(100), nullable=False, index=True)  # muscle_hypertrophy, protein_intake 등

    # 관계 타입
    relation_type = Column(String(50), nullable=False, index=True)  # MENTIONS, INCREASES, SUPPORTS, REDUCES

    # 메타데이터
    confidence = Column(Float, nullable=True)  # 신뢰도 (0.0 ~ 1.0)
    matched_term = Column(String(200), nullable=True)  # 매칭된 검색어
    count = Column(Integer, nullable=True)  # 등장 횟수
    evidence_level = Column(String(50), nullable=True)  # high, medium, low
    magnitude = Column(Float, nullable=True)  # 효과 크기

    # 개념 정보 (빠른 검색용 비정규화)
    concept_name_ko = Column(String(100), nullable=True)
    concept_name_en = Column(String(100), nullable=True)
    concept_type = Column(String(50), nullable=True)  # Outcome, Intervention, Biomarker 등

    # 타임스탬프
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship (선택적)
    # paper = relationship("PaperNode", back_populates="concepts")

    # 복합 인덱스 (paper + concept 조합으로 검색 최적화)
    __table_args__ = (
        Index('idx_paper_concept', 'paper_id', 'concept_id'),
        Index('idx_concept_relation', 'concept_id', 'relation_type'),
    )

    def __repr__(self):
        return f"<PaperConceptRelation(paper_id={self.paper_id}, concept={self.concept_id}, type={self.relation_type})>"

    def to_dict(self):
        """딕셔너리 변환"""
        return {
            "id": self.id,
            "paper_id": self.paper_id,
            "concept_id": self.concept_id,
            "concept_name_ko": self.concept_name_ko,
            "concept_name_en": self.concept_name_en,
            "concept_type": self.concept_type,
            "relation_type": self.relation_type,
            "confidence": self.confidence,
            "matched_term": self.matched_term,
            "count": self.count,
            "evidence_level": self.evidence_level,
            "magnitude": self.magnitude,
        }
