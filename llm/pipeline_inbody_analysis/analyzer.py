"""
인바디 분석 로직
"""

import sys
from pathlib import Path
from typing import Dict, Any

# rule_based_bodytype 모듈 임포트
sys.path.append(str(Path(__file__).parent.parent / "rule_based_bodytype"))
from rule_based_bodytype.body_analysis.pipeline import BodyCompositionAnalyzer

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
        self.body_analyzer = BodyCompositionAnalyzer()

    def calculate_stages(self, measurements: InBodyMeasurements) -> Dict[str, str]:
        """
        규칙 기반 Stage 계산

        Args:
            measurements: InBody 측정 데이터

        Returns:
            {"stage2": "근육형", "stage3": "균형형"}
        """
        body_data = {
            "sex": measurements.성별,
            "age": measurements.나이,
            "height_cm": measurements.신장,
            "weight_kg": measurements.체중,
            "bmi": measurements.BMI,
            "fat_rate": measurements.체지방률,
            "smm": measurements.골격근량,
            "muscle_seg": {
                part: self._grade_to_value(grade)
                for part, grade in measurements.근육_부위별등급.items()
            },
            "fat_seg": (
                {
                    part: self._grade_to_value(grade)
                    for part, grade in measurements.체지방_부위별등급.items()
                }
                if measurements.체지방_부위별등급
                else {}
            ),
        }

        stage_results = self.body_analyzer.analyze_full_pipeline(body_data)

        return {
            "stage2": stage_results["stage2"],
            "stage3": stage_results["stage3"],
        }

    def _grade_to_value(self, grade: str) -> float:
        """등급을 숫자 값으로 변환 (임시)"""
        # 실제로는 더 정교한 변환이 필요할 수 있음
        grade_map = {
            "표준미만": 2.0,
            "표준": 3.0,
            "표준이상": 3.5,
            "우수": 4.0,
            "매우우수": 4.5,
        }
        return grade_map.get(grade, 3.0)

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

        # 1단계: Stage 계산 (규칙 기반)
        print_and_capture("\n📊 1단계: 규칙 기반 체형 분석...")
        stage_results = self.calculate_stages(measurements)
        print_and_capture(f"  ✓ Stage 2: {stage_results['stage2']}")
        print_and_capture(f"  ✓ Stage 3: {stage_results['stage3']}")

        # Measurements에 Stage 정보 추가
        measurements.stage2_근육보정체형 = stage_results["stage2"]
        measurements.stage3_상하체밸런스 = stage_results["stage3"]

        # 2단계: health_records에 저장
        print_and_capture("\n💾 2단계: 측정 데이터 저장...")
        record_id = self.db.save_health_record(
            user_id=user_id,
            measurements=measurements.model_dump(),
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
