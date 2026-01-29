"""
Vector RAG 검색 (SQLAlchemy + pgvector + Reranking)
- OpenAI 1536차원 또는 Ollama bge-m3 1024차원 임베딩 사용
- 시간 가중치 기반 Reranking (자연로그 decay)
"""

from typing import List, Dict, Any, Optional
from shared.database import Database
from shared.llm_clients import OpenAIClient, OllamaClient


class InBodyRAGRetriever:
    """
    인바디 분석 결과 벡터 검색 (pgvector + Reranking)
    - OpenAI (1536D) 또는 Ollama bge-m3 (1024D) 자동 선택
    """

    def __init__(self, db: Database, use_ollama: bool = False):
        """
        Args:
            db: Database 인스턴스 (SQLAlchemy)
            use_ollama: Ollama bge-m3 사용 여부 (False=OpenAI, True=Ollama)
        """
        self.db = db
        self.use_ollama = use_ollama

        if use_ollama:
            self.embedding_client = OllamaClient(
                model="bge-m3:latest", embedding_model="bge-m3:latest"
            )
            self.embedding_dim = 1024
            print("  🔧 RAG Embedder: Ollama bge-m3 (1024D)")
        else:
            self.embedding_client = OpenAIClient()
            self.embedding_dim = 1536
            print("  🔧 RAG Embedder: OpenAI (1536D)")

    def retrieve_similar_analyses(
        self, user_id: int, query: str, top_k: int = 6
    ) -> List[Dict[str, Any]]:
        """
        유사한 인바디 분석 검색 (Vector RAG + Reranking)

        Args:
            user_id: 사용자 ID
            query: 검색 쿼리 (자연어)
            top_k: 상위 K개 결과 (기본 6개)

        Returns:
            유사도 + 시간 가중치가 반영된 분석 리포트 리스트
        """
        print(f"\n🔍 Vector RAG 검색 중 (top_k={top_k})...")

        try:
            # 1. 쿼리를 임베딩으로 변환
            print(f"  - 쿼리 임베딩 생성 중: '{query[:50]}...'")
            query_embedding = self.embedding_client.create_embedding(text=query)
            print(f"  ✓ 쿼리 임베딩 완료 (차원: {len(query_embedding)})")

            # 2. pgvector로 유사도 검색 + Reranking
            results = self.db.search_similar_analyses(
                user_id=user_id,
                query_embedding=query_embedding,
                top_k=top_k,
                embedding_dim=self.embedding_dim,
                rerank=True,  # 시간 가중치 reranking 활성화
            )

            if results:
                print(f"  ✓ {len(results)}개 유사 분석 검색 완료 (Reranked)")
                for i, r in enumerate(results, 1):
                    print(
                        f"    {i}. Score: {r.get('rerank_score', 0):.3f} "
                        f"(Sim: {r['similarity']:.3f}, "
                        f"Time: {r.get('time_weight', 0):.3f}, "
                        f"Days: {r.get('days_ago', 0)})"
                    )
                return results
            else:
                # 임베딩이 없는 경우 fallback
                print("  ⚠️  임베딩된 분석이 없습니다. 최신 분석을 반환합니다.")
                return self._fallback_to_latest(user_id, top_k)

        except Exception as e:
            print(f"  ⚠️  Vector 검색 실패: {e}")
            print("     최신 분석으로 fallback합니다.")
            import traceback

            traceback.print_exc()
            return self._fallback_to_latest(user_id, top_k)

    def _fallback_to_latest(
        self, user_id: int, limit: int = 6
    ) -> List[Dict[str, Any]]:
        """
        Vector 검색 실패 시 최신 분석 반환

        Args:
            user_id: 사용자 ID
            limit: 개수

        Returns:
            최신 분석 리포트 리스트
        """
        try:
            reports = self.db.get_user_analysis_reports(user_id, limit=limit)
            results = []

            for report in reports:
                # 전체 llm_output 가져오기 위해 다시 조회
                full_report = self.db.get_analysis_report(report["id"])
                if full_report:
                    results.append(
                        {
                            "id": full_report["id"],
                            "analysis_text": full_report["llm_output"],
                            "report_date": full_report["report_date"],
                            "similarity": 1.0,  # fallback은 similarity 1.0
                            "rerank_score": 1.0,
                            "time_weight": 1.0,
                            "days_ago": 0,
                        }
                    )

            print(f"  ✓ {len(results)}개 최신 분석 반환")
            return results

        except Exception as e:
            print(f"  ❌ Fallback 실패: {e}")
            return []

    def retrieve_latest_analysis(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        사용자의 최신 인바디 분석 조회

        Args:
            user_id: 사용자 ID

        Returns:
            최신 분석 리포트
        """
        results = self._fallback_to_latest(user_id, limit=1)
        return results[0] if results else None
