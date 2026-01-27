"""
인바디 분석용 프롬프트 생성
"""

from typing import Tuple
from shared.models import InBodyMeasurements


def create_inbody_analysis_prompt(measurements: InBodyMeasurements) -> Tuple[str, str]:
    """
    인바디 분석용 프롬프트 생성

    Args:
        measurements: InBody 측정 데이터

    Returns:
        (system_prompt, user_prompt)
    """

    system_prompt = """당신은 20년 경력의 전문 체형 분석 전문가입니다.

InBody 측정 데이터를 분석하여 사용자의 현재 체형 상태를 **자세하고 정확하게** 설명해주세요.

분석 시 다음 사항을 포함하세요:

1. **전반적인 체형 평가**
   - BMI, 체지방률, 골격근량 기반 종합 평가
   - 비만도 및 건강 위험도 평가

2. **체성분 분석 (상세)**
   - 근육량 (골격근량) 평가: 표준 대비 수준
   - 체지방 평가: 내장지방 포함 위험도
   - 체수분, 단백질, 무기질 균형 상태

3. **Stage 2: 근육 보정 체형 분석**
   - 근육량을 고려한 체형 분류
   - 해당 체형의 특징 및 의미

4. **Stage 3: 상하체 밸런스 분석**
   - 부위별 근육 분포 분석
   - 밸런스 평가 및 불균형 지점

5. **부위별 상세 분석**
   - 각 부위(팔, 몸통, 다리)의 근육/지방 등급 해석
   - 발달 부위 vs 미발달 부위

6. **건강 위험 요인**
   - 내장지방, 복부지방 위험도
   - 대사 건강 평가

7. **개선 방향 제시**
   - 체중 조절, 지방 조절, 근육 조절 목표
   - 우선적으로 개선해야 할 부위

**중요**: 전문적이면서도 이해하기 쉬운 언어로 작성하세요.
수치를 인용하며 구체적으로 설명하되, 사용자가 실제로 행동할 수 있는 인사이트를 제공하세요."""

    # User prompt 생성
    user_prompt_parts = []

    user_prompt_parts.append("# InBody 측정 데이터\n")

    # 기본 정보
    user_prompt_parts.append("## 기본 정보")
    user_prompt_parts.append(f"- 성별: {measurements.성별}")
    user_prompt_parts.append(f"- 나이: {measurements.나이}세")
    user_prompt_parts.append(f"- 신장: {measurements.신장} cm")
    user_prompt_parts.append(f"- 체중: {measurements.체중} kg")

    # 체성분
    user_prompt_parts.append("\n## 체성분 분석")
    user_prompt_parts.append(f"- BMI: {measurements.BMI}")
    user_prompt_parts.append(f"- 체지방률: {measurements.체지방률}%")
    user_prompt_parts.append(f"- 골격근량: {measurements.골격근량} kg")

    if measurements.체수분:
        user_prompt_parts.append(f"- 체수분: {measurements.체수분} L")
    if measurements.단백질:
        user_prompt_parts.append(f"- 단백질: {measurements.단백질} kg")
    if measurements.무기질:
        user_prompt_parts.append(f"- 무기질: {measurements.무기질} kg")
    if measurements.체지방:
        user_prompt_parts.append(f"- 체지방량: {measurements.체지방} kg")

    # 비만 지표
    user_prompt_parts.append("\n## 비만 지표")
    if measurements.복부지방률:
        user_prompt_parts.append(f"- 복부지방률: {measurements.복부지방률}")
    if measurements.내장지방레벨:
        user_prompt_parts.append(f"- 내장지방레벨: {measurements.내장지방레벨}")
    if measurements.비만도:
        user_prompt_parts.append(f"- 비만도: {measurements.비만도}%")

    # 대사
    user_prompt_parts.append("\n## 대사 정보")
    if measurements.기초대사량:
        user_prompt_parts.append(f"- 기초대사량: {measurements.기초대사량} kcal")
    if measurements.권장섭취열량:
        user_prompt_parts.append(f"- 권장 섭취 열량: {measurements.권장섭취열량} kcal")
    if measurements.적정체중:
        user_prompt_parts.append(f"- 적정 체중: {measurements.적정체중} kg")

    # 조절 목표
    user_prompt_parts.append("\n## 조절 목표")
    if measurements.체중조절:
        user_prompt_parts.append(f"- 체중 조절: {measurements.체중조절:+.1f} kg")
    if measurements.지방조절:
        user_prompt_parts.append(f"- 지방 조절: {measurements.지방조절:+.1f} kg")
    if measurements.근육조절:
        user_prompt_parts.append(f"- 근육 조절: {measurements.근육조절:+.1f} kg")

    # 부위별 근육
    user_prompt_parts.append("\n## 부위별 근육 등급")
    for part, grade in measurements.근육_부위별등급.items():
        user_prompt_parts.append(f"- {part}: {grade}")

    # 부위별 체지방
    if measurements.체지방_부위별등급:
        user_prompt_parts.append("\n## 부위별 체지방 등급")
        for part, grade in measurements.체지방_부위별등급.items():
            user_prompt_parts.append(f"- {part}: {grade}")

    # Stage 분석
    user_prompt_parts.append("\n## 규칙 기반 체형 분석")
    user_prompt_parts.append(
        f"- Stage 2 (근육 보정 체형): {measurements.stage2_근육보정체형 or 'N/A'}"
    )
    user_prompt_parts.append(
        f"- Stage 3 (상하체 밸런스): {measurements.stage3_상하체밸런스 or 'N/A'}"
    )

    user_prompt = "\n".join(user_prompt_parts)

    return system_prompt, user_prompt
