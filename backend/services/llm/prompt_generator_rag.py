"""
Prompt Generator with RAG Support
- backend/services/llm/prompt_generator.py를 기반으로 RAG 컨텍스트만 추가
- 기존 구조 100% 동일하게 유지
"""

from typing import Tuple
from schemas.inbody import InBodyData as InBodyMeasurements
from schemas.llm import GoalPlanInput


def create_inbody_analysis_prompt_with_rag(
    measurements: InBodyMeasurements,
    body_type1: str = "",
    body_type2: str = "",
    rag_context: str = ""
) -> Tuple[str, str]:
    """
    InBody 분석용 프롬프트 생성 (RAG 컨텍스트 포함)

    기존 prompt_generator.py의 create_inbody_analysis_prompt와 동일 + RAG만 추가
    """
    # 시스템 프롬프트 (기존과 동일)
    system_prompt = """당신은 전문 체성분 분석가이자 피트니스 컨설턴트입니다.
인바디(InBody) 측정 결과를 바탕으로 사용자의 현재 체형 상태를 종합적으로 분석하고 평가해주세요.

## 분석 목표

이 분석 결과는 이후 맞춤형 운동 및 식단 계획 수립의 기초 자료로 활용됩니다.
따라서 **객관적이고 정확한 현황 파악**에 집중하며, 구체적인 운동/식단 계획은 제시하지 않습니다.

## 분석 항목

### 1. 기본 체형 분류 및 종합 평가
- BMI, 체지방률, 골격근량을 종합하여 체형 유형 판단
- 현재 체형의 주요 특징 요약

### 2. 체성분 상세 분석
**체지방 분석**
- 체지방률 평가 (성별/연령 기준 비교)
- 복부지방률 및 내장지방 레벨 평가

**근육량 분석**
- 골격근량의 적정성
- 근육 조절 필요량
- 기초대사량 평가

### 3. 부위별 불균형 분석
- 근육 발달 불균형
- 체지방 분포 불균형

### 4. 우선순위 개선 과제 도출

## 중요 원칙
1. **객관성 유지**: 측정 데이터 기반 팩트 중심
2. **명확한 현황 파악**: 구체적 수치 활용
3. **건강 우선**: 위험 요소 명확히 지적
4. **구체적 운동/식단 계획은 제외**: 방향성만 제시

### 과학적 근거 활용
- 제공된 과학 논문 정보가 있다면, 이를 자연스럽게 분석에 통합하세요
- 논문을 직접 인용하지 말고, 근거로 활용하여 신뢰도를 높이세요
"""

    # User prompt 생성 (기존과 동일)
    user_prompt_parts = []
    user_prompt_parts.append("# InBody 측정 데이터\n")

    # 기본 정보
    user_prompt_parts.append("## 기본 정보")
    user_prompt_parts.append(f"- 성별: {measurements.기본정보.성별}")
    user_prompt_parts.append(f"- 나이: {measurements.기본정보.연령}세")
    user_prompt_parts.append(f"- 신장: {measurements.기본정보.신장} cm")
    user_prompt_parts.append(f"- 체중: {measurements.체중관리.체중} kg")

    # 체성분
    user_prompt_parts.append("\n## 체성분 분석")
    user_prompt_parts.append(f"- BMI: {measurements.비만분석.BMI}")
    user_prompt_parts.append(f"- 체지방률: {measurements.비만분석.체지방률}%")
    user_prompt_parts.append(f"- 골격근량: {measurements.체중관리.골격근량} kg")

    if measurements.체성분.체수분:
        user_prompt_parts.append(f"- 체수분: {measurements.체성분.체수분} L")
    if measurements.체성분.단백질:
        user_prompt_parts.append(f"- 단백질: {measurements.체성분.단백질} kg")
    if measurements.체성분.무기질:
        user_prompt_parts.append(f"- 무기질: {measurements.체성분.무기질} kg")
    if measurements.체성분.체지방:
        user_prompt_parts.append(f"- 체지방량: {measurements.체성분.체지방} kg")

    # 비만 지표
    user_prompt_parts.append("\n## 비만 지표")
    if measurements.비만분석.복부지방률:
        user_prompt_parts.append(f"- 복부지방률: {measurements.비만분석.복부지방률}")
    if measurements.비만분석.내장지방레벨:
        user_prompt_parts.append(f"- 내장지방레벨: {measurements.비만분석.내장지방레벨}")
    if measurements.비만분석.비만도:
        user_prompt_parts.append(f"- 비만도: {measurements.비만분석.비만도}%")

    # 대사
    user_prompt_parts.append("\n## 대사 정보")
    if measurements.연구항목.기초대사량:
        user_prompt_parts.append(f"- 기초대사량: {measurements.연구항목.기초대사량} kcal")
    if measurements.연구항목.권장섭취열량:
        user_prompt_parts.append(f"- 권장 섭취 열량: {measurements.연구항목.권장섭취열량} kcal")
    if measurements.체중관리.적정체중:
        user_prompt_parts.append(f"- 적정 체중: {measurements.체중관리.적정체중} kg")

    # 조절 목표
    user_prompt_parts.append("\n## 조절 목표")
    if measurements.체중관리.체중조절 is not None:
        user_prompt_parts.append(f"- 체중 조절: {measurements.체중관리.체중조절:+.1f} kg")
    if measurements.체중관리.지방조절 is not None:
        user_prompt_parts.append(f"- 지방 조절: {measurements.체중관리.지방조절:+.1f} kg")
    if measurements.체중관리.근육조절 is not None:
        user_prompt_parts.append(f"- 근육 조절: {measurements.체중관리.근육조절:+.1f} kg")

    # 부위별 근육
    user_prompt_parts.append("\n## 부위별 근육 등급")
    if measurements.부위별근육분석:
        for part, grade in measurements.부위별근육분석.model_dump().items():
            if grade:
                user_prompt_parts.append(f"- {part}: {grade}")

    # 부위별 체지방
    if measurements.부위별체지방분석:
        user_prompt_parts.append("\n## 부위별 체지방 등급")
        for part, grade in measurements.부위별체지방분석.model_dump().items():
            if grade:
                user_prompt_parts.append(f"- {part}: {grade}")

    # Stage 분석
    user_prompt_parts.append("\n## 규칙 기반 체형 분석")
    user_prompt_parts.append(f"- Stage 2 (근육 보정 체형): {body_type1 or 'N/A'}")
    user_prompt_parts.append(f"- Stage 3 (상하체 밸런스): {body_type2 or 'N/A'}")

    # RAG 컨텍스트 추가 (유일한 차이점)
    if rag_context:
        user_prompt_parts.append(rag_context)

    user_prompt = "\n".join(user_prompt_parts)

    return system_prompt, user_prompt


def create_weekly_plan_prompt_with_rag(
    goal_input: GoalPlanInput,
    measurements: InBodyMeasurements,
    rag_context: str = ""
) -> Tuple[str, str]:
    """
    주간 계획 생성용 프롬프트 (RAG 컨텍스트 포함)

    기존 prompt_generator.py의 create_weekly_plan_prompt와 동일 + RAG만 추가
    """
    system_prompt = """당신은 사용자의 건강 데이터와 목표를 분석하여 맞춤형 주간 운동 및 식단 계획을 수립하는 전문 퍼스널 트레이너입니다.
사용자의 신체 상태(인바디), 목표, 그리고 이전 건강 분석 결과를 종합적으로 고려하여 실천 가능하고 효과적인 1주차 계획을 작성해주세요.

## 작성 지침
1. **개인화**: 사용자의 체중, 근육량, 체지방률과 구체적인 목표를 반영하세요.
2. **구체성**: 운동 종목, 세트 수, 식단 메뉴 등을 구체적으로 제시하세요.
3. **안전성**: 사용자의 신체 상태에 무리가 가지 않는 수준으로 설정하세요.
4. **과학적 근거**: 제공된 논문 정보가 있다면 자연스럽게 활용하세요.

## 출력 형식
- **주간 목표 요약**: 이번 주 집중할 포인트
- **운동 계획**: 요일별 운동 루틴
- **식단 가이드**: 영양 섭취 포인트
- **생활 습관 팁**: 수면, 수분 섭취 등
"""

    user_prompt_parts = []
    user_prompt_parts.append(f"# 사용자 목표")
    user_prompt_parts.append(f"- 목표 유형: {goal_input.user_goal_type}")
    user_prompt_parts.append(f"- 상세 내용: {goal_input.user_goal_description}")

    user_prompt_parts.append(f"\n# 신체 정보")
    user_prompt_parts.append(f"- 성별: {measurements.기본정보.성별}")
    user_prompt_parts.append(f"- 체중: {measurements.체중관리.체중}kg")
    user_prompt_parts.append(f"- 골격근량: {measurements.체중관리.골격근량}kg")
    user_prompt_parts.append(f"- 체지방률: {measurements.비만분석.체지방률}%")

    if goal_input.status_analysis_result:
        user_prompt_parts.append(f"\n# 건강 상태 분석 결과 (참고)")
        user_prompt_parts.append(goal_input.status_analysis_result)

    # RAG 컨텍스트 추가 (유일한 차이점)
    if rag_context:
        user_prompt_parts.append(rag_context)

    user_prompt = "\n".join(user_prompt_parts)

    return system_prompt, user_prompt
