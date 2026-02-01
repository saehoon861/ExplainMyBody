"""
Graph RAG Retriever - Hybrid Search (Vector + Graph)
- Vector 유사도 검색 (PostgreSQL pgvector) → 초기 후보 논문 탐색
- Graph 탐색 (Neo4j) → 개념 기반 관련 논문 확장
- Reranking → 최종 결과 정렬
- 항상 OpenAI text-embedding-3-small 사용 (1536D)
"""

from typing import List, Dict, Any, Optional
import sys
from pathlib import Path

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))
# backend 폴더도 추가 (backend 내부의 상대 경로 import를 위해)
sys.path.insert(0, str(project_root / "backend"))

from sqlalchemy.orm import Session
from backend.database import SessionLocal
from backend.repositories.paper_repository import PaperRepository
from backend.repositories.neo4j_repository import Neo4jRepository
from shared.llm_clients import OpenAIClient


class GraphRAGRetriever:
    """
    Graph RAG 검색기 (Hybrid: Vector + Graph)
    - Vector Search: 쿼리와 유사한 논문 검색 (pgvector)
    - Graph Expansion: 개념 기반 관련 논문 확장 (Neo4j)
    - Reranking: 시간, 유사도, 신뢰도 기반 재정렬
    """

    def __init__(self, use_neo4j: bool = True):
        """
        Args:
            use_neo4j: Neo4j 그래프 탐색 사용 여부 (기본: True)
        """
        self.use_neo4j = use_neo4j

        # OpenAI 임베딩 클라이언트 (항상 text-embedding-3-small 사용)
        self.embedding_client = OpenAIClient()
        self.embedding_dim = 1536

        # PostgreSQL 세션 및 Repository
        self.session: Optional[Session] = None
        self.paper_repo: Optional[PaperRepository] = None

        # Neo4j Repository
        self.neo4j_repo: Optional[Neo4jRepository] = None
        if use_neo4j:
            try:
                self.neo4j_repo = Neo4jRepository()
                if not self.neo4j_repo.driver:
                    print("  ⚠️  Neo4j 연결 실패. Vector 검색만 사용합니다.")
                    self.use_neo4j = False
            except Exception as e:
                print(f"  ⚠️  Neo4j 초기화 실패: {e}. Vector 검색만 사용합니다.")
                self.use_neo4j = False

        print(f"  🔧 Graph RAG Embedder: OpenAI text-embedding-3-small (1536D)")
        print(f"  🔧 Neo4j Graph: {'✅ Enabled' if self.use_neo4j else '❌ Disabled'}")

    def _get_session(self) -> Session:
        """PostgreSQL 세션 lazy 초기화"""
        if not self.session:
            self.session = SessionLocal()
            self.paper_repo = PaperRepository(self.session)
        return self.session

    def retrieve_relevant_papers(
        self,
        query: str,
        concepts: Optional[List[str]] = None,
        top_k: int = 10,
        domain: Optional[str] = None,
        lang: str = "ko",
    ) -> List[Dict[str, Any]]:
        """
        관련 논문 검색 (Hybrid: Vector + Graph)

        Args:
            query: 검색 쿼리 (자연어)
            concepts: 핵심 개념 리스트 (예: ["muscle_hypertrophy", "protein_intake"])
            top_k: 최종 결과 개수
            domain: 도메인 필터 (예: "protein_hypertrophy")
            lang: 언어 필터 ("ko" 또는 "en")

        Returns:
            논문 리스트 (유사도 + 그래프 기반)
        """
        print(f"\n🔍 Graph RAG 검색 중 (top_k={top_k})...")
        print(f"  - 쿼리: '{query[:50]}...'")
        if concepts:
            print(f"  - 개념: {concepts}")

        try:
            # 1. 쿼리 임베딩 생성 (OpenAI text-embedding-3-small)
            print(f"\n  📊 1단계: 쿼리 임베딩 생성 중...")
            query_embedding = self.embedding_client.create_embedding(text=query)
            print(f"    ✓ 임베딩 완료 (차원: {len(query_embedding)})")

            # 2. Vector 검색 (pgvector)
            print(f"\n  🔎 2단계: Vector 유사도 검색 (PostgreSQL)...")
            session = self._get_session()

            # 항상 embedding_ko_openai 사용 (모든 논문에 대해 한국어 임베딩 생성했음)
            use_ko_embedding = True

            vector_papers = self.paper_repo.search_similar_papers(
                query_embedding=query_embedding,
                top_k=top_k * 2,  # 후보 확장 (나중에 필터링)
                lang=lang,
                domain=domain,
                use_ko_embedding=use_ko_embedding,
            )

            print(f"    ✓ {len(vector_papers)}개 후보 논문 검색 완료")

            # 3. Graph 탐색 (Neo4j) - 개념 기반 확장
            graph_papers = []
            if self.use_neo4j and concepts:
                print(f"\n  🔷 3단계: Graph 탐색 (Neo4j)...")
                graph_papers = self._expand_by_concepts(concepts, limit=top_k)
                print(f"    ✓ {len(graph_papers)}개 그래프 기반 논문 발견")

            # 4. 결과 병합 및 Reranking
            print(f"\n  🎯 4단계: 결과 병합 및 Reranking...")
            merged_papers = self._merge_and_rerank(
                vector_papers=vector_papers,
                graph_papers=graph_papers,
                top_k=top_k,
            )

            print(f"    ✓ 최종 {len(merged_papers)}개 논문 선정\n")

            # 결과 출력
            for i, paper in enumerate(merged_papers, 1):
                source = paper.get('source_type', 'unknown')
                score = paper.get('final_score', 0)
                print(f"    {i}. [{source}] Score: {score:.3f} - {paper.get('title', 'N/A')[:60]}...")

            return merged_papers

        except Exception as e:
            print(f"  ❌ Graph RAG 검색 실패: {e}")
            import traceback
            traceback.print_exc()
            return []

    def _expand_by_concepts(
        self, concepts: List[str], limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        개념 기반 그래프 탐색 (Neo4j)

        Args:
            concepts: 개념 ID 리스트
            limit: 개념당 논문 개수

        Returns:
            논문 리스트
        """
        if not self.neo4j_repo:
            return []

        graph_papers = []

        for concept_id in concepts:
            # 개념과 연결된 논문 조회
            papers = self.neo4j_repo.get_papers_by_concept_graph(
                concept_id=concept_id,
                relation_types=['MENTIONS', 'INCREASES', 'SUPPORTS'],
                limit=limit,
            )

            for paper in papers:
                graph_papers.append({
                    'paper_id': paper['paper_id'],
                    'title': paper['title'],
                    'relation_type': paper['relation_type'],
                    'confidence': paper['confidence'],
                    'source_type': 'graph',
                    'concept_id': concept_id,
                })

        return graph_papers

    def _merge_and_rerank(
        self,
        vector_papers: List[Dict[str, Any]],
        graph_papers: List[Dict[str, Any]],
        top_k: int,
    ) -> List[Dict[str, Any]]:
        """
        Vector 검색 + Graph 검색 결과 병합 및 Reranking

        Args:
            vector_papers: Vector 검색 결과
            graph_papers: Graph 검색 결과
            top_k: 최종 결과 개수

        Returns:
            병합 및 재정렬된 논문 리스트
        """
        # paper_id를 키로 하는 논문 딕셔너리
        paper_map = {}

        # 1. Vector 검색 결과 추가 (similarity 기반)
        for paper in vector_papers:
            paper_id = paper.get('paper_id')
            if not paper_id:
                continue

            paper_map[paper_id] = {
                **paper,
                'vector_score': paper.get('similarity', 0.0),
                'graph_score': 0.0,
                'source_type': 'vector',
            }

        # 2. Graph 검색 결과 추가 (confidence 기반)
        for paper in graph_papers:
            paper_id = paper.get('paper_id')
            if not paper_id:
                continue

            confidence = paper.get('confidence', 0.0)

            if paper_id in paper_map:
                # 이미 존재하는 경우 graph_score 추가
                paper_map[paper_id]['graph_score'] = max(
                    paper_map[paper_id]['graph_score'],
                    confidence
                )
                paper_map[paper_id]['source_type'] = 'hybrid'
            else:
                # 새로운 논문 추가 (PostgreSQL에서 상세 정보 조회 필요)
                paper_map[paper_id] = {
                    'paper_id': paper_id,
                    'title': paper.get('title', ''),
                    'vector_score': 0.0,
                    'graph_score': confidence,
                    'source_type': 'graph',
                    'relation_type': paper.get('relation_type'),
                }

        # 3. 최종 점수 계산 (가중 평균)
        VECTOR_WEIGHT = 0.7  # Vector 검색 가중치 (0.6 → 0.7 증가)
        GRAPH_WEIGHT = 0.3   # Graph 검색 가중치 (0.4 → 0.3 감소)

        for paper_id, paper in paper_map.items():
            vector_score = paper.get('vector_score', 0.0)
            graph_score = paper.get('graph_score', 0.0)

            # 최종 점수 = 가중 평균
            final_score = (
                VECTOR_WEIGHT * vector_score +
                GRAPH_WEIGHT * graph_score
            )

            paper['final_score'] = final_score

        # 4. PostgreSQL에서 상세 정보 보강 (graph-only 논문)
        self._enrich_papers_from_postgresql(list(paper_map.values()))

        # 5. 점수 정규화 (선택)
        all_papers = list(paper_map.values())
        if all_papers:
            # 최고/최저 점수 찾기
            max_score = max(p.get('final_score', 0.0) for p in all_papers)
            min_score = min(p.get('final_score', 0.0) for p in all_papers)

            # 정규화 (0.0-1.0 범위로)
            if max_score > min_score:
                for paper in all_papers:
                    original_score = paper.get('final_score', 0.0)
                    normalized_score = (original_score - min_score) / (max_score - min_score)
                    paper['final_score'] = normalized_score
                    paper['original_score'] = original_score  # 원본 점수 보존

        # 6. 점수 기반 정렬 및 상위 K개 선택
        sorted_papers = sorted(
            all_papers,
            key=lambda x: x.get('final_score', 0.0),
            reverse=True
        )

        return sorted_papers[:top_k]

    def _enrich_papers_from_postgresql(self, papers: List[Dict[str, Any]]):
        """
        PostgreSQL에서 논문 상세 정보 조회하여 보강

        Args:
            papers: 논문 리스트 (in-place 업데이트)
        """
        if not self.session or not papers:
            return

        from sqlalchemy import text

        # paper_id 리스트 추출
        paper_ids = [p['paper_id'] for p in papers if 'paper_id' in p]
        if not paper_ids:
            return

        # PostgreSQL에서 상세 정보 조회
        query = text("""
            SELECT paper_id, title, chunk_text, lang, source, year, pmid, doi
            FROM paper_nodes
            WHERE paper_id = ANY(:paper_ids)
        """)

        results = self.session.execute(query, {'paper_ids': paper_ids}).fetchall()

        # paper_id를 키로 하는 맵 생성
        db_paper_map = {
            str(row[0]): {
                'title': row[1],
                'chunk_text': row[2],
                'lang': row[3],
                'source': row[4],
                'year': row[5],
                'pmid': row[6],
                'doi': row[7],
            }
            for row in results
        }

        # 논문 정보 보강
        for paper in papers:
            paper_id = str(paper.get('paper_id', ''))
            if paper_id in db_paper_map:
                # PostgreSQL 데이터로 업데이트 (기존 데이터는 유지)
                db_data = db_paper_map[paper_id]
                for key, value in db_data.items():
                    if key not in paper or not paper[key]:
                        paper[key] = value

    def close(self):
        """리소스 정리"""
        if self.session:
            self.session.close()
            self.session = None

        if self.neo4j_repo:
            self.neo4j_repo.close()
            self.neo4j_repo = None

    def __del__(self):
        """소멸자"""
        self.close()
