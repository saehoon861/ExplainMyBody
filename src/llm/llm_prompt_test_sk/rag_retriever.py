"""
Simple Embedding-based RAG Retriever (테스트용)
backend/services/llm/rag_retriever.py와 동일하지만 독립적인 DB 연결
"""

from typing import List, Dict, Any, Optional
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker
import os
from dotenv import load_dotenv

from llm_clients import OpenAIClient

load_dotenv()


class SimpleRAGRetriever:
    """
    Simple Embedding-based RAG Retriever
    - Vector 유사도 검색만 사용 (pgvector)
    - OpenAI text-embedding-3-small (1536D)
    """

    def __init__(self):
        """초기화"""
        # OpenAI 임베딩 클라이언트
        self.embedding_client = OpenAIClient()
        self.embedding_dim = 1536

        # PostgreSQL 연결 (독립적)
        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            raise ValueError("DATABASE_URL 환경변수가 설정되지 않았습니다.")

        self.engine = create_engine(db_url)
        self.SessionLocal = sessionmaker(bind=self.engine)
        self.session: Optional[Session] = None

    def _get_session(self) -> Session:
        """PostgreSQL 세션 lazy 초기화"""
        if not self.session:
            self.session = self.SessionLocal()
        return self.session

    def retrieve_relevant_papers(
        self,
        query: str,
        top_k: int = 5,
        lang: str = "ko",
    ) -> List[Dict[str, Any]]:
        """
        관련 논문 검색 (Vector 유사도만)

        Args:
            query: 검색 쿼리 (자연어)
            top_k: 최종 결과 개수
            lang: 언어 필터 ("ko" 또는 "en")

        Returns:
            논문 리스트 (유사도 기반)
        """
        try:
            print(f"\n🔍 RAG 검색 중...")
            print(f"  쿼리: {query}")

            # 1. 쿼리 임베딩 생성
            query_embedding = self.embedding_client.create_embedding(text=query)
            print(f"  ✓ 임베딩 생성 완료 ({len(query_embedding)}D)")

            # 2. Vector 검색 (pgvector)
            session = self._get_session()
            papers = self._search_similar_papers(
                session=session,
                query_embedding=query_embedding,
                top_k=top_k,
                lang=lang,
            )

            print(f"  ✓ {len(papers)}개 논문 검색 완료\n")
            return papers

        except Exception as e:
            print(f"  ❌ RAG 검색 실패: {e}")
            return []

    def _search_similar_papers(
        self,
        session: Session,
        query_embedding: List[float],
        top_k: int,
        lang: str,
    ) -> List[Dict[str, Any]]:
        """
        Vector 유사도 검색 (pgvector)

        Args:
            session: DB 세션
            query_embedding: 쿼리 임베딩 벡터
            top_k: 결과 개수
            lang: 언어 필터

        Returns:
            논문 리스트
        """
        # pgvector 코사인 유사도 검색 (<=> 연산자)
        # embedding_ko_openai 사용 (한국어 요약에 대한 임베딩)
        query_sql = text("""
            SELECT
                paper_id,
                title,
                chunk_text,
                chunk_ko_summary,
                year,
                source,
                pmid,
                doi,
                lang,
                1 - (embedding_ko_openai <=> :query_embedding) as similarity
            FROM paper_nodes
            WHERE embedding_ko_openai IS NOT NULL
              AND chunk_ko_summary IS NOT NULL
              AND chunk_ko_summary != ''
            ORDER BY embedding_ko_openai <=> :query_embedding
            LIMIT :top_k
        """)

        # 쿼리 임베딩을 PostgreSQL array 형식으로 변환
        embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"

        result = session.execute(
            query_sql,
            {
                "query_embedding": embedding_str,
                "top_k": top_k,
            }
        )

        papers = []
        for row in result:
            papers.append({
                'paper_id': row[0],
                'title': row[1] or 'N/A',
                'chunk_text': row[2] or '',
                'chunk_ko_summary': row[3] or '',
                'year': row[4],
                'source': row[5] or 'Unknown',
                'pmid': row[6],
                'doi': row[7],
                'lang': row[8] or 'unknown',
                'similarity': float(row[9]) if row[9] else 0.0,
            })

        return papers

    def format_papers_for_prompt(self, papers: List[Dict[str, Any]]) -> str:
        """
        논문을 프롬프트에 추가할 형식으로 포맷팅
        - 논문 메타데이터 제거, 핵심 내용만 전달

        Args:
            papers: 논문 리스트

        Returns:
            포맷된 문자열
        """
        if not papers:
            return ""

        formatted_text = "\n\n## 참고 자료\n\n"

        for i, paper in enumerate(papers, 1):
            chunk_ko_summary = paper.get('chunk_ko_summary', '')
            # 한국어 요약 우선 사용
            content = chunk_ko_summary if chunk_ko_summary else paper.get('chunk_text', '')[:300]

            if content:
                formatted_text += f"{content}\n\n"

        return formatted_text

    def close(self):
        """리소스 정리"""
        if self.session:
            self.session.close()
            self.session = None

    def __del__(self):
        """소멸자"""
        self.close()
