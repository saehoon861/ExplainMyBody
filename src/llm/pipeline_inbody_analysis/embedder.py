"""
임베딩 생성 및 저장 (OpenAI + Ollama bge-m3)
"""

from typing import List, Optional
from shared.llm_clients import BaseLLMClient, OpenAIClient, OllamaClient
from shared.database import Database


class InBodyEmbedder:
    """인바디 분석 결과 임베딩 (OpenAI 1536차원 + Ollama bge-m3 1024차원)"""

    def __init__(
        self,
        db: Database,
        llm_client: BaseLLMClient,
        embedding_model: Optional[str] = None,
    ):
        """
        Args:
            db: Database 인스턴스
            llm_client: LLM 클라이언트 (분석에 사용된 모델)
            embedding_model: 임베딩 모델 이름 (None이면 클라이언트 기본값 사용)
        """
        self.db = db
        self.llm_client = llm_client
        self.embedding_model = embedding_model

    def create_and_save_embedding(
        self, analysis_id: int, analysis_text: str
    ) -> Optional[dict]:
        """
        분석 텍스트를 임베딩하고 DB에 저장 (OpenAI + Ollama 동시 생성)

        Args:
            analysis_id: 분석 리포트 ID
            analysis_text: 분석 텍스트

        Returns:
            {"embedding_1536": [...], "embedding_1024": [...]} 또는 None
        """
        print("\n🔢 임베딩 생성 중...")

        try:
            embedding_1536 = None
            embedding_1024 = None

            # 1. OpenAI 임베딩 생성 (1536차원)
            try:
                openai_client = OpenAIClient()
                if hasattr(openai_client, "create_embedding"):
                    embedding_1536 = openai_client.create_embedding(text=analysis_text)
                    print(
                        f"  ✓ OpenAI 임베딩 생성 완료 (차원: {len(embedding_1536)})"
                    )
            except Exception as e:
                print(f"  ⚠️  OpenAI 임베딩 생성 실패: {e}")

            # 2. Ollama bge-m3 임베딩 생성 (1024차원)
            try:
                ollama_client = OllamaClient(
                    model="bge-m3:latest", embedding_model="bge-m3:latest"
                )
                if hasattr(ollama_client, "create_embedding"):
                    embedding_1024 = ollama_client.create_embedding(text=analysis_text)
                    print(
                        f"  ✓ Ollama bge-m3 임베딩 생성 완료 (차원: {len(embedding_1024)})"
                    )
            except Exception as e:
                print(f"  ⚠️  Ollama 임베딩 생성 실패: {e}")

            # 3. DB에 임베딩 저장
            if embedding_1536 or embedding_1024:
                success = self.db.update_analysis_embedding(
                    analysis_id,
                    embedding_1536=embedding_1536,
                    embedding_1024=embedding_1024,
                )

                if success:
                    print(f"  ✓ 임베딩 저장 완료 (Analysis ID: {analysis_id})")
                    saved = []
                    if embedding_1536:
                        saved.append("1536D")
                    if embedding_1024:
                        saved.append("1024D")
                    print(f"    저장된 임베딩: {', '.join(saved)}")
                else:
                    print(f"  ⚠️  임베딩 저장 실패: 리포트를 찾을 수 없습니다")

                return {
                    "embedding_1536": embedding_1536,
                    "embedding_1024": embedding_1024,
                }
            else:
                print("  ⚠️  임베딩 생성 실패: OpenAI와 Ollama 모두 실패")
                return None

        except Exception as e:
            print(f"  ⚠️  임베딩 생성/저장 실패: {e}")
            import traceback

            traceback.print_exc()
            return None
