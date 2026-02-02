"""
Graph Expansion Pipeline Analyzer
- 완전 Deterministic Pipeline
- LLM Reasoning 제거
- Graph Hop 기반 자동 확장

Flow:
1. DB InBody Load
2. Rule-based Seed Extractor (하드코딩)
3. Graph Expansion Retriever (SQL Hop)
4. LLM Report Writer (글쓰기만)
5. DB Save
"""

from typing import Dict, Any, List, Optional
import sys
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
from pipeline_inbody_analysis_rag.rule_based_seed_extractor import RuleBasedSeedExtractor
from pipeline_inbody_analysis_rag.graph_expansion_retriever import GraphExpansionRetriever
from pipeline_inbody_analysis_rag.prompts_graph_expansion import create_report_writer_prompt


class InBodyAnalyzerGraphExpansion:
    """
    Graph Expansion Pipeline Analyzer

    완전 Deterministic:
    - Rule-based Seed 추출 (LLM 없음)
    - Graph Hop 확장 (SQL)
    - LLM은 글쓰기만
    """

    def __init__(
        self,
        llm_client: BaseLLMClient,
        model_version: str = "gpt-4o-mini",
        use_graph_expansion: bool = True
    ):
        """
        Args:
            llm_client: LLM 클라이언트 (글쓰기용)
            model_version: 모델 버전
            use_graph_expansion: Graph Expansion 사용 여부
        """
        self.llm_client = llm_client
        self.model_version = model_version
        self.use_graph_expansion = use_graph_expansion

        # Rule-based Seed Extractor
        self.seed_extractor = RuleBasedSeedExtractor()

        # Graph Expansion Retriever
        self.graph_retriever = None
        if use_graph_expansion:
            try:
                self.graph_retriever = GraphExpansionRetriever()
                print("  ✅ Graph Expansion Retriever 초기화 완료")
            except Exception as e:
                print(f"  ⚠️  Graph Expansion 초기화 실패: {e}")
                self.graph_retriever = None

    def analyze(
        self,
        user_id: int,
        measurements: InBodyMeasurements,
        source: str = "manual"
    ) -> Dict[str, Any]:
        """
        Graph Expansion Pipeline 실행

        Args:
            user_id: 사용자 ID
            measurements: InBody 측정 데이터
            source: 데이터 소스

        Returns:
            {
                "record_id": int,
                "analysis_id": int,
                "analysis_text": str,
                "seed_concepts": List[str],
                "risk_concepts": List[Dict],
                "intervention_concepts": List[Dict],
                "evidence_count": int
            }
        """
        output_lines = []

        def print_and_capture(*args, **kwargs):
            """print 출력을 캡처"""
            message = " ".join(str(arg) for arg in args)
            output_lines.append(message)
            print(*args, **kwargs)

        print_and_capture("=" * 60)
        print_and_capture(f"InBody Graph Expansion 분석 시작 (User ID: {user_id})")
        print_and_capture(f"  🔧 모델: {self.model_version}")
        print_and_capture(f"  🔧 Pipeline: Deterministic (Rule + Graph + LLM)")
        print_and_capture("=" * 60)

        # ==================== Step 1: Rule-based Seed 추출 ====================
        print_and_capture("\n📊 Step 1: Rule-based Seed Extraction (LLM 없음)...")

        try:
            # Seed 추출 + 체형 판정 자연어 생성
            seed_concept_ids = self.seed_extractor.extract_seeds(measurements)
            assessment_text = self.seed_extractor.generate_assessment_with_seeds(measurements)

            print_and_capture(f"  ✅ 추출된 Seeds: {seed_concept_ids}")
            print_and_capture(f"\n{assessment_text}\n")

        except Exception as e:
            print_and_capture(f"  ❌ Seed 추출 실패: {e}")
            raise e

        # ==================== Step 2: Graph Expansion ====================
        risk_concepts = []
        intervention_concepts = []
        evidence_chunks = []

        if self.use_graph_expansion and self.graph_retriever and seed_concept_ids:
            print_and_capture("\n🔍 Step 2: Graph Expansion (SQL Hop)...")

            try:
                expansion_result = self.graph_retriever.expand_and_retrieve(
                    seed_concept_ids=seed_concept_ids,
                    top_k_papers=20,
                    top_k_risks=10,
                    top_k_interventions=10,
                    top_k_evidence=5
                )

                seed_papers = expansion_result["seed_papers"]
                risk_concepts = expansion_result["risk_concepts"]
                intervention_concepts = expansion_result["intervention_concepts"]
                evidence_chunks = expansion_result["evidence_chunks"]

                print_and_capture(f"  ✅ 확장 완료:")
                print_and_capture(f"     - Papers: {len(seed_papers)}개")
                print_and_capture(f"     - Risk Concepts: {len(risk_concepts)}개")
                print_and_capture(f"     - Intervention Concepts: {len(intervention_concepts)}개")
                print_and_capture(f"     - Evidence Chunks: {len(evidence_chunks)}개")

            except Exception as e:
                print_and_capture(f"  ⚠️  Graph Expansion 실패: {e}")

        # ==================== Step 3: DB 저장 (health_records) ====================
        print_and_capture("\n💾 Step 3: 측정 데이터 저장...")
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

        # ==================== Step 4: LLM Report Writer (글쓰기만) ====================
        print_and_capture("\n📝 Step 4: LLM Report Writer (글쓰기만)...")

        try:
            system_prompt, user_prompt = create_report_writer_prompt(
                assessment_text=assessment_text,
                seed_concepts=seed_concept_ids,
                risk_concepts=risk_concepts,
                intervention_concepts=intervention_concepts,
                evidence_chunks=evidence_chunks,
                previous_record=None  # TODO: 이전 기록 조회
            )

            final_report = self.llm_client.generate_chat(system_prompt, user_prompt)
            print_and_capture(f"  ✅ 리포트 생성 완료 ({len(final_report)} 글자)")

        except Exception as e:
            print_and_capture(f"  ❌ LLM 리포트 생성 실패: {e}")
            raise e

        # ==================== Step 5: DB 저장 (analysis_reports) ====================
        print_and_capture("\n💾 Step 5: 분석 결과 저장...")
        try:
            full_analysis_text = "\n".join(output_lines) + "\n\n" + final_report

            analysis_data = AnalysisReportCreate(
                record_id=record_id,
                llm_output=full_analysis_text,
                model_version=self.model_version,
                analysis_type="inbody_graph_expansion"
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
        print_and_capture("✨ InBody Graph Expansion 분석 완료!")
        print_and_capture("=" * 60)

        return {
            "record_id": record_id,
            "analysis_id": analysis_id,
            "analysis_text": "\n".join(output_lines),
            "seed_concepts": seed_concept_ids,
            "risk_concepts": risk_concepts,
            "intervention_concepts": intervention_concepts,
            "evidence_count": len(evidence_chunks),
            "final_report": final_report
        }
