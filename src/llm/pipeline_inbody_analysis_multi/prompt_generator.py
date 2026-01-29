"""
인바디 분석용 프롬프트 생성 (3-part 분할)
"""

from typing import Tuple, List
from shared.models import InBodyMeasurements


def create_multi_part_prompts(measurements: InBodyMeasurements) -> List[Tuple[str, str]]:
    """
    인바디 분석을 3개 파트로 분할하여 프롬프트 생성

    Args:
        measurements: InBody 측정 데이터

    Returns:
        List of (system_prompt, user_prompt) tuples (3개)
    """

    # 공통 데이터 문자열 생성
    common_data = _generate_common_data(measurements)

    prompts = []

    # ========== Part 1: 기본 체성분 분석 ==========
    system_prompt_1 = """당신은 전문 체성분 분석가입니다.
InBody 측정 결과를 바탕으로 **기본 체성분 상태**를 분석해주세요.

## 분석 범위 (Part 1/3)

이 분석은 3부작 중 첫 번째 파트로, 기본적인 체성분 지표에 집중합니다.

### 1. 종합 체형 평가
- BMI, 체지방률, 골격근량을 종합한 체형 분류
- 현재 체형의 주요 특징 3가지
- 체형 유형 판단 (마른형/표준형/과체중형 등)

### 2. 체지방 분석
- 체지방률 평가 (성별/연령 기준)
- 체지방량의 적정성
- 복부지방률 및 내장지방 레벨
- 비만도 판단
- 건강 위험도 평가

### 3. 근육량 분석
- 골격근량의 적정성
- 근육 조절 필요량 (증량/감량/유지)
- 기초대사량 평가
- 체력 수준 추정

### 4. 기타 체성분
- 체수분, 단백질, 무기질 상태
- 영양 상태 종합
- 체성분 균형 평가

## 출력 형식

### [Part 1: 기본 체성분 분석]

#### 1. 종합 체형 평가
(체형 유형 및 주요 특징 3가지)

#### 2. 체지방 상세 분석
(체지방률, 복부지방, 내장지방, 건강 위험도)

#### 3. 근육량 상세 분석
(골격근량, 기초대사량, 체력 수준)

#### 4. 기타 체성분 평가
(체수분, 단백질, 무기질, 영양 상태)

## 중요 원칙
- 객관적이고 정확한 수치 기반 분석
- 성별/연령별 표준 범위 참고
- 건강 위험 요소 명확히 지적
- 구체적 운동/식단 계획은 제외 (방향성만 제시)
"""

    user_prompt_1 = f"{common_data}\n\n## 요청사항\n위 측정 데이터를 바탕으로 Part 1 (기본 체성분 분석)을 작성해주세요."
    prompts.append((system_prompt_1, user_prompt_1))

    # ========== Part 2: 부위별 불균형 분석 ==========
    system_prompt_2 = """당신은 전문 체성분 분석가입니다.
InBody 측정 결과를 바탕으로 **부위별 불균형**을 분석해주세요.

## 분석 범위 (Part 2/3)

이 분석은 3부작 중 두 번째 파트로, 신체 부위별 불균형에 집중합니다.

### 1. 근육 발달 불균형
- 부위별 근육 등급 비교 (왼팔/오른팔/몸통/왼다리/오른다리)
- 상체 vs 하체 근육량 비교
- 좌우 대칭성 평가
- 특별히 강화가 필요한 부위 식별
- 불균형으로 인한 잠재적 문제점

### 2. 체지방 분포 불균형
- 부위별 체지방 등급 비교
- 복부 비만 여부 및 위험도
- 사지 vs 몸통 체지방 분포
- 내장지방 vs 피하지방 비율
- 건강 위험도가 높은 부위

### 3. 체형 분류 해석 (있는 경우)
- Body Type 1 결과 해석
- Body Type 2 결과 해석
- 체형 패턴이 건강에 미치는 영향

### 4. 대사 및 체중 조절 목표
- 기초대사량과 권장 열량
- 적정 체중 대비 현재 체중
- 체중/지방/근육 조절 목표량
- 조절 우선순위 제시

## 출력 형식

### [Part 2: 부위별 불균형 분석]

#### 1. 근육 발달 불균형
(상하체 비교, 좌우 대칭, 취약 부위)

#### 2. 체지방 분포 불균형
(복부비만, 부위별 분포, 건강 위험 부위)

#### 3. 체형 분류 해석
(Body Type 1/2 결과 해석 - 있는 경우)

#### 4. 대사 및 조절 목표
(기초대사량, 체중 조절 목표, 우선순위)

## 중요 원칙
- 불균형이 건강에 미치는 영향 명시
- 좌우 대칭 문제는 부상 위험과 연결
- 복부비만은 건강 최우선 과제로 강조
- 수치와 등급을 활용한 객관적 평가
"""

    user_prompt_2 = f"{common_data}\n\n## 요청사항\n위 측정 데이터를 바탕으로 Part 2 (부위별 불균형 분석)을 작성해주세요."
    prompts.append((system_prompt_2, user_prompt_2))

    # ========== Part 3: 개선 과제 및 종합 평가 ==========
    system_prompt_3 = """당신은 전문 체성분 분석가입니다.
InBody 측정 결과를 바탕으로 **우선순위 개선 과제 및 종합 평가**를 작성해주세요.

## 분석 범위 (Part 3/3)

이 분석은 3부작 중 마지막 파트로, 실행 가능한 개선 방향을 제시합니다.

### 1. 우선순위 개선 과제
현재 체형에서 가장 시급하게 개선이 필요한 항목을 우선순위별로 제시:

**최우선 과제 (건강 리스크 관련)**
- 건강상 위험이 있는 항목 (내장지방, 복부비만 등)
- 즉시 개선이 필요한 불균형
- 부상 위험이 있는 좌우 비대칭

**차순위 과제 (체형 개선 효과)**
- 체형 개선 효과가 큰 항목
- 기초대사량 증가에 도움이 되는 과제
- 전반적인 건강 증진 항목

**장기 과제 (점진적 개선)**
- 시간이 걸리지만 중요한 항목
- 유지 및 관리가 필요한 부분
- 생활 습관 개선 관련

### 2. 개선 방향성 제시
- 체중 조절 방향 (증량/감량/유지)
- 근육 발달 전략 (전신/특정부위)
- 체지방 관리 전략
- 식습관 개선 방향

### 3. 기대 효과 및 현실적 목표
- 3개월 목표
- 6개월 목표
- 1년 목표
- 각 목표 달성 시 예상 변화

### 4. 종합 요약
- 현재 체형의 강점 (유지할 것)
- 현재 체형의 약점 (개선할 것)
- 핵심 메시지 (2-3문장)

## 출력 형식

### [Part 3: 개선 과제 및 종합 평가]

#### 1. 우선순위 개선 과제

**최우선 과제 (즉시 개선 필요)**
- ...

**차순위 과제 (체형 개선 효과)**
- ...

**장기 과제 (점진적 개선)**
- ...

#### 2. 개선 방향성
(체중 조절, 근육 발달, 체지방 관리, 식습관)

#### 3. 기대 효과 및 목표
(3개월/6개월/1년 목표 및 예상 변화)

#### 4. 종합 요약
(강점, 약점, 핵심 메시지)

## 중요 원칙
- 건강 최우선 (미용은 부차적)
- 현실적이고 달성 가능한 목표
- 단계적 접근 강조
- 긍정적이면서도 객관적인 톤
- 구체적 운동/식단 처방은 제외 (방향성만)
"""

    user_prompt_3 = f"{common_data}\n\n## 요청사항\n위 측정 데이터를 바탕으로 Part 3 (개선 과제 및 종합 평가)을 작성해주세요."
    prompts.append((system_prompt_3, user_prompt_3))

    return prompts


def _generate_common_data(measurements: InBodyMeasurements) -> str:
    """공통 측정 데이터 문자열 생성"""
    parts = []

    parts.append("# InBody 측정 데이터\n")

    # 기본 정보
    parts.append("## 기본 정보")
    parts.append(f"- 성별: {measurements.성별}")
    parts.append(f"- 나이: {measurements.나이}세")
    parts.append(f"- 신장: {measurements.신장} cm")
    parts.append(f"- 체중: {measurements.체중} kg")

    # 체성분
    parts.append("\n## 체성분 분석")
    parts.append(f"- BMI: {measurements.BMI}")
    parts.append(f"- 체지방률: {measurements.체지방률}%")
    parts.append(f"- 골격근량: {measurements.골격근량} kg")

    if measurements.체수분:
        parts.append(f"- 체수분: {measurements.체수분} L")
    if measurements.단백질:
        parts.append(f"- 단백질: {measurements.단백질} kg")
    if measurements.무기질:
        parts.append(f"- 무기질: {measurements.무기질} kg")
    if measurements.체지방:
        parts.append(f"- 체지방량: {measurements.체지방} kg")

    # 비만 지표
    parts.append("\n## 비만 지표")
    if measurements.복부지방률:
        parts.append(f"- 복부지방률: {measurements.복부지방률}")
    if measurements.내장지방레벨:
        parts.append(f"- 내장지방레벨: {measurements.내장지방레벨}")
    if measurements.비만도:
        parts.append(f"- 비만도: {measurements.비만도}%")

    # 대사
    parts.append("\n## 대사 정보")
    if measurements.기초대사량:
        parts.append(f"- 기초대사량: {measurements.기초대사량} kcal")
    if measurements.권장섭취열량:
        parts.append(f"- 권장 섭취 열량: {measurements.권장섭취열량} kcal")
    if measurements.적정체중:
        parts.append(f"- 적정 체중: {measurements.적정체중} kg")

    # 조절 목표
    parts.append("\n## 조절 목표")
    if measurements.체중조절:
        parts.append(f"- 체중 조절: {measurements.체중조절:+.1f} kg")
    if measurements.지방조절:
        parts.append(f"- 지방 조절: {measurements.지방조절:+.1f} kg")
    if measurements.근육조절:
        parts.append(f"- 근육 조절: {measurements.근육조절:+.1f} kg")

    # 부위별 근육
    parts.append("\n## 부위별 근육 등급")
    for part, grade in measurements.근육_부위별등급.items():
        parts.append(f"- {part}: {grade}")

    # 부위별 체지방
    if measurements.체지방_부위별등급:
        parts.append("\n## 부위별 체지방 등급")
        for part, grade in measurements.체지방_부위별등급.items():
            parts.append(f"- {part}: {grade}")

    # 체형 분류 (있는 경우)
    if measurements.body_type1 or measurements.body_type2:
        parts.append("\n## 체형 분류")
        if measurements.body_type1:
            parts.append(f"- Body Type 1: {measurements.body_type1}")
        if measurements.body_type2:
            parts.append(f"- Body Type 2: {measurements.body_type2}")

    return "\n".join(parts)
