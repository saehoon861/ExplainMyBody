"""
Graph RAG 통합 테스트 스크립트

LLM Test SK 환경에서 Graph RAG를 사용하여 InBody 분석 테스트
- 모델: gpt-4o-mini
- Graph RAG: PostgreSQL + Neo4j
- 단독 실행 가능
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "backend"))
sys.path.insert(0, str(project_root / "src" / "llm"))

# 환경 변수 로드
from dotenv import load_dotenv
load_dotenv(project_root / ".env")

# 로컬 임포트
from llm_clients import create_llm_client
from prompt_generator import create_inbody_analysis_prompt

# Graph RAG 파이프라인
try:
    from pipeline_inbody_analysis_rag.analyzer import InBodyAnalyzerGraphRAG
    from pipeline_weekly_plan_rag.graph_rag_retriever import GraphRAGRetriever
    GRAPH_RAG_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Graph RAG 임포트 실패: {e}")
    GRAPH_RAG_AVAILABLE = False

# Backend 스키마
try:
    from schemas.inbody import InBodyData
    from shared.models import InBodyMeasurements
    BACKEND_SCHEMA_AVAILABLE = True
except ImportError:
    print("⚠️  InBody 스키마 임포트 실패")
    BACKEND_SCHEMA_AVAILABLE = False
    InBodyData = None
    InBodyMeasurements = None


def convert_inbody_data_to_measurements(data: InBodyData) -> InBodyMeasurements:
    """
    InBodyData (nested) → InBodyMeasurements (flat) 변환

    Args:
        data: InBodyData 객체 (nested 구조)

    Returns:
        InBodyMeasurements 객체 (flat 구조)
    """
    return InBodyMeasurements(
        # 기본 정보
        성별=data.기본정보.성별,
        나이=data.기본정보.연령,
        신장=data.기본정보.신장,
        체중=data.체중관리.체중,

        # 체성분
        무기질=data.체성분.무기질,
        체수분=data.체성분.체수분,
        단백질=data.체성분.단백질,
        체지방=data.체성분.체지방,
        골격근량=data.체중관리.골격근량,

        # 비만 지표
        BMI=data.비만분석.BMI,
        체지방률=data.비만분석.체지방률,
        복부지방률=data.비만분석.복부지방률,
        내장지방레벨=data.비만분석.내장지방레벨,
        비만도=data.비만분석.비만도,

        # 대사
        기초대사량=data.연구항목.기초대사량,
        적정체중=data.체중관리.적정체중,
        권장섭취열량=data.연구항목.권장섭취열량,

        # 조절
        체중조절=data.체중관리.체중조절,
        지방조절=data.체중관리.지방조절,
        근육조절=data.체중관리.근육조절,

        # 부위별 (부위명 매핑)
        근육_부위별등급={
            "왼팔": data.부위별근육분석.왼쪽팔,
            "오른팔": data.부위별근육분석.오른쪽팔,
            "몸통": data.부위별근육분석.복부,
            "왼다리": data.부위별근육분석.왼쪽하체,
            "오른다리": data.부위별근육분석.오른쪽하체,
        },
        체지방_부위별등급={
            "왼팔": data.부위별체지방분석.왼쪽팔,
            "오른팔": data.부위별체지방분석.오른쪽팔,
            "몸통": data.부위별체지방분석.복부,
            "왼다리": data.부위별체지방분석.왼쪽하체,
            "오른다리": data.부위별체지방분석.오른쪽하체,
        },

        # 체형 분류
        body_type1=data.body_type1,
        body_type2=data.body_type2,
    )


class GraphRAGTester:
    """Graph RAG 통합 테스터"""

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        use_graph_rag: bool = True,
        use_neo4j: bool = True
    ):
        """
        Args:
            model: LLM 모델 (기본: gpt-4o-mini)
            use_graph_rag: Graph RAG 사용 여부
            use_neo4j: Neo4j 그래프 탐색 사용 여부
        """
        self.model = model
        self.use_graph_rag = use_graph_rag and GRAPH_RAG_AVAILABLE

        print("=" * 70)
        print("🧪 Graph RAG 통합 테스트 초기화")
        print("=" * 70)
        print(f"  🔧 모델: {self.model}")
        print(f"  🔧 Graph RAG: {'✅ Enabled' if self.use_graph_rag else '❌ Disabled'}")
        print(f"  🔧 Neo4j: {'✅ Enabled' if use_neo4j else '❌ Disabled'}")
        print()

        # LLM 클라이언트 초기화
        self.llm_client = create_llm_client(self.model)

        # Graph RAG Analyzer 초기화
        self.analyzer = None
        if self.use_graph_rag:
            try:
                self.analyzer = InBodyAnalyzerGraphRAG(
                    llm_client=self.llm_client,
                    model_version=self.model,
                    use_graph_rag=True,
                    use_neo4j=use_neo4j
                )
                print("  ✅ Graph RAG Analyzer 초기화 완료")
            except Exception as e:
                print(f"  ❌ Graph RAG Analyzer 초기화 실패: {e}")
                self.use_graph_rag = False

        print("=" * 70)
        print()

    def load_sample_data(self, sample_name: str = "default") -> Optional[InBodyData]:
        """
        샘플 InBody 데이터 로드

        Args:
            sample_name: 샘플 이름 (default, gymnast, obese, skinnyfat, juggernaut)

        Returns:
            InBodyData 객체
        """
        # 샘플 파일 경로
        pipeline_dir = project_root / "src" / "llm" / "pipeline_inbody_analysis_rag"

        sample_files = {
            "default": "sample_inbody_data.json",
            "gymnast": "sample_inbody_gymnast.json",
            "obese": "sample_inbody_obese.json",
            "skinnyfat": "sample_inbody_skinnyfat.json",
            "juggernaut": "sample_inbody_juggernaut.json",
        }

        filename = sample_files.get(sample_name, sample_files["default"])
        sample_path = pipeline_dir / filename

        if not sample_path.exists():
            print(f"❌ 샘플 파일 없음: {sample_path}")
            return None

        try:
            with open(sample_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            print(f"📂 샘플 데이터 로드: {filename}")

            # InBodyData 객체 생성
            if BACKEND_SCHEMA_AVAILABLE:
                measurements = InBodyData(**data)
                print(f"  ✅ InBodyData 객체 생성 완료")
                return measurements
            else:
                print(f"  ⚠️  스키마 없음, dict 반환")
                return data

        except Exception as e:
            print(f"❌ 샘플 데이터 로드 실패: {e}")
            return None

    def test_graph_rag_retrieval(
        self,
        measurements: InBodyData,
        top_k: int = 10
    ):
        """
        Graph RAG 논문 검색 테스트

        Args:
            measurements: InBody 측정 데이터
            top_k: 검색할 논문 수
        """
        if not self.use_graph_rag or not self.analyzer or not self.analyzer.graph_rag:
            print("⚠️  Graph RAG가 비활성화되어 있습니다.")
            return

        print("=" * 70)
        print("📚 Graph RAG 논문 검색 테스트")
        print("=" * 70)
        print()

        try:
            # 1. 개념 추출
            print("🔍 1단계: 개념 추출...")
            concepts = self.analyzer._extract_concepts_from_measurements(measurements)
            print(f"  ✅ 추출된 개념: {', '.join(sorted(concepts))}")
            print()

            # 2. 검색 쿼리 생성
            print("🔍 2단계: 검색 쿼리 생성...")
            query = self.analyzer._generate_query_from_measurements(measurements)
            print(f"  ✅ 쿼리: {query[:100]}...")
            print()

            # 3. 논문 검색
            print(f"🔍 3단계: 논문 검색 (Top {top_k})...")
            papers = self.analyzer.graph_rag.retrieve_relevant_papers(
                query=query,
                concepts=list(concepts),
                top_k=top_k
            )
            print(f"  ✅ 검색된 논문: {len(papers)}개")
            print()

            # 4. 검색 결과 출력
            if papers:
                print("📄 검색 결과 (Top 5):")
                print("-" * 70)
                for i, paper in enumerate(papers[:5], 1):
                    print(f"\n{i}. {paper.get('title', 'N/A')}")
                    print(f"   출처: {paper.get('source', 'N/A')} ({paper.get('year', 'N/A')})")
                    print(f"   점수: Vector={paper.get('vector_score', 0):.3f}, "
                          f"Graph={paper.get('graph_score', 0):.3f}, "
                          f"Final={paper.get('final_score', 0):.3f}")
                    print(f"   초록: {paper.get('chunk_text', 'N/A')[:100]}...")
                print()

        except Exception as e:
            print(f"❌ Graph RAG 검색 실패: {e}")
            import traceback
            traceback.print_exc()

        print("=" * 70)
        print()

    def test_analysis_with_rag(
        self,
        measurements: InBodyData,
        user_id: int = 1
    ) -> Optional[Dict[str, Any]]:
        """
        Graph RAG를 사용한 전체 분석 테스트

        Args:
            measurements: InBody 측정 데이터
            user_id: 사용자 ID (테스트용)

        Returns:
            분석 결과 dict
        """
        if not self.use_graph_rag or not self.analyzer:
            print("⚠️  Graph RAG Analyzer가 없습니다. 기본 프롬프트 테스트를 실행합니다.")
            return self._test_basic_analysis(measurements)

        # InBodyData → InBodyMeasurements 변환
        if isinstance(measurements, InBodyData):
            measurements = convert_inbody_data_to_measurements(measurements)

        print("=" * 70)
        print("📝 Graph RAG 전체 분석 테스트")
        print("=" * 70)
        print()

        try:
            # InBodyAnalyzerGraphRAG의 analyze() 메서드 호출
            # 주의: DB 저장은 제외하고 분석만 수행
            result = self.analyzer.analyze(
                user_id=user_id,
                measurements=measurements,
                source="test"
            )

            print()
            print("=" * 70)
            print("✅ 분석 완료")
            print("=" * 70)
            print()
            print("📊 분석 결과:")
            print("-" * 70)
            print(result.get("analysis_text", "분석 텍스트 없음"))
            print()
            print("=" * 70)

            return result

        except Exception as e:
            print(f"❌ 분석 실패: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _test_basic_analysis(
        self,
        measurements: InBodyData
    ) -> Optional[Dict[str, Any]]:
        """
        Graph RAG 없는 기본 분석 (프롬프트만 테스트)

        Args:
            measurements: InBody 측정 데이터

        Returns:
            분석 결과 dict
        """
        print("=" * 70)
        print("📝 기본 분석 테스트 (Graph RAG 없음)")
        print("=" * 70)
        print()

        try:
            # 1. 프롬프트 생성
            print("🔨 프롬프트 생성...")
            system_prompt, user_prompt = create_inbody_analysis_prompt(
                measurements=measurements,
                body_type1=getattr(measurements, 'body_type1', None),
                body_type2=getattr(measurements, 'body_type2', None)
            )

            print(f"  ✅ System Prompt: {len(system_prompt)}자")
            print(f"  ✅ User Prompt: {len(user_prompt)}자")
            print()

            # 2. LLM 호출
            print("🤖 LLM 호출 중...")
            analysis_text = self.llm_client.generate_chat(
                system_prompt=system_prompt,
                user_prompt=user_prompt
            )

            print(f"  ✅ 응답 생성 완료 ({len(analysis_text)}자)")
            print()

            # 3. 결과 출력
            print("=" * 70)
            print("📊 분석 결과:")
            print("-" * 70)
            print(analysis_text)
            print()
            print("=" * 70)

            return {
                "analysis_text": analysis_text,
                "system_prompt": system_prompt,
                "user_prompt": user_prompt
            }

        except Exception as e:
            print(f"❌ 분석 실패: {e}")
            import traceback
            traceback.print_exc()
            return None

    def save_result(
        self,
        result: Dict[str, Any],
        output_file: str = "test_result.json"
    ):
        """
        테스트 결과 저장

        Args:
            result: 분석 결과
            output_file: 출력 파일명
        """
        output_path = Path(__file__).parent / output_file

        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)

            print(f"💾 결과 저장: {output_path}")

        except Exception as e:
            print(f"❌ 결과 저장 실패: {e}")


def main():
    """메인 실행 함수"""

    parser = argparse.ArgumentParser(description="Graph RAG 통합 테스트")
    parser.add_argument(
        "--sample",
        type=str,
        default="default",
        choices=["default", "gymnast", "obese", "skinnyfat", "juggernaut"],
        help="샘플 데이터 선택"
    )
    parser.add_argument(
        "--no-rag",
        action="store_true",
        help="Graph RAG 비활성화"
    )
    parser.add_argument(
        "--no-neo4j",
        action="store_true",
        help="Neo4j 비활성화 (Vector Search만)"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="gpt-4o-mini",
        help="LLM 모델 (기본: gpt-4o-mini)"
    )
    parser.add_argument(
        "--test-retrieval",
        action="store_true",
        help="논문 검색만 테스트"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="test_result.json",
        help="결과 저장 파일명"
    )

    args = parser.parse_args()

    # Tester 초기화
    tester = GraphRAGTester(
        model=args.model,
        use_graph_rag=not args.no_rag,
        use_neo4j=not args.no_neo4j
    )

    # 샘플 데이터 로드
    measurements = tester.load_sample_data(args.sample)

    if not measurements:
        print("❌ 샘플 데이터 로드 실패. 종료합니다.")
        return

    print()

    # 테스트 실행
    if args.test_retrieval:
        # 논문 검색만 테스트
        tester.test_graph_rag_retrieval(measurements, top_k=10)
    else:
        # 전체 분석 테스트
        result = tester.test_analysis_with_rag(measurements, user_id=999)

        if result:
            # 결과 저장
            tester.save_result(result, args.output)

    print()
    print("=" * 70)
    print("✅ 테스트 완료")
    print("=" * 70)


if __name__ == "__main__":
    main()
