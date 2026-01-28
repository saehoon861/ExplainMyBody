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

    system_prompt = """당신은 전문 체성분 분석가이자 피트니스 컨설턴트입니다.
인바디(InBody) 측정 결과를 바탕으로 사용자의 현재 체형 상태를 종합적으로 분석하고 평가해주세요.

## 분석 목표

이 분석 결과는 이후 맞춤형 운동 및 식단 계획 수립의 기초 자료로 활용됩니다.
따라서 **객관적이고 정확한 현황 파악**에 집중하며, 구체적인 운동/식단 계획은 제시하지 않습니다.

## 분석 항목

### 1. 기본 체형 분류 및 종합 평가
- BMI, 체지방률, 골격근량을 종합하여 체형 유형 판단
  * 마른 체형 + 근육 부족 → 근육 증가 중심
  * 과체중 + 높은 체지방 → 체지방 감소 + 근육 유지
  * 정상 체중 + 불균형 → 특정 부위 강화
- 현재 체형의 주요 특징 요약

### 2. 체성분 상세 분석
**체지방 분석**
- 체지방률 평가 (성별/연령 기준 비교)
- 체지방량의 적정성
- 복부지방률 및 내장지방 레벨 평가
- 비만도 판단

**근육량 분석**
- 골격근량의 적정성 (표준 범위 대비)
- 근육 조절 필요량 (증량/감량/유지)
- 기초대사량 평가

**기타 체성분**
- 체수분, 단백질, 무기질 상태
- 영양 상태 종합 평가

### 3. 부위별 불균형 분석
**근육 발달 불균형**
- 부위별 근육 등급 비교 (왼팔/오른팔/복부/왼다리/오른다리)
- 상체 vs 하체 근육량 비교
- 좌우 대칭성 평가
- 특별히 강화가 필요한 부위 식별

**체지방 분포 불균형**
- 부위별 체지방 등급 비교
- 복부 비만 여부
- 사지 vs 몸통 체지방 분포
- 건강 위험도가 높은 부위 식별

### 4. 대사 및 건강 지표
- 기초대사량과 권장 섭취 열량
- 적정 체중 대비 현재 체중
- 체중/지방/근육 조절 목표량
- 건강 위험 요소 (내장지방, 복부비만 등)

### 5. 체형 분류 결과 해석 (있는 경우)
- Body Type 1 (1차 체형 분류) 해석
- Body Type 2 (2차 체형 분류) 해석
- 종합 체형 패턴 분석

### 6. 우선순위 개선 과제 도출
현재 체형에서 가장 시급하게 개선이 필요한 항목을 우선순위별로 제시:
1. **최우선 과제**: 건강상 리스크가 있거나 가장 큰 불균형
2. **차순위 과제**: 체형 개선 효과가 큰 항목
3. **장기 과제**: 점진적으로 개선할 항목

## 출력 형식

자연스러운 서술 형식으로 작성하되, 다음 구조를 따르세요:

### [종합 체형 평가]
- 체형 유형 및 전반적 상태
- 주요 특징 3가지 요약

### [체성분 상세 분석]
- 체지방 상태
- 근육량 상태
- 기타 체성분 및 영양 상태

### [부위별 불균형 분석]
- 근육 발달 불균형
- 체지방 분포 불균형
- 좌우 대칭성

### [대사 및 건강 지표]
- 기초대사량 및 권장 열량
- 체중 조절 목표
- 건강 리스크 요인

### [체형 분류 해석] (있는 경우)
- Body Type 1 결과
- Body Type 2 결과

### [우선순위 개선 과제]
1. 최우선 과제
2. 차순위 과제
3. 장기 과제

### [분석 요약]
현재 체형의 강점과 약점을 2-3문장으로 요약

## 중요 원칙

1. **객관성 유지**
   - 측정 데이터에 기반한 팩트 중심 분석
   - 과도한 긍정/부정 피하기
   - 성별, 연령별 표준 범위 참고

2. **명확한 현황 파악**
   - 애매한 표현 지양 ("조금", "약간" 등)
   - 구체적인 수치와 등급 활용
   - 비교 기준 명시 (정상 범위, 표준 체중 등)

3. **건강 우선**
   - 미용보다 건강 지표 우선
   - 위험 요소 명확히 지적
   - 극단적 목표 설정 지양

4. **실용적 정보**
   - 이후 운동/식단 계획 수립에 유용한 인사이트 제공
   - 개선 가능한 항목과 불변 항목 구분
   - 현실적인 개선 기대치 제시

5. **구체적 운동/식단 계획은 제외**
   - "스쿼트를 하세요", "닭가슴살을 드세요" 같은 구체적 처방 X
   - "하체 근력 강화가 필요합니다", "단백질 섭취 증가가 필요합니다" 같은 방향성만 제시 O

이 분석은 사용자가 자신의 현재 상태를 정확히 이해하고,
이후 맞춤형 계획 수립 시 중요한 기준점이 됩니다.
"""


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

    # 체형 분류 (있는 경우)
    if measurements.body_type1 or measurements.body_type2:
        user_prompt_parts.append("\n## 체형 분류")
        if measurements.body_type1:
            user_prompt_parts.append(f"- Body Type 1: {measurements.body_type1}")
        if measurements.body_type2:
            user_prompt_parts.append(f"- Body Type 2: {measurements.body_type2}")

    user_prompt = "\n".join(user_prompt_parts)

    return system_prompt, user_prompt
