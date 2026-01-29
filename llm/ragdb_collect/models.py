"""
RAG 문서 데이터 모델
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class PaperMetadata(BaseModel):
    """논문 메타데이터"""

    domain: str = Field(..., description="분야: protein_hypertrophy, fat_loss, korean_diet, body_composition")
    language: str = Field(..., description="언어: en, ko")
    title: str = Field(..., description="논문 제목")
    abstract: str = Field(..., description="초록 전문")
    keywords: List[str] = Field(default_factory=list, description="키워드 리스트")
    source: str = Field(..., description="출처: PubMed, KCI, KoreaScience")
    year: Optional[int] = Field(None, description="발행 연도")
    pmid: Optional[str] = Field(None, description="PubMed ID")
    doi: Optional[str] = Field(None, description="DOI")
    authors: Optional[List[str]] = Field(default_factory=list, description="저자 리스트")
    journal: Optional[str] = Field(None, description="저널명")


class CollectionStats(BaseModel):
    """수집 통계"""

    total_collected: int = 0
    by_domain: dict = Field(default_factory=dict)
    by_language: dict = Field(default_factory=dict)
    by_source: dict = Field(default_factory=dict)
    failed_count: int = 0
