"""
인바디 분석 로직 (Graph RAG 적용)
- InBody 데이터 분석
- Graph RAG로 관련 논문 검색
- 항상 gpt-4o-mini 사용
- Database 클래스 의존성 제거 (직접 repository 사용)
"""

from typing import Dict, Any, List
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
from pipeline_inbody_analysis_rag.prompt_generator import create_inbody_analysis_prompt
from pipeline_weekly_plan_rag.graph_rag_retriever import GraphRAGRetriever


class InBodyAnalyzerGraphRAG:
    """인바디 분석기 (Graph RAG 적용)"""

    def __init__(
        self,
        llm_client: BaseLLMClient,
        model_version: str = "gpt-4o-mini",
        use_graph_rag: bool = True,
        use_neo4j: bool = True,
    ):
        """
        Args:
            llm_client: LLM 클라이언트
            model_version: 모델 버전 (항상 gpt-4o-mini)
            use_graph_rag: Graph RAG 사용 여부 (기본: True)
            use_neo4j: Neo4j 그래프 탐색 사용 여부 (기본: True)
        """
        self.llm_client = llm_client
        self.model_version = model_version
        self.use_graph_rag = use_graph_rag

        # Graph RAG Retriever (논문만 사용)
        self.graph_rag = None
        if use_graph_rag:
            try:
                self.graph_rag = GraphRAGRetriever(use_neo4j=use_neo4j)
                print("  ✅ Graph RAG 활성화")
            except Exception as e:
                print(f"  ⚠️  Graph RAG 초기화 실패: {e}")
                self.use_graph_rag = False

    def analyze(
        self,
        user_id: int,
        measurements: InBodyMeasurements,
        source: str = "manual",
    ) -> Dict[str, Any]:
        """
        전체 인바디 분석 수행 (Graph RAG 적용)

        Args:
            user_id: 사용자 ID
            measurements: InBody 측정 데이터
            source: 데이터 소스

        Returns:
            {
                "record_id": int,
                "analysis_id": int,
                "analysis_text": str,
            }
        """
        # 출력 메시지를 수집하기 위한 리스트
        output_lines = []

        def print_and_capture(*args, **kwargs):
            """print 출력을 캡처하면서 동시에 콘솔에도 출력"""
            message = " ".join(str(arg) for arg in args)
            output_lines.append(message)
            print(*args, **kwargs)

        print_and_capture("=" * 60)
        print_and_capture(f"InBody 분석 시작 (User ID: {user_id}, Graph RAG)")
        print_and_capture(f"  🔧 모델: {self.model_version}")
        print_and_capture(
            f"  🔧 Graph RAG: {'✅ Enabled' if self.use_graph_rag else '❌ Disabled'}"
        )
        print_and_capture("=" * 60)

        # 1단계: 체형 정보 확인
        print_and_capture("\n📊 1단계: 체형 정보 확인...")
        if measurements.body_type1:
            print_and_capture(f"  ✓ Body Type 1: {measurements.body_type1}")
        if measurements.body_type2:
            print_and_capture(f"  ✓ Body Type 2: {measurements.body_type2}")
        if not measurements.body_type1 and not measurements.body_type2:
            print_and_capture("  ⚠️  체형 정보 없음 (body_type1, body_type2 미입력)")

        # 2단계: Graph RAG 논문 검색
        paper_context = []
        if self.use_graph_rag and self.graph_rag:
            print_and_capture("\n🔍 2단계: Graph RAG 논문 검색...")

            # 체형 및 건강 상태에서 핵심 개념 추출
            concepts = self._extract_concepts_from_measurements(measurements)

            # 쿼리 생성
            query = self._generate_query_from_measurements(measurements)

            # Graph RAG 검색
            paper_context = self.graph_rag.retrieve_relevant_papers(
                query=query,
                concepts=concepts,
                top_k=10,  # 5 → 10으로 증가 (더 다양한 결과)
                domain=None,  # 도메인 자동 추론
                lang=None,  # 언어 필터 제거 (영어 논문 포함)
            )

            if paper_context:
                print_and_capture(f"  ✓ {len(paper_context)}개 관련 논문 검색 완료")
            else:
                print_and_capture("  ⚠️  관련 논문이 없습니다.")

        # 3단계: health_records에 저장
        print_and_capture("\n💾 3단계: 측정 데이터 저장...")
        db_session = SessionLocal()
        try:
            m = measurements.model_dump()
            health_record_data = HealthRecordCreate(
                measurements=m,
                source=source,
                measured_at=None  # 현재 시간 사용
            )
            record = HealthRecordRepository.create(db_session, user_id, health_record_data)
            record_id = record.id
            print_and_capture(f"  ✓ Record ID: {record_id}")
        except Exception as e:
            db_session.rollback()
            raise e

        # 4단계: 프롬프트 생성 (Graph RAG 컨텍스트 포함)
        print_and_capture("\n📝 4단계: 프롬프트 생성...")
        system_prompt, user_prompt = create_inbody_analysis_prompt(
            measurements,
            paper_context=paper_context
        )

        # 5단계: LLM 분석 (gpt-4o-mini)
        print_and_capture(f"\n🤖 5단계: LLM 분석 생성 ({self.model_version})...")
        print_and_capture("  - LLM 호출 중...")
        analysis_text = self.llm_client.generate_chat(system_prompt, user_prompt)
        print_and_capture(f"  ✓ 분석 완료 ({len(analysis_text)} 글자)")

        # 6단계: 분석 결과 저장
        print_and_capture("\n💾 6단계: 분석 결과 저장...")
        try:
            analysis_data = AnalysisReportCreate(
                record_id=record_id,
                llm_output=analysis_text,
                model_version=self.model_version,
                analysis_type="inbody_graph_rag"
            )
            report = AnalysisReportRepository.create(db_session, user_id, analysis_data)
            analysis_id = report.id
            print_and_capture(f"  ✓ Analysis ID: {analysis_id}")
        except Exception as e:
            db_session.rollback()
            raise e
        finally:
            db_session.close()

        print_and_capture("\n" + "=" * 60)
        print_and_capture("✨ InBody 분석 완료!")
        print_and_capture("=" * 60)

        # 전체 출력 메시지와 LLM 분석 결과를 결합
        full_output = "\n".join(output_lines) + "\n\n" + "=" * 60 + "\n"
        full_output += "📋 LLM 분석 리포트\n"
        full_output += "=" * 60 + "\n\n"
        full_output += analysis_text

        return {
            "record_id": record_id,
            "analysis_id": analysis_id,
            "analysis_text": full_output,
        }

    def _extract_concepts_from_measurements(
        self, measurements: InBodyMeasurements
    ) -> List[str]:
        """
        InBody 측정 데이터에서 핵심 개념 추출

        Args:
            measurements: InBody 측정 데이터

        Returns:
            개념 ID 리스트
        """
        concepts = set()

        # 체지방률 기반
        if measurements.체지방률:
            high_threshold = 25 if measurements.성별 == "남성" else 30
            low_threshold = 10 if measurements.성별 == "남성" else 20

            if measurements.체지방률 > high_threshold:
                concepts.add("fat_loss")
                concepts.add("body_fat_percentage")
            elif measurements.체지방률 < low_threshold:
                concepts.add("lean_mass")

        # 골격근량 기반
        if measurements.근육조절:
            if measurements.근육조절 > 0:
                concepts.update(["muscle_hypertrophy", "resistance_training", "protein_intake"])
            elif measurements.근육조절 < 0:
                concepts.add("muscle_loss_prevention")

        # 내장지방 기반
        if measurements.내장지방레벨 and measurements.내장지방레벨 > 10:
            concepts.update(["visceral_fat", "metabolic_health", "cardiovascular_health"])

        # BMI 기반
        if measurements.BMI:
            if measurements.BMI < 18.5:
                concepts.add("underweight")
            elif measurements.BMI >= 25:
                concepts.update(["overweight", "weight_loss", "caloric_deficit"])

        # 기초대사량 - 데이터가 적어서 주석 처리
        # if measurements.기초대사량:
        #     concepts.add("basal_metabolic_rate")

        # 기본 개념 추가 (데이터가 많은 개념들)
        if not concepts:
            concepts.update(["protein_intake", "body_composition", "skeletal_muscle_mass"])

        return list(concepts)

    def _generate_query_from_measurements(self, measurements: InBodyMeasurements) -> str:
        """
        InBody 측정 데이터에서 검색 쿼리 생성

        Args:
            measurements: InBody 측정 데이터

        Returns:
            검색 쿼리 문자열
        """
        query_parts = []

        # 주요 개선 목표
        if measurements.근육조절 and measurements.근육조절 > 2:
            query_parts.append("근육 증가")
        if measurements.지방조절 and measurements.지방조절 < -2:
            query_parts.append("체지방 감소")

        # 건강 위험 요소
        if measurements.내장지방레벨 and measurements.내장지방레벨 > 10:
            query_parts.append("내장지방 감소")
        if measurements.복부지방률 and float(measurements.복부지방률) > 0.9:
            query_parts.append("복부 비만 개선")

        # 기본 쿼리
        if not query_parts:
            query_parts.append("체성분 개선")

        query = f"{' '.join(query_parts)} 방법 및 효과"
        return query

    def __del__(self):
        """소멸자 - 리소스 정리"""
        if self.graph_rag:
            self.graph_rag.close()
