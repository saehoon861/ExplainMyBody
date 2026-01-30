"""
PaperNode 테이블 ORM 모델 (Graph RAG용)
논문 데이터 저장 및 pgvector 벡터 검색
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Float
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB
from pgvector.sqlalchemy import Vector
from database import Base


class PaperNode(Base):
    """논문 노드 테이블 (Graph RAG용)"""
    __tablename__ = "paper_nodes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    paper_id = Column(String(100), unique=True, nullable=False, index=True)  # paper_12345678

    # 텍스트 데이터
    title = Column(Text, nullable=False)
    chunk_text = Column(Text, nullable=False)  # 원본 초록
    lang = Column(String(10), nullable=False, index=True)  # ko 또는 en
    chunk_ko_summary = Column(Text, nullable=True)  # 한국어 요약 (영어 논문만)

    # 메타데이터
    domain = Column(String(100), nullable=False, index=True)  # protein_hypertrophy, fat_loss 등
    source = Column(String(50), nullable=False)  # pubmed, kci, scienceon
    year = Column(Integer, nullable=True, index=True)
    pmid = Column(String(50), nullable=True)
    doi = Column(String(100), nullable=True)
    authors = Column(JSONB, nullable=True)  # ["Author1", "Author2"]
    journal = Column(String(200), nullable=True)
    keywords = Column(JSONB, nullable=True)  # ["keyword1", "keyword2"]

    # 임베딩 벡터 (pgvector)
    embedding_openai = Column(Vector(1536), nullable=True)  # OpenAI text-embedding-3-small
    embedding_ollama = Column(Vector(1024), nullable=True)  # Ollama bge-m3
    embedding_ko_openai = Column(Vector(1536), nullable=True)  # 한국어 요약 임베딩 (OpenAI)

    # 임베딩 제공자
    embedding_provider = Column(String(50), nullable=True)  # openai 또는 ollama

    # 타임스탬프
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<PaperNode(id={self.id}, paper_id={self.paper_id}, title={self.title[:50]})>"

    def to_dict(self):
        """딕셔너리 변환 (API 응답용)"""
        return {
            "id": self.id,
            "paper_id": self.paper_id,
            "title": self.title,
            "chunk_text": self.chunk_text,
            "lang": self.lang,
            "chunk_ko_summary": self.chunk_ko_summary,
            "domain": self.domain,
            "source": self.source,
            "year": self.year,
            "pmid": self.pmid,
            "doi": self.doi,
            "authors": self.authors,
            "journal": self.journal,
            "keywords": self.keywords,
            "embedding_provider": self.embedding_provider,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
