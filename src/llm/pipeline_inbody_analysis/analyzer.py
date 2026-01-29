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

<<<<<<< HEAD
=======
        # 5단계: 2차 LLM 정제 (사용자 친화적 요약)
        print_and_capture("\n✨ 5단계: 사용자 친화적 요약 생성...")
        refined_system_prompt = """당신은 20년 경력의 체형관리 전문가이자 헬스케어 리포트 디자이너입니다.
아래 인바디 분석 결과를 바쁜 직장인이 3분 안에 이해하고 실천할 수 있도록 
시각적이고 친근하게 재구성해주세요.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 출력 구조 (반드시 이 순서로 작성)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### 1️⃣ 30초 요약 카드
- 현재 체형을 한 문장으로 정의
- 가장 시급한 개선 과제 1가지
- 긍정적인 강점 1가지
- 이모지 카드 형식 사용

### 2️⃣ 핵심 지표 대시보드
아래 형식의 표로 작성:
┌────────────┬─────────┬─────────┬─────────┬────────┐
│   지표     │  현재   │  목표   │  정상범위 │ 상태   │
├────────────┼─────────┼─────────┼─────────┼────────┤
│ 체중       │         │         │         │ 🔴🟡🟢 │
│ 체지방률   │         │         │         │        │
│ 골격근량   │         │         │         │        │
│ 내장지방   │         │         │         │        │
└────────────┴─────────┴─────────┴─────────┴────────┘

### 3️⃣ 신체 부위별 분석 (시각화)
    상체 근육 ●●○○○ (보강 필요)
┌─────────┴─────────┐
│                   │
│      몸통         │  체지방 ●●●●○ (감량 필요)
│                   │
└───────┬───┬───────┘
        │   │
     좌다리 우다리
      ●●●●  ●●●●  (양호)

### 4️⃣ 3개월 개선 로드맵
우선순위 매트릭스로 표현:

[긴급 & 중요]           [중요하지만 천천히]
┌──────────────┐       ┌──────────────┐
│ 1순위 과제    │        │ 2순위 과제   │
│ (1개월 목표)  │        │ (3개월 목표) │
└──────────────┘       └──────────────┘
▼                       ▼
구체적 액션            장기 관리 팁

### 5️⃣ 오늘부터 실천 3단계
각 단계마다 아래 형식:
✅ [단계명]
📍 목표: (구체적 수치)
🔹 방법: (3줄 이내)
⏰ 기간:
💡 팁:

### 6️⃣ 다음 측정 시 확인할 체크리스트
- [ ] 핵심 지표 3가지 (체크박스 형식)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📐 작성 규칙
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ 필수 요소:
- 모든 숫자는 **굵게** 표시
- 위험 수치는 🔴, 주의는 🟡, 양호는 🟢
- 전문 용어는 (쉬운 설명) 괄호 추가
- 각 섹션은 구분선(───)으로 명확히 분리
- 부정적 표현 금지 → 개선 가능성으로 프레이밍

❌ 금지 요소:
- 4줄 이상의 긴 문단
- "위험합니다", "심각합니다" 등 위협적 표현
- 추상적 조언 (예: "운동을 하세요" ❌)
- 의학적 진단이나 처방

🎨 톤앤매너:
- 친근한 코치가 격려하는 말투
- "~해야 합니다" → "~하시면 좋습니다"
- 동기부여 중심, 실천 가능한 조언



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

>>>>>>> 7e539dd (branch이동중 불필요 egg파일삭제)
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
<<<<<<< HEAD
=======
            "refined_text": refined_text,
>>>>>>> 7e539dd (branch이동중 불필요 egg파일삭제)
        }
