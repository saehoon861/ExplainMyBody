"""
Multi-Call 자연어 기반 InBody 분석기
- Call1: 체형 판정 (자연어)
- Call2: Router (concept_id 추출) + Graph RAG 검색
- Call3: 최종 리포트 생성
"""

from typing import Dict, Any, List, Optional
import sys
import json
from pathlib import Path

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "backend"))

from shared.models import InBodyMeasurements
from shared.llm_clients import BaseLLMClient
from backend.database import SessionLocal
from backend.repositories.common.health_record_repository import HealthRecordRepository
from backend.repositories.llm.analysis_report_repository import AnalysisReportRepository
from backend.schemas.common import HealthRecordCreate
from backend.schemas.llm import AnalysisReportCreate
from pipeline_inbody_analysis_rag.prompts_multi_call import (
    create_body_assessment_prompt,
    create_concept_router_prompt,
    create_final_report_prompt
)
from pipeline_weekly_plan_rag.graph_rag_retriever import GraphRAGRetriever
from pipeline_inbody_analysis_rag.concept_definitions import get_concept_name


class InBodyAnalyzerMultiCall:
    """
    Multi-Call 자연어 기반 InBody 분석기

    Flow:
    1. Tool0: DB에서 measurements 불러오기 (선택)
    2. Call1: 체형 판정 자연어 생성
    3. Call2-1 Router: 자연어 → concept_id[] 추출
    4. Call2-2 Tool: Graph RAG 검색
    5. Call3: 최종 리포트 (Evidence 통합)
    """

    def __init__(
        self,
        llm_client: BaseLLMClient,
        model_version: str = "gpt-4o-mini",
        use_graph_rag: bool = True,
        use_neo4j: bool = True
    ):
        """
        Args:
            llm_client: LLM 클라이언트
            model_version: 모델 버전
            use_graph_rag: Graph RAG 사용 여부
            use_neo4j: Neo4j 그래프 탐색 사용 여부
        """
        self.llm_client = llm_client
        self.model_version = model_version
        self.use_graph_rag = use_graph_rag

        # Graph RAG 초기화
        self.graph_rag = None
        if use_graph_rag:
            try:
                self.graph_rag = GraphRAGRetriever(
                    embedder_type="openai",
                    use_neo4j=use_neo4j
                )
                print("  ✅ Graph RAG Analyzer (Multi-Call) 초기화 완료")
            except Exception as e:
                print(f"  ⚠️  Graph RAG 초기화 실패: {e}")
                self.graph_rag = None

    def analyze(
        self,
        user_id: int,
        measurements: InBodyMeasurements,
        source: str = "manual"
    ) -> Dict[str, Any]:
        """
        Multi-Call 기반 InBody 분석 실행

        Args:
            user_id: 사용자 ID
            measurements: InBody 측정 데이터
            source: 데이터 소스

        Returns:
            {
                "record_id": int,
                "analysis_id": int,
                "analysis_text": str,
                "call1_assessment": str,
                "call2_concept_ids": List[str],
                "call3_report": str
            }
        """
        output_lines = []

        def print_and_capture(*args, **kwargs):
            """print 출력을 캡처하면서 동시에 콘솔에도 출력"""
            message = " ".join(str(arg) for arg in args)
            output_lines.append(message)
            print(*args, **kwargs)

        print_and_capture("=" * 60)
        print_and_capture(f"InBody Multi-Call 분석 시작 (User ID: {user_id})")
        print_and_capture(f"  🔧 모델: {self.model_version}")
        print_and_capture(
            f"  🔧 Graph RAG: {'✅ Enabled' if self.use_graph_rag else '❌ Disabled'}"
        )
        print_and_capture("=" * 60)

        # ==================== CALL 1: 체형 판정 ====================
        print_and_capture("\n📊 CALL 1: 체형 판정 (자연어 생성)...")

        try:
            system_prompt, user_prompt = create_body_assessment_prompt(measurements)
            call1_assessment = self.llm_client.generate_chat(system_prompt, user_prompt)
            print_and_capture(f"  ✅ 체형 판정 완료 ({len(call1_assessment)} 글자)")
            print_and_capture(f"\n{call1_assessment}\n")
        except Exception as e:
            print_and_capture(f"  ❌ Call1 실패: {e}")
            raise e

        # ==================== CALL 2: Router + Graph RAG ====================
        concept_ids = []
        evidence_chunks = []

        if self.use_graph_rag and self.graph_rag:
            print_and_capture("\n🔍 CALL 2-1: Concept Router (자연어 → concept_id)...")

            try:
                system_prompt, user_prompt = create_concept_router_prompt(call1_assessment)
                router_output = self.llm_client.generate_chat(system_prompt, user_prompt)

                # JSON 파싱
                router_output = router_output.strip()
                if router_output.startswith("```"):
                    # 코드 블록 제거
                    router_output = router_output.split("```")[1]
                    if router_output.startswith("json"):
                        router_output = router_output[4:]
                    router_output = router_output.strip()

                concept_ids = json.loads(router_output)
                print_and_capture(f"  ✅ 추출된 concept_ids: {concept_ids}")

            except Exception as e:
                print_and_capture(f"  ⚠️  Router 실패: {e}, 기본 concept 사용")
                # Fallback: 기본 concept
                concept_ids = ["body_composition", "skeletal_muscle_mass", "body_fat_percentage"]

            print_and_capture("\n🔍 CALL 2-2: Graph RAG 검색...")

            try:
                # Graph RAG로 논문 검색
                papers = self.graph_rag.hybrid_search(
                    query="인바디 체성분 분석",  # 더미 쿼리 (concept 기반 검색)
                    concept_ids=concept_ids,
                    top_k=5
                )

                print_and_capture(f"  ✅ 검색된 논문: {len(papers)}개")

                # Evidence 형식으로 변환
                for paper in papers:
                    for cid in concept_ids:
                        evidence_chunks.append({
                            "concept_id": cid,
                            "chunk_text": paper.get("chunk_text", ""),
                            "chunk_ko_summary": paper.get("chunk_ko_summary", ""),
                            "title": paper.get("title", ""),
                            "final_score": paper.get("final_score", 0.0)
                        })

                # Top 5개만 유지
                evidence_chunks = evidence_chunks[:5]

            except Exception as e:
                print_and_capture(f"  ⚠️  Graph RAG 검색 실패: {e}")
                evidence_chunks = []

        # ==================== DB 저장: health_records ====================
        print_and_capture("\n💾 3단계: 측정 데이터 저장...")
        db_session = SessionLocal()
        try:
            m = measurements.model_dump()
            health_record_data = HealthRecordCreate(
                measurements=m,
                source=source,
                measured_at=None
            )
            record = HealthRecordRepository.create(db_session, user_id, health_record_data)
            record_id = record.id
            print_and_capture(f"  ✓ Record ID: {record_id}")
        except Exception as e:
            db_session.rollback()
            raise e

        # ==================== CALL 3: 최종 리포트 ====================
        print_and_capture("\n📝 CALL 3: 최종 리포트 생성 (Evidence 통합)...")

        try:
            system_prompt, user_prompt = create_final_report_prompt(
                body_assessment_text=call1_assessment,
                evidence_chunks=evidence_chunks,
                previous_record=None  # TODO: 이전 기록 조회
            )
            call3_report = self.llm_client.generate_chat(system_prompt, user_prompt)
            print_and_capture(f"  ✅ 최종 리포트 완료 ({len(call3_report)} 글자)")

        except Exception as e:
            print_and_capture(f"  ❌ Call3 실패: {e}")
            raise e

        # ==================== DB 저장: analysis_reports ====================
        print_and_capture("\n💾 6단계: 분석 결과 저장...")
        try:
            # 전체 분석 텍스트 결합
            full_analysis_text = "\n".join(output_lines) + "\n\n" + call3_report

            analysis_data = AnalysisReportCreate(
                record_id=record_id,
                llm_output=full_analysis_text,
                model_version=self.model_version,
                analysis_type="inbody_multi_call_rag"
            )
            analysis_report = AnalysisReportRepository.create(db_session, analysis_data)
            analysis_id = analysis_report.id
            print_and_capture(f"  ✓ Analysis ID: {analysis_id}")

            db_session.commit()
        except Exception as e:
            db_session.rollback()
            raise e
        finally:
            db_session.close()

        print_and_capture("\n" + "=" * 60)
        print_and_capture("✨ InBody Multi-Call 분석 완료!")
        print_and_capture("=" * 60)

        return {
            "record_id": record_id,
            "analysis_id": analysis_id,
            "analysis_text": "\n".join(output_lines),
            "call1_assessment": call1_assessment,
            "call2_concept_ids": concept_ids,
            "call3_report": call3_report
        }
