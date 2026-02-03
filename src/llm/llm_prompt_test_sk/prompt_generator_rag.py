"""
Prompt Generator with RAG Support
- backend/services/llm/prompt_generator.py를 기반으로 RAG 컨텍스트만 추가
- 기존 구조 100% 동일하게 유지
"""

from typing import Tuple
from schemas_inbody import InBodyData as InBodyMeasurements
from schemas import GoalPlanInput


def create_inbody_analysis_summary_prompt_with_rag(
    measurements: InBodyMeasurements,
    body_type1: str = "",
    body_type2: str = "",
    rag_context: str = ""
) -> Tuple[str, str]:
    """
    InBody 분석 요약 프롬프트 생성 (Prompt 1)
    5줄 요약: 체형, 근육, 지방, 식단, 운동
    """
    system_prompt = """너는 헬스 유튜브에서 흔히 나오는
유쾌하지만 팩폭 날리는 PT 코치다.

인바디 결과를 보고
유저가 웃으면서도 “아… 해야겠다” 싶게
6줄 요약을 만든다.

조건:
- 딱 5줄 + 마지막 동기부여 1줄 (총 6줄)
- 말투는 현실적 + 살짝 장난 + 팩트는 정확
- “복잡하게 하지 말고 이거만 해라” 느낌
- 운동/식단은 구체적으로 딱 한 가지씩 제시


## 분석 목표
사용자가 한눈에 자신의 체성분 상태를 파악하고 즉시 실천할 수 있는 핵심 정보를 제공합니다.

"""

    # User prompt 생성 (템플릿 기반)
    user_prompt = f"""# InBody 측정 데이터

## 기본 정보
- 성별: {measurements.기본정보.성별}
- 나이: {measurements.기본정보.연령}세
- 신장: {measurements.기본정보.신장} cm

## 핵심 체성분
- 체중: {measurements.체중관리.체중} kg
- BMI: {measurements.비만분석.BMI}
- 체지방률: {measurements.비만분석.체지방률}%
- 골격근량: {measurements.체중관리.골격근량} kg
{"- 내장지방레벨: " + str(measurements.비만분석.내장지방레벨) if measurements.비만분석.내장지방레벨 else ""}

## 조절 목표
{f"- 체중 조절: {measurements.체중관리.체중조절:+.1f} kg" if measurements.체중관리.체중조절 is not None else ""}
{f"- 지방 조절: {measurements.체중관리.지방조절:+.1f} kg" if measurements.체중관리.지방조절 is not None else ""}
{f"- 근육 조절: {measurements.체중관리.근육조절:+.1f} kg" if measurements.체중관리.근육조절 is not None else ""}

## 대사 정보
{f"- 기초대사량: {measurements.연구항목.기초대사량} kcal" if measurements.연구항목.기초대사량 else ""}
{f"- 권장 섭취 열량: {measurements.연구항목.권장섭취열량} kcal" if measurements.연구항목.권장섭취열량 else ""}

## 체형 분류
- Stage 2: {body_type1 or 'N/A'}
- Stage 3: {body_type2 or 'N/A'}

{rag_context}

---

출력 형식:

😮 체형:
💪 근육:
🔥 지방:
🍽 식단:
🏋️ 운동:
📢 한마디:

스타일 가이드:
- 절대 비하/조롱/놀리는 말투 금지
- 사용자를 평가하는 드립 금지 ("불량학생", "게으르네" 등)
- 무례한 농담 금지
- 유머는 "가볍고 긍정적인 동기부여" 수준만 허용

"""
    return system_prompt, user_prompt


def create_inbody_analysis_detail_prompt_with_rag(
    measurements: InBodyMeasurements,
    body_type1: str = "",
    body_type2: str = "",
    prev_inbody: str = "",
    health_notes: str = "",
    rag_context: str = ""
) -> Tuple[str, str]:
    """
    InBody 분석 세부 리포트 프롬프트 생성 (Prompt 2)
    이전 기록 비교, 개선사항, 주의사항
    """
    system_prompt = """
너는 재미있지만 프로다운 PT 코치다.
인바디 결과를 바탕으로 유저가 바로 실행할 수 있게 한다
- 각 섹션은 최소 5줄 이상

출력 규칙 (중요):

- 숫자/목표는 **굵게 강조**
- 딱딱한 보고서 말투 금지 ("필요합니다" X)
- 행동 중심
- 읽기 쉽게 미션/포인트 느낌
- 문장 끝은 가끔 코치 한마디로 마무리


형식:

📈 개선사항 및 권장 행동
1. ...
2. ...
3. ...
4. ...
5. ...
. ...

⚠️ 건강 특이사항 및 주의 포인트 
1. ...
2. ...
3. ...
4. ...
5. ...
. ...

톤:
- PT쌤이 확신 있게 말하는 느낌
- 현실적이지만 부드럽게 상대가 공감할 수 있도록 작성
"""

    # 부위별 데이터 자동 수집
    muscle_analysis = "\n".join([
        f"- {part}: {grade}"
        for part, grade in measurements.부위별근육분석.model_dump().items()
        if grade
    ]) if measurements.부위별근육분석 else ""

    fat_analysis = "\n".join([
        f"- {part}: {grade}"
        for part, grade in measurements.부위별체지방분석.model_dump().items()
        if grade
    ]) if measurements.부위별체지방분석 else ""

    # User prompt 생성 (템플릿 기반)
    user_prompt = f"""# InBody 측정 데이터 (전체)

## 기본 정보
- 성별: {measurements.기본정보.성별}
- 나이: {measurements.기본정보.연령}세
- 신장: {measurements.기본정보.신장} cm

## 체성분 분석
- 체중: {measurements.체중관리.체중} kg
- BMI: {measurements.비만분석.BMI}
- 체지방률: {measurements.비만분석.체지방률}%
- 골격근량: {measurements.체중관리.골격근량} kg
{f"- 체수분: {measurements.체성분.체수분} L" if measurements.체성분.체수분 else ""}
{f"- 단백질: {measurements.체성분.단백질} kg" if measurements.체성분.단백질 else ""}
{f"- 무기질: {measurements.체성분.무기질} kg" if measurements.체성분.무기질 else ""}
{f"- 체지방량: {measurements.체성분.체지방} kg" if measurements.체성분.체지방 else ""}

## 비만 지표
{f"- 복부지방률: {measurements.비만분석.복부지방률}" if measurements.비만분석.복부지방률 else ""}
{f"- 내장지방레벨: {measurements.비만분석.내장지방레벨}" if measurements.비만분석.내장지방레벨 else ""}
{f"- 비만도: {measurements.비만분석.비만도}%" if measurements.비만분석.비만도 else ""}

## 대사 정보
{f"- 기초대사량: {measurements.연구항목.기초대사량} kcal" if measurements.연구항목.기초대사량 else ""}
{f"- 권장 섭취 열량: {measurements.연구항목.권장섭취열량} kcal" if measurements.연구항목.권장섭취열량 else ""}
{f"- 적정 체중: {measurements.체중관리.적정체중} kg" if measurements.체중관리.적정체중 else ""}

## 조절 목표
{f"- 체중 조절: {measurements.체중관리.체중조절:+.1f} kg" if measurements.체중관리.체중조절 is not None else ""}
{f"- 지방 조절: {measurements.체중관리.지방조절:+.1f} kg" if measurements.체중관리.지방조절 is not None else ""}
{f"- 근육 조절: {measurements.체중관리.근육조절:+.1f} kg" if measurements.체중관리.근육조절 is not None else ""}

## 부위별 근육 등급
{muscle_analysis}

## 부위별 체지방 등급
{fat_analysis}

## 규칙 기반 체형 분석
- Stage 2 (근육 보정 체형): {body_type1 or 'N/A'}
- Stage 3 (상하체 밸런스): {body_type2 or 'N/A'}

---

이전 인바디 기록: {prev_inbody if prev_inbody else '없음'}
건강 특이사항: {health_notes if health_notes else '없음'}

{rag_context}

---

아래 섹션별로 작성:

📊 **이전 기록과의 변화**
(이전 기록 있으면 3~5줄 수치 비교 / 없으면 '이전 기록 없음')

📈 **개선사항 및 권장 행동** 

⚠️ **건강 특이사항 및 주의 포인트** 
이 섹션 마지막 줄은 반드시
짧은 동기부여 한방 문장으로 친절하게 끝내라.

"""
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
