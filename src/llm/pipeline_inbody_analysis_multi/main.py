#!/usr/bin/env python3
"""
InBody 분석 파이프라인 실행 파일
Endpoint: /api/inbody/analysis
"""

import sys
import argparse
import json
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.database import Database
from shared.llm_clients import create_llm_client
from shared.models import InBodyMeasurements, InBodyAnalysisRequest, InBodyAnalysisResponse

from pipeline_inbody_analysis_multi.analyzer import InBodyAnalyzer
from pipeline_inbody_analysis_multi.embedder import InBodyEmbedder

load_dotenv()


def run_inbody_analysis(
    user_id: int,
    measurements_dict: dict,
    model: str = "gpt-4o-mini",
    db_url: str = None,
    source: str = "manual",
    enable_embedding: bool = False,
) -> InBodyAnalysisResponse:
    """
    인바디 분석 파이프라인 실행

    Args:
        user_id: 사용자 ID
        measurements_dict: InBody 측정 데이터 (dict)
        model: LLM 모델 이름
        db_url: 데이터베이스 URL
        source: 데이터 소스
        enable_embedding: 임베딩 생성 여부

    Returns:
        InBodyAnalysisResponse
    """
    try:
        # 1. Pydantic 모델 검증
        measurements = InBodyMeasurements(**measurements_dict)

        # 2. Database 및 LLM 클라이언트 초기화
        db = Database(db_url)
        llm_client = create_llm_client(model)

        print(f"✅ 데이터베이스 연결 완료")
        print(f"🤖 LLM 모델: {model}")

        # 3. InBody 분석 수행
        analyzer = InBodyAnalyzer(db, llm_client, model)
        result = analyzer.analyze(user_id, measurements, source)

        # 4. 임베딩 생성 (선택적)
        embedding = None
        if enable_embedding:
            embedder = InBodyEmbedder(db, llm_client)
            embedding = embedder.create_and_save_embedding(
                result["analysis_id"], result["analysis_text"]
            )
            result["embedding"] = embedding

        # 5. 성공 응답
        return InBodyAnalysisResponse(
            success=True,
            record_id=result["record_id"],
            analysis_id=result["analysis_id"],
            analysis_text=result["analysis_text"],
            refined_text=result.get("refined_text"),
        )

    except Exception as e:
        # 에러 응답
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

        return InBodyAnalysisResponse(success=False, error=str(e))


def main():
    parser = argparse.ArgumentParser(description="InBody 분석 파이프라인")

    # 필수 인자
    parser.add_argument("--user-id", type=int, required=True, help="사용자 ID")

    # 측정 데이터 입력 방법
    parser.add_argument(
        "--measurements-json", type=str, help="측정 데이터 JSON 문자열"
    )
    parser.add_argument(
        "--measurements-file", type=str, help="측정 데이터 JSON 파일 경로"
    )
 
    # 선택적 인자
    parser.add_argument(
        "--model",
        default="gpt-4o-mini",
        help="LLM 모델 (gpt-4o-mini, claude-3-5-sonnet-20241022 등)",
    )
    parser.add_argument("--db-url", default=None, help="데이터베이스 URL")
    parser.add_argument(
        "--source", default="manual", help="데이터 소스 (manual, inbody_ocr 등)"
    )
    parser.add_argument(
        "--enable-embedding", action="store_true", help="임베딩 생성 활성화"
    )
    parser.add_argument(
        "--output-file", type=str, help="결과를 저장할 TXT 파일 경로"
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

    # 분석 실행
    response = run_inbody_analysis(
        user_id=args.user_id,
        measurements_dict=measurements_dict,
        model=args.model,
        db_url=args.db_url,
        source=args.source,
        enable_embedding=args.enable_embedding,
    )

    # 결과 출력
    print("\n" + "=" * 60)
    print("📋 분석 결과")
    print("=" * 60)

    if response.success:
        print(f"✅ 성공!")
        print(f"   - Record ID: {response.record_id}")
        print(f"   - Analysis ID: {response.analysis_id}")
        print(f"\n{response.analysis_text}")
    else:
        print(f"❌ 실패: {response.error}")
    
    # 파일로 저장 (성공 시에만 저장)
    if args.output_file and response.success:
        try:
            output_path = Path(args.output_file)
            # 디렉토리가 없으면 생성
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # TXT 파일로 저장 (분석 텍스트 + 정제된 요약)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write("=" * 60 + "\n")
                f.write("InBody 분석 결과\n")
                f.write("=" * 60 + "\n\n")
                f.write(f"Record ID: {response.record_id}\n")
                f.write(f"Analysis ID: {response.analysis_id}\n\n")
                f.write("-" * 60 + "\n\n")
                f.write(response.analysis_text)

                # 정제된 요약 추가
                if response.refined_text:
                    f.write("\n\n" + "=" * 60 + "\n")
                    f.write("📱 사용자 친화적 요약\n")
                    f.write("=" * 60 + "\n\n")
                    f.write(response.refined_text)

            print(f"\n💾 결과 저장 완료: {output_path.absolute()}")
        except Exception as e:
            print(f"\n⚠️  파일 저장 실패: {e}")
            import traceback
            traceback.print_exc()
    
    if not response.success:
        sys.exit(1)


if __name__ == "__main__":
    main()
