"""
Multi-Call 자연어 기반 Graph RAG 통합 테스트

테스트 순서:
1. Call1: 체형 판정 자연어 생성
2. Call2 Router: 자연어 → concept_id 추출
3. Call2 Tool: Graph RAG 검색
4. Call3: 최종 리포트 생성
"""

import sys
import json
import argparse
from pathlib import Path
from dotenv import load_dotenv

# 프로젝트 루트 경로 추가
project_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "backend"))
sys.path.insert(0, str(project_root / "src" / "llm"))

load_dotenv(project_root / ".env")

# 로컬 임포트
from llm_clients import create_llm_client

# Graph RAG 파이프라인
try:
    from pipeline_inbody_analysis_rag.analyzer_multi_call import InBodyAnalyzerMultiCall
    MULTI_CALL_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Multi-Call 임포트 실패: {e}")
    MULTI_CALL_AVAILABLE = False

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

        # 부위별
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


class MultiCallTester:
    """Multi-Call Graph RAG 테스터"""

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        use_graph_rag: bool = True,
        use_neo4j: bool = True
    ):
        self.model = model
        self.use_graph_rag = use_graph_rag

        print("=" * 70)
        print("🧪 Multi-Call Graph RAG 통합 테스트 초기화")
        print("=" * 70)
        print(f"  🔧 모델: {self.model}")
        print(f"  🔧 Multi-Call: ✅ Enabled")
        print(f"  🔧 Graph RAG: {'✅ Enabled' if use_graph_rag else '❌ Disabled'}")
        print(f"  🔧 Neo4j: {'✅ Enabled' if use_neo4j else '❌ Disabled'}")
        print()

        # LLM 클라이언트 초기화
        self.llm_client = create_llm_client(self.model)

        # Multi-Call Analyzer 초기화
        self.analyzer = None
        if self.use_graph_rag and MULTI_CALL_AVAILABLE:
            try:
                self.analyzer = InBodyAnalyzerMultiCall(
                    llm_client=self.llm_client,
                    model_version=self.model,
                    use_graph_rag=True,
                    use_neo4j=use_neo4j
                )
            except Exception as e:
                print(f"❌ Multi-Call Analyzer 초기화 실패: {e}")
                self.analyzer = None

        print("=" * 70)
        print()

    def load_sample_data(self, sample_name: str = "default") -> InBodyData:
        """샘플 데이터 로드"""
        pipeline_dir = project_root / "src" / "llm" / "pipeline_inbody_analysis_rag"

        sample_files = {
            "default": "sample_inbody_data.json",
            "gymnast": "sample_inbody_gymnast.json",
            "obese": "sample_inbody_obese.json",
            "skinnyfat": "sample_inbody_skinnyfat.json",
            "juggernaut": "sample_inbody_juggernaut.json",
        }

        filename = sample_files.get(sample_name, sample_files["default"])
        filepath = pipeline_dir / filename

        print(f"📂 샘플 데이터 로드: {filename}")

        if not filepath.exists():
            print(f"❌ 샘플 파일 없음: {filepath}")
            sys.exit(1)

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data_dict = json.load(f)

            # InBodyData 객체 생성
            inbody_data = InBodyData(**data_dict)
            print("  ✅ InBodyData 객체 생성 완료")
            print()

            return inbody_data

        except Exception as e:
            print(f"❌ 샘플 데이터 로드 실패: {e}")
            sys.exit(1)

    def test_multi_call_analysis(
        self,
        measurements: InBodyMeasurements,
        user_id: int = 999
    ) -> dict:
        """Multi-Call 전체 분석 테스트"""

        if not self.analyzer:
            print("❌ Multi-Call Analyzer가 없습니다.")
            return {}

        # InBodyData → InBodyMeasurements 변환
        if isinstance(measurements, InBodyData):
            measurements = convert_inbody_data_to_measurements(measurements)

        print("=" * 70)
        print("📝 Multi-Call Graph RAG 전체 분석 테스트")
        print("=" * 70)
        print()

        try:
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

            # Call별 결과 출력
            print("📊 Multi-Call 결과 요약:")
            print("-" * 70)
            print(f"\n[CALL 1: 체형 판정]\n")
            print(result.get("call1_assessment", "N/A"))
            print(f"\n[CALL 2: Concept IDs]\n")
            print(result.get("call2_concept_ids", []))
            print(f"\n[CALL 3: 최종 리포트]\n")
            print(result.get("call3_report", "N/A"))

            return {
                "record_id": result["record_id"],
                "analysis_id": result["analysis_id"],
                "analysis_text": result["analysis_text"],
                "model_version": self.model,
                "multi_call_used": True
            }

        except Exception as e:
            print(f"❌ 분석 실패: {e}")
            import traceback
            traceback.print_exc()
            return {}


def main():
    parser = argparse.ArgumentParser(description="Multi-Call Graph RAG 통합 테스트")
    parser.add_argument("--sample", default="default", help="샘플 데이터 선택 (default/gymnast/obese/skinnyfat)")
    parser.add_argument("--model", default="gpt-4o-mini", help="LLM 모델 선택")
    parser.add_argument("--no-rag", action="store_true", help="Graph RAG 비활성화")
    parser.add_argument("--no-neo4j", action="store_true", help="Neo4j 비활성화")
    parser.add_argument("--output", default="test_multi_call_result.json", help="결과 저장 파일명")

    args = parser.parse_args()

    # Tester 초기화
    tester = MultiCallTester(
        model=args.model,
        use_graph_rag=not args.no_rag,
        use_neo4j=not args.no_neo4j
    )

    # 샘플 데이터 로드
    inbody_data = tester.load_sample_data(args.sample)

    # Multi-Call 분석 실행
    result = tester.test_multi_call_analysis(inbody_data)

    # 결과 저장
    if result:
        output_path = Path(__file__).parent / args.output
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\n💾 결과 저장: {output_path}")

    print()
    print("=" * 70)
    print("✅ 테스트 완료")
    print("=" * 70)


if __name__ == "__main__":
    main()
