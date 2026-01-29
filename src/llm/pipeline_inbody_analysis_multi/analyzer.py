"""
인바디 분석 로직
"""

from typing import Dict, Any

from shared.models import InBodyMeasurements
from shared.llm_clients import BaseLLMClient
from shared.database import Database
from pipeline_inbody_analysis_multi.prompt_generator import create_multi_part_prompts


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

        # 3단계: LLM 분석 (3회 호출)
        print_and_capture("\n🤖 3단계: LLM 분석 생성 (3-part 분할)...")
        prompts = create_multi_part_prompts(measurements)

        analysis_parts = []
        part_names = ["기본 체성분 분석", "부위별 불균형 분석", "개선 과제 및 종합 평가"]

        for i, (system_prompt, user_prompt) in enumerate(prompts, 1):
            print_and_capture(f"  - Part {i}/3: {part_names[i-1]} LLM 호출 중...")
            part_text = self.llm_client.generate_chat(system_prompt, user_prompt)
            analysis_parts.append(part_text)
            print_and_capture(f"  ✓ Part {i} 완료 ({len(part_text)} 글자)")

        # 3개 파트를 하나로 결합
        print_and_capture("\n  - 3개 파트 결합 중...")
        analysis_text = "\n\n" + ("=" * 80 + "\n\n").join(analysis_parts)
        print_and_capture(f"  ✓ 전체 분석 완료 ({len(analysis_text)} 글자)")

        # 4단계: 분석 결과 저장
        print_and_capture("\n💾 4단계: 분석 결과 저장...")
        analysis_id = self.db.save_analysis_report(
            user_id=user_id,
            record_id=record_id,
            llm_output=analysis_text,
            model_version=self.model_version,
        )
        print_and_capture(f"  ✓ Analysis ID: {analysis_id}")

        # 5단계: 2차 LLM 정제 (사용자 친화적 요약)
        print_and_capture("\n✨ 5단계: 사용자 친화적 요약 생성...")
        refined_system_prompt = """당신은 의료 리포트 편집자입니다.
주어진 인바디 분석 리포트를 일반 사용자가 이해하기 쉽게 요약하고 정제해주세요.

## 목표
- 전문 용어를 쉬운 말로 풀어쓰기
- 핵심 내용만 간결하게 요약
- 실천 가능한 조언 중심으로 재구성
- 긍정적이고 동기부여가 되는 톤

## 출력 형식
### 📊 현재 상태 한눈에 보기
(체형, 체지방, 근육량 핵심 3줄 요약)

### 💪 개선이 필요한 부분
(우선순위 1-3가지, 각 1-2문장)

### 🎯 실천 가이드
(구체적이고 실천 가능한 방향 3-5가지)

### ✅ 현재 잘하고 있는 부분
(긍정적 피드백 2-3가지)

전문적이지만 친근하게 작성해주세요."""

        refined_user_prompt = f"""다음 인바디 분석 리포트를 사용자 친화적으로 요약해주세요:

{analysis_text}"""

        print_and_capture("  - 2차 LLM 호출 중...")
        refined_text = self.llm_client.generate_chat(
            refined_system_prompt, refined_user_prompt
        )
        print_and_capture(f"  ✓ 요약 완료 ({len(refined_text)} 글자)")

        # 6단계: 정제된 결과 DB 업데이트
        print_and_capture("\n💾 6단계: 정제된 요약 저장...")
        self.db.update_analysis_refined_output(analysis_id, refined_text)
        print_and_capture(f"  ✓ Refined output 업데이트 완료")

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
            "refined_text": refined_text,
        }
