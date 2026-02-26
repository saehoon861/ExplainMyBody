"""
인바디 분석용 프롬프트 생성
"""

from typing import Tuple, Optional
from schemas.inbody import InBodyData as InBodyMeasurements
from schemas.llm import GoalPlanInput


def create_inbody_analysis_prompt(
    measurements: InBodyMeasurements,
    body_type1: Optional[str] = None,
    body_type2: Optional[str] = None,
    prev_inbody_data: Optional[InBodyMeasurements] = None,
    interval_days: Optional[str] = None
) -> Tuple[str, str]:
    """
    인바디 분석용 프롬프트 생성

    Args:
        measurements: InBody 측정 데이터
        body_type1: 1차 체형 (예: 비만형)
        body_type2: 2차 체형 (예: 상체발달형)
        prev_inbody_data: 이전 InBody 측정 데이터 (선택)
        interval_days: 이전 InBody 측정 일시 (선택)

    Returns:
        (system_prompt, user_prompt)
    """
    
    print(f"\n[DEBUG][PromptGenerator] create_inbody_analysis_prompt 호출")
    print(f"[DEBUG][PromptGenerator] prev_inbody_data is None: {prev_inbody_data is None}")
    print(f"[DEBUG][PromptGenerator] interval_days is None: {interval_days is None}")
    # test를 위해서 interval_days를 10일로 설정  #fixme
    interval_days = "10"
    # 이전 인바디 데이터 포맷팅
    prev_inbody_text = "없음"
    if prev_inbody_data and interval_days:
        print(f"[DEBUG][PromptGenerator] ✅ 이전 인바디 데이터로 텍스트 생성 중...")
        prev_inbody_text = f"""
이전 인바디 데이터와 간격 {interval_days}일
- 변화 체중: {measurements.체중관리.체중 - prev_inbody_data.체중관리.체중} kg
- 변화 골격근량: {measurements.체중관리.골격근량 - prev_inbody_data.체중관리.골격근량} kg
- 변화 체지방률: {measurements.비만분석.체지방률 - prev_inbody_data.비만분석.체지방률}%
- 변화 BMI: {measurements.비만분석.BMI - prev_inbody_data.비만분석.BMI}
- 변화 체지방량: {measurements.체성분.체지방 - prev_inbody_data.체성분.체지방} kg
- 변화 복부지방률: {measurements.비만분석.복부지방률 - prev_inbody_data.비만분석.복부지방률}%
"""
        print(f"[DEBUG][PromptGenerator] prev_inbody_text 생성 완료: {len(prev_inbody_text)} chars")
    else:
        print(f"[DEBUG][PromptGenerator] ⚠️ 이전 인바디 데이터 없음, '없음'으로 설정")


    system_prompt = f"""너는 헬스 유튜브에서 흔히 나오는
        유쾌하지만 팩폭 날리는 PT 코치다.

        인바디 결과를 보고
        유저가 웃으면서도 “아… 해야겠다” 싶게
        6줄 요약을 만든다.

        조건:
        - 딱 5줄 + 마지막 동기부여 1줄 (총 6줄)
        - 말투는 현실적 + 살짝 장난 + 팩트는 정확
        - “복잡하게 하지 말고 이거만 해라” 느낌
        - 운동/식단은 구체적으로 딱 한 가지씩 제시

        -이후 개선사항 및 권장 행동 5줄
        -이후 건강 특이사항 및 주의 포인트 5줄

        출력 규칙 (중요):

        - 숫자/목표는 **굵게 강조**
        - 딱딱한 보고서 말투 금지 ("필요합니다" X)
        - 행동 중심
        - 읽기 쉽게 미션/포인트 느
        - 문장 끝은 가끔 코치 한마디로 마무리


        형식:

        ### [종합 체형 평가]

        😮 체형:
        💪 근육:
        🔥 지방:
        🍽 식단:
        🏋️ 운동:
        📢 한마디:



        ### [📊 이전 기록과의 변화]
        - 이전 인바디 기록 정보는 다음과 같다. {prev_inbody_text}
        - 이전 기록이 있으면 **3~5줄 이내**로 핵심 변화만 해석
        - “이전보다 증가/감소”로 끝내지 말고
        **이 변화가 의미하는 체성분 패턴**을 반드시 설명
        - 이전 기록이 있고 없고는 반드시 구분하여 설명한다. 
        - "없음"이 아니라 변화가 0인 경우는 이전 인바디 기록이 있으나, 변화가 없음을 의미한다. 이에 대한 설명도 반드시 포함한다.
        - 이전 기록이 없으면:
        → “이전 기록 없음” + 현재 상태가 **시작점으로서 어떤 의미인지** 설명

        ### [📈 개선사항 및 권장 행동]
        1. ...
        2. ...
        3. ...
        4. ...
        5. ...
        . ...

        ### [⚠️ 건강 특이사항 및 주의 포인트]
        1. ...
        2. ...
        3. ...
        4. ...
        5. ...
        . ...

        이 섹션 마지막 줄은 반드시
        짧은 동기부여 한방 문장으로 친절하게 끝내라.

        톤:
        - PT쌤이 확신 있게 말하는 느낌
        - 현실적이지만 부드럽게 상대가 공감할 수 있도록 작성


        ## 분석 목표
        사용자가 한눈에 자신의 체성분 상태를 파악하고 즉시 실천할 수 있는 핵심 정보를 제공합니다.


        ---

        스타일 가이드:
        - 절대 비하/조롱/놀리는 말투 금지
        - 사용자를 평가하는 드립 금지 ("불량학생", "게으르네" 등)
        - 무례한 농담 금지
        - 유머는 "가볍고 긍정적인 동기부여" 수준만 허용

        """


    # User prompt 생성
    user_prompt_parts = []

    user_prompt_parts.append("# InBody 측정 데이터\n")

    # 기본 정보
    user_prompt_parts.append("## 기본 정보")
    user_prompt_parts.append(f"- 성별: {measurements.기본정보.성별}")
    user_prompt_parts.append(f"- 나이: {measurements.기본정보.연령}세")
    user_prompt_parts.append(f"- 신장: {measurements.기본정보.신장} cm")
    user_prompt_parts.append(f"- 체중: {measurements.체중관리.체중} kg")


    # 인바디 이전 정보 (데이터가 실제로 있을 때만 포함)
    if prev_inbody_text != "없음":
        user_prompt_parts.append("\n## ⚠️ 이전 인바디 기록과의 비교")
        user_prompt_parts.append(prev_inbody_text)


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
        # Pydantic 모델을 dict로 변환하여 순회
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
    user_prompt_parts.append(
        f"- 체형 분류: {body_type1 or 'N/A'}"
    )
    user_prompt_parts.append(
        f"- 상하체 밸런스: {body_type2 or 'N/A'}"
    )

    user_prompt = "\n".join(user_prompt_parts)

    return system_prompt, user_prompt


def create_weekly_plan_prompt(
    goal_input: GoalPlanInput,
    measurements: InBodyMeasurements,
) -> Tuple[str, str]:
    """
    주간 계획 생성용 프롬프트 생성

    Args:
        goal_input: 사용자 목표 및 분석 결과 입력
        measurements: InBody 측정 데이터

    Returns:
        (system_prompt, user_prompt)
    """
    system_prompt = """당신은 사용자의 건강 데이터와 목표를 분석하여 맞춤형 주간 운동 및 식단 계획을 수립하는 전문 퍼스널 트레이너입니다.
사용자의 신체 상태(인바디), 목표, 그리고 이전 건강 분석 결과를 종합적으로 고려하여 실천 가능하고 효과적인 1주차 계획을 작성해주세요.

## 작성 지침
1. **개인화**: 사용자의 체중, 근육량, 체지방률과 구체적인 목표를 반영하세요.
2. **구체성**: 운동 종목, 세트 수, 식단 메뉴 등을 구체적으로 제시하세요.
3. **안전성**: 사용자의 신체 상태에 무리가 가지 않는 수준으로 설정하세요.
4. **동기부여**: 계획의 의도와 기대 효과를 함께 설명하여 동기를 부여하세요.

## 출력 형식
자연스러운 줄글과 리스트 형식을 혼용하여 가독성 있게 작성해주세요.
- **주간 목표 요약**: 이번 주 집중할 포인트
- **운동 계획**: 요일별 또는 분할별 운동 루틴 (유산소/무산소 비중 포함)
- **식단 가이드**: 아침/점심/저녁/간식 추천 메뉴 및 영양 섭취 포인트
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
        
    user_prompt = "\n".join(user_prompt_parts)
    
    return system_prompt, user_prompt