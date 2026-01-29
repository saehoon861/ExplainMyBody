"""
인바디 분석 로직
"""

from typing import Dict, Any

from shared.models import InBodyMeasurements
from shared.llm_clients import BaseLLMClient
from shared.database import Database
from pipeline_inbody_analysis.prompt_generator import create_inbody_analysis_prompt


class InBodyAnalyzer:
    """인바디 분석기"""

    def __init__(self, db: Database, llm_client: BaseLLMClient, model_version: str):
        """
        Args:
            db: Database 인스턴스
            llm_client: LLM 클라이언트
            model_version: 모델 버전
        """
        self.db = db
        self.llm_client = llm_client
        self.model_version = model_version

    def analyze(
        self,
        user_id: int,
        measurements: InBodyMeasurements,
        source: str = "manual",
    ) -> Dict[str, Any]:
        """
        전체 인바디 분석 수행

        Args:
            user_id: 사용자 ID
            measurements: InBody 측정 데이터
            source: 데이터 소스

        Returns:
            {
                "record_id": int,
                "analysis_id": int,
                "analysis_text": str,
                "embedding": List[float] (optional)
            }
        """
        # 출력 메시지를 수집하기 위한 리스트
        output_lines = []
        
        def print_and_capture(*args, **kwargs):
            """print 출력을 캡처하면서 동시에 콘솔에도 출력"""
            message = ' '.join(str(arg) for arg in args)
            output_lines.append(message)
            print(*args, **kwargs)
        
        print_and_capture("=" * 60)
        print_and_capture(f"InBody 분석 시작 (User ID: {user_id})")
        print_and_capture("=" * 60)

        # 1단계: 체형 정보 확인
        print_and_capture("\n📊 1단계: 체형 정보 확인...")
        if measurements.body_type1:
            print_and_capture(f"  ✓ Body Type 1: {measurements.body_type1}")
        if measurements.body_type2:
            print_and_capture(f"  ✓ Body Type 2: {measurements.body_type2}")
        if not measurements.body_type1 and not measurements.body_type2:
            print_and_capture("  ⚠️  체형 정보 없음 (body_type1, body_type2 미입력)")

        # 2단계: health_records에 저장
        print_and_capture("\n💾 2단계: 측정 데이터 저장...")
        m = measurements.model_dump()
        record_id = self.db.save_health_record(
            user_id=user_id,
            measurements=m,
            source=source,
        )
        print_and_capture(f"  ✓ Record ID: {record_id}")

        # 3단계: LLM 분석
        print_and_capture("\n🤖 3단계: LLM 분석 생성...")
        system_prompt, user_prompt = create_inbody_analysis_prompt(measurements)

        print_and_capture("  - LLM 호출 중...")
        analysis_text = self.llm_client.generate_chat(system_prompt, user_prompt)
        print_and_capture(f"  ✓ 분석 완료 ({len(analysis_text)} 글자)")

        # 4단계: 분석 결과 저장
        print_and_capture("\n💾 4단계: 분석 결과 저장...")
        analysis_id = self.db.save_analysis_report(
            user_id=user_id,
            record_id=record_id,
            llm_output=analysis_text,
            model_version=self.model_version,
        )
        print_and_capture(f"  ✓ Analysis ID: {analysis_id}")

        print_and_capture("\n" + "=" * 60)
        print_and_capture("✨ InBody 분석 완료!")
        print_and_capture("=" * 60)

        # 전체 출력 메시지와 LLM 분석 결과를 결합
        full_output = '\n'.join(output_lines) + '\n\n' + '=' * 60 + '\n'
        full_output += '📋 LLM 분석 리포트\n'
        full_output += '=' * 60 + '\n\n'
        full_output += analysis_text

        return {
            "record_id": record_id,
            "analysis_id": analysis_id,
            "analysis_text": full_output,
        }
