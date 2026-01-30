#!/usr/bin/env python3
"""
InBody 분석 파이프라인 실행 파일 (Graph RAG 적용)
- 항상 gpt-4o-mini 및 text-embedding-3-small 사용
- Graph RAG (Vector + Graph Traversal) 자동 적용
- Database 클래스 의존성 제거
"""

import sys
import argparse
import json
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.llm_clients import create_llm_client
from shared.models import InBodyMeasurements, InBodyAnalysisResponse

from pipeline_inbody_analysis_rag.analyzer import InBodyAnalyzerGraphRAG

load_dotenv()


def run_inbody_analysis_with_graph_rag(
    user_id: int,
    measurements_dict: dict,
    use_neo4j: bool = True,
) -> InBodyAnalysisResponse:
    """
    인바디 분석 파이프라인 실행 (Graph RAG 적용)

    Args:
        user_id: 사용자 ID
        measurements_dict: InBody 측정 데이터 (dict)
        use_neo4j: Neo4j 그래프 탐색 사용 여부

    Returns:
        InBodyAnalysisResponse
    """
    try:
        # 1. Pydantic 모델 검증
        measurements = InBodyMeasurements(**measurements_dict)

        # 2. LLM 클라이언트 초기화 (항상 gpt-4o-mini)
        model = "gpt-4o-mini"
        llm_client = create_llm_client(model)

        print(f"✅ LLM 초기화 완료")
        print(f"🤖 LLM 모델: {model} (고정)")
        print(f"📊 Embedding: text-embedding-3-small (고정)")

        # 3. InBody 분석 수행 (Graph RAG 자동 적용)
        analyzer = InBodyAnalyzerGraphRAG(
            llm_client=llm_client,
            model_version=model,
            use_graph_rag=True,  # 항상 Graph RAG 사용
            use_neo4j=use_neo4j,
        )
        result = analyzer.analyze(user_id, measurements, source="manual")

        # 4. 성공 응답
        return InBodyAnalysisResponse(
            success=True,
            record_id=result["record_id"],
            analysis_id=result["analysis_id"],
            analysis_text=result["analysis_text"],
        )

    except Exception as e:
        # 에러 응답
        print(f"\n❌ 오류 발생: {e}")
        import traceback

        traceback.print_exc()

        return InBodyAnalysisResponse(success=False, error=str(e))


def main():
    parser = argparse.ArgumentParser(description="InBody 분석 파이프라인 (Graph RAG)")

    # 필수 인자
    parser.add_argument("--user-id", type=int, required=True, help="사용자 ID")

    # 측정 데이터 입력 방법
    parser.add_argument("--measurements-json", type=str, help="측정 데이터 JSON 문자열")
    parser.add_argument("--measurements-file", type=str, help="측정 데이터 JSON 파일 경로")

    # 선택적 인자
    parser.add_argument("--output-file", type=str, help="결과를 저장할 TXT 파일 경로")
    parser.add_argument(
        "--no-neo4j",
        action="store_true",
        help="Neo4j 그래프 탐색 비활성화 (Vector만 사용)",
    )

    args = parser.parse_args()

    # 측정 데이터 로드
    if args.measurements_json:
        measurements_dict = json.loads(args.measurements_json)
    elif args.measurements_file:
        with open(args.measurements_file, "r", encoding="utf-8") as f:
            measurements_dict = json.load(f)
    else:
        print("오류: --measurements-json 또는 --measurements-file 중 하나 필수")
        sys.exit(1)

    # 분석 실행 (Graph RAG 자동 적용)
    response = run_inbody_analysis_with_graph_rag(
        user_id=args.user_id,
        measurements_dict=measurements_dict,
        use_neo4j=not args.no_neo4j,
    )

    # 결과 출력
    print("\n" + "=" * 60)
    print("📋 분석 결과 (Graph RAG)")
    print("=" * 60)

    if response.success:
        print(f"✅ 성공!")
        print(f"   - Record ID: {response.record_id}")
        print(f"   - Analysis ID: {response.analysis_id}")
        print(f"   - 모델: gpt-4o-mini")
        print(f"   - Embedding: text-embedding-3-small")
        print(f"   - Graph RAG: ✅ 적용됨")
        print(f"\n{response.analysis_text}")
    else:
        print(f"❌ 실패: {response.error}")

    # 파일로 저장 (성공 시에만 저장)
    if args.output_file and response.success:
        try:
            output_path = Path(args.output_file)
            # 디렉토리가 없으면 생성
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # TXT 파일로 저장 (분석 텍스트만)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write("=" * 80 + "\n")
                f.write("InBody 분석 결과 (Graph RAG 적용)\n")
                f.write("=" * 80 + "\n\n")
                f.write(f"Record ID: {response.record_id}\n")
                f.write(f"Analysis ID: {response.analysis_id}\n")
                f.write(f"모델: gpt-4o-mini\n")
                f.write(f"Embedding: text-embedding-3-small\n")
                f.write(f"Graph RAG: ✅ 적용됨\n\n")
                f.write("-" * 80 + "\n\n")
                f.write(response.analysis_text)

            print(f"\n💾 결과 저장 완료: {output_path.absolute()}")
        except Exception as e:
            print(f"\n⚠️  파일 저장 실패: {e}")
            import traceback

            traceback.print_exc()

    if not response.success:
        sys.exit(1)


if __name__ == "__main__":
    main()
