"""
Prompt Generator with RAG Support
- backend/services/llm/prompt_generator.py를 기반으로 RAG 컨텍스트만 추가
- 기존 구조 100% 동일하게 유지
- 사용자 프로필 (workout_place, preferred_sport) 분기 처리 지원
"""

from typing import Tuple, Dict, Any, Optional
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



def create_weekly_plan_summary_prompt_with_rag(
    goal_input: GoalPlanInput,
    measurements: InBodyMeasurements,
    rag_context: str = "",
    user_profile: Optional[Dict[str, Any]] = None
) -> Tuple[str, str]:
    """
    주간 계획 요약 프롬프트 생성 (Prompt 1)
    이번 주 핵심 목표와 전략 요약

    Args:
        goal_input: 사용자 목표 정보
        measurements: 인바디 측정 데이터
        rag_context: RAG 검색 결과
        user_profile: 사용자 프로필 (workout_place, preferred_sport 등)
                     예: {"body_type1": "마른비만형", "body_type2": "상체비만형",
                          "workout_place": "홈트", "preferred_sport": None}
    """
    # 사용자 프로필 기반 전략 텍스트 생성
    strategy_text = ""
    if user_profile:
        try:
            from user_profile_strategy import build_strategy_text_from_dict
            strategy_text = build_strategy_text_from_dict(user_profile)
        except ImportError:
            # 모듈 없으면 스킵
            pass

    system_prompt = """너는 빡센 헬스 PT다.

사용자의 체성분과 목표를 보고, 이번 주에 집중할 핵심 전략을 딱 3가지로 정리해라.
존댓말로 작성해라.

## 사용자 맞춤 전략 활용
- 제공된 체형별/장소별 전략을 반드시 반영하세요
- 전략에 명시된 주의사항과 코치 조언을 존중하세요
"""

    user_prompt = f"""# 사용자 목표
- 목표 유형: {goal_input.user_goal_type}
- 상세 내용: {goal_input.user_goal_description}

# 신체 정보
- 성별: {measurements.기본정보.성별}
- 나이: {measurements.기본정보.연령}세
- 신장: {measurements.기본정보.신장}cm
- 체중: {measurements.체중관리.체중}kg
- BMI: {measurements.비만분석.BMI}
- 골격근량: {measurements.체중관리.골격근량}kg
- 체지방률: {measurements.비만분석.체지방률}%
{f"- 기초대사량: {measurements.연구항목.기초대사량}kcal" if measurements.연구항목.기초대사량 else ""}

# 조절 목표
{f"- 체중 조절: {measurements.체중관리.체중조절:+.1f}kg" if measurements.체중관리.체중조절 is not None else ""}
{f"- 지방 조절: {measurements.체중관리.지방조절:+.1f}kg" if measurements.체중관리.지방조절 is not None else ""}
{f"- 근육 조절: {measurements.체중관리.근육조절:+.1f}kg" if measurements.체중관리.근육조절 is not None else ""}

{strategy_text if strategy_text else ""}

{rag_context}

---

출력 형식:

🎯 주간 목표 (한 줄 요약)

💪 핵심 전략 1:
🔥 핵심 전략 2:
🍽 핵심 전략 3:
"""
    return system_prompt, user_prompt



def create_workout_plan_prompt_with_rag(
    goal_input: GoalPlanInput,
    measurements: InBodyMeasurements,
    rag_context: str = "",
    user_profile: Optional[Dict[str, Any]] = None
) -> Tuple[str, str]:
    """
    요일별 운동 계획 프롬프트 (Prompt 2)
    """
    # 사용자 프로필 기반 전략 텍스트 생성
    strategy_text = ""
    if user_profile:
        try:
            from user_profile_strategy import build_strategy_text_from_dict
            strategy_text = build_strategy_text_from_dict(user_profile)
        except ImportError:
            pass

    system_prompt = """당신은 사용자의 체형과 목표에 맞는 요일별 운동 계획을 작성하는 전문 퍼스널 트레이너입니다.

## 작성 지침
1. 사용자의 운동 장소와 가능 일수를 반영하세요
2. 각 운동마다 세트×횟수, 중량/시간을 구체적으로 제시하세요
3. 제공된 체형별 전략을 반드시 반영하세요
4. 휴식일도 명시하세요
"""

    user_prompt = f"""# 사용자 정보
- 체중: {measurements.체중관리.체중}kg
- 골격근량: {measurements.체중관리.골격근량}kg
- 체지방률: {measurements.비만분석.체지방률}%
- 주당 운동 가능: {goal_input.available_days_per_week if goal_input.available_days_per_week else 5}일
- 회당 시간: {goal_input.available_time_per_session if goal_input.available_time_per_session else 60}분

{strategy_text if strategy_text else ""}

{rag_context}

---

출력 형식:

🏋️ **요일별 운동 계획**

**월요일:**
- 메인: [운동명] [세트×횟수] [중량/시간]
- 보조: [운동명] [세트×횟수]
- 마무리: [스트레칭/유산소]

**화요일:**
...

(주당 {goal_input.available_days_per_week if goal_input.available_days_per_week else 5}일 기준, 휴식일 포함)
"""
    return system_prompt, user_prompt


def create_diet_plan_prompt_with_rag(
    goal_input: GoalPlanInput,
    measurements: InBodyMeasurements,
    rag_context: str = "",
    user_profile: Optional[Dict[str, Any]] = None
) -> Tuple[str, str]:
    """
    식단 계획 프롬프트 (Prompt 3)
    """
    # 사용자 프로필 기반 전략 텍스트 생성
    strategy_text = ""
    if user_profile:
        try:
            from user_profile_strategy import build_strategy_text_from_dict
            strategy_text = build_strategy_text_from_dict(user_profile)
        except ImportError:
            pass

    system_prompt = """당신은 사용자의 목표에 맞는 식단 계획을 작성하는 영양 전문가입니다.

## 작성 지침
1. 기초대사량과 목표를 고려한 칼로리 설정
2. 단백질/탄수화물/지방 비율 제시
3. 구체적인 식단 예시 제공
4. 제공된 체형별 식단 전략을 반영하세요
"""

    user_prompt = f"""# 사용자 정보
- 체중: {measurements.체중관리.체중}kg
- 골격근량: {measurements.체중관리.골격근량}kg
- 체지방률: {measurements.비만분석.체지방률}%
{f"- 기초대사량: {measurements.연구항목.기초대사량}kcal" if measurements.연구항목.기초대사량 else ""}
{f"- 권장 섭취 열량: {measurements.연구항목.권장섭취열량}kcal" if measurements.연구항목.권장섭취열량 else ""}
- 목표: {goal_input.user_goal_type}

{strategy_text if strategy_text else ""}

{rag_context}

---

출력 형식:

🍽 **식단 계획**

**일일 목표 칼로리:** XXX kcal
**영양소 비율:** 단백질 XX% / 탄수화물 XX% / 지방 XX%
**일일 단백질 목표:** XX g

**추천 식단 예시:**

**아침 (XXX kcal):**
- 메뉴 1
- 메뉴 2

**점심 (XXX kcal):**
- 메뉴 1
- 메뉴 2

**저녁 (XXX kcal):**
- 메뉴 1
- 메뉴 2

**간식:**
- 추천 간식
"""
    return system_prompt, user_prompt


def create_lifestyle_motivation_prompt_with_rag(
    goal_input: GoalPlanInput,
    measurements: InBodyMeasurements,
    rag_context: str = "",
    user_profile: Optional[Dict[str, Any]] = None
) -> Tuple[str, str]:
    """
    생활 습관 팁 및 동기부여 프롬프트 (Prompt 4)
    """
    system_prompt = """당신은 사용자의 건강한 생활 습관을 돕는 라이프 코치입니다.

## 작성 지침
1. 실천 가능한 생활 습관 팁 제공 (3-5가지)
2. 수면, 수분, 스트레스 관리 포함
3. 마지막에 강력한 동기부여 문장으로 마무리
"""

    user_prompt = f"""# 사용자 정보
- 목표: {goal_input.user_goal_type}
- 현재 체지방률: {measurements.비만분석.체지방률}%
- 근육량: {measurements.체중관리.골격근량}kg

{rag_context}

---

출력 형식:

💡 **생활 습관 팁**

1. **수면:** ...
2. **수분 섭취:** ...
3. **스트레스 관리:** ...
4. **회복:** ...
5. **기타:** ...

🔥 **동기부여 한방 문장**
[강력하고 긍정적인 동기부여 문장 2-3줄]
"""
    return system_prompt, user_prompt
