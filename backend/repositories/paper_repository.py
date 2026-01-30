"""
PaperNode Repository - 논문 벡터 검색 (pgvector)
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, or_
from sqlalchemy.sql import text
from models.paper_node import PaperNode
from models.paper_concept_relation import PaperConceptRelation


class PaperRepository:
    """논문 벡터 검색 Repository"""

    def __init__(self, session: Session):
        """
        Args:
            session: SQLAlchemy Session
        """
        self.session = session

    def search_similar_papers(
        self,
        query_embedding: List[float],
        top_k: int = 10,
        lang: Optional[str] = None,
        domain: Optional[str] = None,
        use_ko_embedding: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        벡터 유사도 검색 (pgvector <=> 연산자)

        Args:
            query_embedding: 쿼리 임베딩 벡터
            top_k: 상위 K개 결과
            lang: 언어 필터 (ko/en)
            domain: 도메인 필터
            use_ko_embedding: 한국어 임베딩 사용 여부

        Returns:
            유사 논문 리스트
        """
        # 임베딩 컬럼 선택
        if use_ko_embedding:
            embedding_col = "embedding_ko_openai"
        else:
            embedding_col = "embedding_openai"

        # SQL 쿼리 (pgvector cosine similarity)
        query = f"""
        SELECT
            id,
            paper_id,
            title,
            chunk_text,
            lang,
            chunk_ko_summary,
            domain,
            source,
            year,
            pmid,
            doi,
            journal,
            1 - ({embedding_col} <=> :query_embedding) as similarity
        FROM paper_nodes
        WHERE {embedding_col} IS NOT NULL
        """

        # 필터 조건 추가
        params = {"query_embedding": str(query_embedding)}

        if lang:
            query += " AND lang = :lang"
            params["lang"] = lang

        if domain:
            query += " AND domain = :domain"
            params["domain"] = domain

        # 정렬 및 제한
        query += f" ORDER BY {embedding_col} <=> :query_embedding LIMIT :top_k"
        params["top_k"] = top_k

        # 실행
        result = self.session.execute(text(query), params)
        rows = result.fetchall()

        # 결과 변환
        papers = []
        for row in rows:
            papers.append({
                "id": row[0],
                "paper_id": row[1],
                "title": row[2],
                "chunk_text": row[3],
                "lang": row[4],
                "chunk_ko_summary": row[5],
                "domain": row[6],
                "source": row[7],
                "year": row[8],
                "pmid": row[9],
                "doi": row[10],
                "journal": row[11],
                "similarity": float(row[12]),
            })

        return papers

    def get_paper_by_id(self, paper_id: str) -> Optional[PaperNode]:
        """
        Paper ID로 논문 조회

        Args:
            paper_id: paper_12345678

        Returns:
            PaperNode 또는 None
        """
        return self.session.query(PaperNode).filter(
            PaperNode.paper_id == paper_id
        ).first()

    def get_papers_by_concept(
        self,
        concept_id: str,
        relation_type: Optional[str] = None,
        min_confidence: float = 0.5,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        개념 ID로 관련 논문 검색

        Args:
            concept_id: muscle_hypertrophy, protein_intake 등
            relation_type: MENTIONS, INCREASES 등
            min_confidence: 최소 신뢰도
            limit: 결과 개수

        Returns:
            관련 논문 리스트
        """
        query = (
            self.session.query(PaperNode, PaperConceptRelation)
            .join(
                PaperConceptRelation,
                PaperNode.id == PaperConceptRelation.paper_id
            )
            .filter(PaperConceptRelation.concept_id == concept_id)
        )

        if relation_type:
            query = query.filter(PaperConceptRelation.relation_type == relation_type)

        if min_confidence:
            query = query.filter(
                PaperConceptRelation.confidence >= min_confidence
            )

        query = query.order_by(desc(PaperConceptRelation.confidence)).limit(limit)

        results = query.all()

        papers = []
        for paper_node, relation in results:
            paper_dict = paper_node.to_dict()
            paper_dict["relation"] = relation.to_dict()
            papers.append(paper_dict)

        return papers

    def get_related_concepts(
        self, paper_id: int, relation_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        논문 ID로 관련 개념 조회

        Args:
            paper_id: Paper DB ID
            relation_type: 관계 타입 필터

        Returns:
            관련 개념 리스트
        """
        query = self.session.query(PaperConceptRelation).filter(
            PaperConceptRelation.paper_id == paper_id
        )

        if relation_type:
            query = query.filter(PaperConceptRelation.relation_type == relation_type)

        query = query.order_by(desc(PaperConceptRelation.confidence))

        relations = query.all()
        return [r.to_dict() for r in relations]

    def bulk_insert_papers(self, papers: List[Dict[str, Any]]) -> int:
        """
        대량 논문 삽입

        Args:
            papers: 논문 데이터 리스트

        Returns:
            삽입된 개수
        """
        try:
            paper_nodes = [PaperNode(**paper) for paper in papers]
            self.session.bulk_save_objects(paper_nodes)
            self.session.commit()
            return len(paper_nodes)
        except Exception as e:
            self.session.rollback()
            raise e

    def bulk_insert_relations(self, relations: List[Dict[str, Any]]) -> int:
        """
        대량 관계 삽입

        Args:
            relations: 관계 데이터 리스트

        Returns:
            삽입된 개수
        """
        try:
            relation_objs = [PaperConceptRelation(**rel) for rel in relations]
            self.session.bulk_save_objects(relation_objs)
            self.session.commit()
            return len(relation_objs)
        except Exception as e:
            self.session.rollback()
            raise e
