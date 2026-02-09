"""
Rule-Based Prompt Generator
- 룰 우선순위: Health (최우선) > Goal > BodyType1 > BodyType2 > Preference
- 4개 독립 프롬프트: 주간 목표 요약 / 운동 계획 / 식단 계획 / 생활 습관
- 호출 인터페이스: create_XXX(goal_input, measurements, rag_context, user_profile) → (system, user)
- user_profile에 health_specifics, preferences 키 추가하면 Health/Preference 룰 자동 적용
- 룰 데이터는 rules.py에서 관리 (향후 DB 로드 대응)
"""

from typing import Tuple, Dict, Any, List, Optional
from schemas.inbody import InBodyData as InBodyMeasurements
from schemas.llm import GoalPlanInput
from .rules import (
    BODY_TYPE1_RULES, BODY_TYPE2_RULES, HEALTH_RULES,
    GOAL_RULES, PREFERENCE_RULES, REHAB_RULES,
    EXERCISE_TYPE_LIST, EXERCISE_TYPE_RULES,
)


# =============================================================================
# 파싱 헬퍼
# =============================================================================

def _parse_health_conditions(health_specifics: str) -> List[str]:
    """health_specifics → HEALTH_RULES 키로 매칭
    예: "고혈압, 관절염 (상세 설명)" → ["고혈압", "관절염"]
    """
    if not health_specifics:
        return []
    return [i.strip() for i in health_specifics.split("(")[0].split(",") if i.strip() in HEALTH_RULES]


def _parse_goals(goal_type: str) -> List[str]:
    """goal_type → GOAL_RULES 키로 매칭
    예: "감량, 재활" → ["감량", "재활"]
    """
    if not goal_type:
        return []
    return [i.strip() for i in goal_type.split(",") if i.strip() in GOAL_RULES]


def _parse_activity_level(preferences: str) -> str:
    """preferences → 활동레벨 추출
    예: "활동레벨: 보통, 유산소, 웨이트" → "보통"
    """
    if not preferences:
        return "보통"
    for part in preferences.split(","):
        part = part.strip()
        if part.startswith("활동레벨:"):
            level = part.replace("활동레벨:", "").strip()
            if level in PREFERENCE_RULES:
                return level
    return "보통"


def _parse_rehab(goal_description: str) -> List[str]:
    """goal_description에서 재활 부위 추출
    예: "허리 재활" → ["허리 재활"]
    """
    if not goal_description:
        return []
    return [part for part in REHAB_RULES if part in goal_description]


def _parse_preferred_exercises(preferences: str) -> List[str]:
    """preferences에서 선호 운동 타입 목록 추출 (활동레벨 제외)
    예: "활동레벨: 보통, 유산소, 웨이트, 걷기" → ["유산소", "웨이트", "걷기"]
    """
    if not preferences:
        return []
    return [i.strip() for i in preferences.split(",") if i.strip() in EXERCISE_TYPE_LIST]


# =============================================================================
# 룰 합성 (Priority: Health > Goal > BodyType1 > BodyType2 > Preference)
# =============================================================================

def _synthesize(goal_input: GoalPlanInput, user_profile: Dict[str, Any]) -> Dict[str, Any]:
    """모든 룰을 우선순위에 따라 한 구조로 합성"""

    body_type1 = user_profile.get("body_type1", "알 수 없음")
    body_type2 = user_profile.get("body_type2", "표준형")
    health_specifics = user_profile.get("health_specifics", "")
    preferences = user_profile.get("preferences", "")

    # goal_type: goal_input이 있으면 거기서, 없으면 user_profile에서
    goal_type = (
        goal_input.user_goal_type
        if goal_input and goal_input.user_goal_type
        else user_profile.get("goal_type", "")
    )

    health_conditions = _parse_health_conditions(health_specifics)
    goals = _parse_goals(goal_type)
    activity_level = _parse_activity_level(preferences)
    preferred_exercises = _parse_preferred_exercises(preferences)

    # --- Health 룰 수집 (최우선) ---
    health_forbid, health_require, health_prefer = [], [], []
    for cond in health_conditions:
        rule = HEALTH_RULES[cond]
        health_forbid.extend(rule.get("forbid", []))
        health_require.extend(rule.get("require", []))
        health_prefer.extend(rule.get("prefer", []))

    # --- Rehab 룰 수집 (Health와 동등 우선순위) ---
    rehab_parts: List[str] = []
    if "재활" in goals and goal_input and goal_input.user_goal_description:
        rehab_parts = _parse_rehab(goal_input.user_goal_description)
        for part in rehab_parts:
            rule = REHAB_RULES[part]
            health_forbid.extend(rule.get("forbid", []))
            health_require.extend(rule.get("require", []))
            health_prefer.extend(rule.get("prefer", []))

    # --- Goal 룰 수집 ---
    goal_diet_require, goal_diet_keep = [], []
    goal_training_require, goal_training_avoid = [], []
    for g in goals:
        rule = GOAL_RULES[g]
        goal_diet_require.extend(rule["diet"].get("require", []))
        goal_diet_keep.extend(rule["diet"].get("keep", []))
        goal_training_require.extend(rule["training"].get("require", []))
        goal_training_avoid.extend(rule["training"].get("avoid", []))

    # --- 매칭 안된 값 수집 (룰 없이 그대로 LLM에 전달) ---
    # 이미 파싱된 결과와 원본 차이로 미매칭 항목 도출
    unmatched: Dict[str, List[str]] = {}

    if health_specifics:
        if "(" in health_specifics:
            unmatched["health_detail"] = [health_specifics.split("(", 1)[1].rstrip(")").strip()]
        all_health = [i.strip() for i in health_specifics.split("(")[0].split(",") if i.strip()]
        raw_health = [i for i in all_health if i not in health_conditions]
        if raw_health:
            unmatched["health"] = raw_health

    if goal_type:
        all_goals = [i.strip() for i in goal_type.split(",") if i.strip()]
        raw_goal = [i for i in all_goals if i not in goals]
        if raw_goal:
            unmatched["goal"] = raw_goal

    if preferences:
        if activity_level == "보통" and "활동레벨:" in preferences:
            # _parse_activity_level이 매칭 못 한 경우 원본값 전달
            for part in preferences.split(","):
                part = part.strip()
                if part.startswith("활동레벨:"):
                    level = part.replace("활동레벨:", "").strip()
                    if level not in PREFERENCE_RULES:
                        unmatched["activity_level"] = [level]
        all_exercises = [i.strip() for i in preferences.split(",") if i.strip() and not i.strip().startswith("활동레벨:")]
        raw_exercises = [i for i in all_exercises if i not in preferred_exercises]
        if raw_exercises:
            unmatched["exercises"] = raw_exercises

    return {
        "health": {
            "conditions": health_conditions,
            "rehab_parts": rehab_parts,
            "forbid": health_forbid,
            "require": health_require,
            "prefer": health_prefer,
        },
        "goal": {
            "goals": goals,
            "diet": {"require": goal_diet_require, "keep": goal_diet_keep},
            "training": {"require": goal_training_require, "avoid": goal_training_avoid},
        },
        "body_type1": {
            "name": body_type1,
            "rule": BODY_TYPE1_RULES.get(body_type1, BODY_TYPE1_RULES["알 수 없음"]),
        },
        "body_type2": {
            "name": body_type2,
            "rule": BODY_TYPE2_RULES.get(body_type2, BODY_TYPE2_RULES["표준형"]),
        },
        "preference": {
            "level": activity_level,
            "rule": PREFERENCE_RULES.get(activity_level, PREFERENCE_RULES["보통"]),
            "exercises": preferred_exercises,
        },
        "unmatched": unmatched,
    }


# =============================================================================
# 텍스트 블록 빌더 (각 프롬프트에서 필요한 부분만 조합)
# =============================================================================

def _facts_block(s: Dict, goal_input: GoalPlanInput) -> str:
    """공통 INPUT FACTS"""
    all_health = s["health"]["conditions"] + s["health"].get("rehab_parts", [])
    health_str = ", ".join(all_health) or "특이사항 없음"
    goal_str = ", ".join(s["goal"]["goals"]) or "미설정"
    return (
        f"[INPUT FACTS]\n"
        f"- BodyType1: {s['body_type1']['name']}\n"
        f"- BodyType2: {s['body_type2']['name']}\n"
        f"- Goal: {goal_str}\n"
        f"- Health: {health_str}\n"
        f"- Preference: 강도 {s['preference']['level']}\n"
        f"- 선호 운동: {', '.join(s['preference']['exercises']) if s['preference']['exercises'] else '미설정'}\n"
        f"- 목표 상세: {goal_input.user_goal_description or '미설정'}"
    )


def _health_block(s: Dict) -> str:
    """⚠️ Health + Rehab 룰 (forbid/require/prefer) — 조건 없으면 빈 문자열"""
    all_conditions = s["health"]["conditions"] + s["health"].get("rehab_parts", [])
    if not all_conditions:
        return ""
    lines = [f"⚠️ [HEALTH RULES - 최우선 준수] ({', '.join(all_conditions)})"]
    if s["health"]["forbid"]:
        lines.append(f"  ⛔ 금지 (절대 포함 안함): {', '.join(s['health']['forbid'])}")
    if s["health"]["require"]:
        lines.append(f"  ✅ 필수 반영: {', '.join(s['health']['require'])}")
    if s["health"]["prefer"]:
        lines.append(f"  👍 우선 추천: {', '.join(s['health']['prefer'])}")
    return "\n".join(lines)


def _workout_block(s: Dict) -> str:
    """운동 관련 룰 블록 (Goal training + BodyType1 training + BodyType2 adjustment + Preference)"""
    bt1 = s["body_type1"]["rule"]
    bt2 = s["body_type2"]["rule"]
    pref = s["preference"]["rule"]
    goal = s["goal"]

    lines = ["[WORKOUT RULES]"]

    # Goal → training
    if goal["training"]["require"]:
        lines.append(f"  목표 필수: {', '.join(goal['training']['require'])}")
    if goal["training"]["avoid"]:
        lines.append(f"  목표 회피: {', '.join(goal['training']['avoid'])}")

    # BodyType1 → training
    if bt1["training"].get("prefer"):
        lines.append(f"  체형1 선호: {', '.join(bt1['training']['prefer'])}")
    if bt1["training"].get("avoid"):
        lines.append(f"  체형1 회피: {', '.join(bt1['training']['avoid'])}")

    # BodyType2 → 상하체 조정
    adj = bt2.get("training_adjustment", {})
    if adj.get("lower"):
        lines.append(f"  하체 조정: {', '.join(adj['lower'])}")
    if adj.get("upper"):
        lines.append(f"  상체 조정: {', '.join(adj['upper'])}")

    # Preference
    if pref.get("prefer"):
        lines.append(f"  선호도 추천: {', '.join(pref['prefer'])}")
    if pref.get("avoid"):
        lines.append(f"  선호도 회피: {', '.join(pref['avoid'])}")

    # 사용자 선호 운동 타입 (룰로 확장)
    if s["preference"]["exercises"]:
        for ex in s["preference"]["exercises"]:
            rule = EXERCISE_TYPE_RULES.get(ex, {})
            examples = ", ".join(rule.get("core_examples", []))
            intensity = rule.get("intensity", "")
            note = rule.get("usage_note", "")
            detail = f"{examples} ({intensity})" if examples else ""
            line = f"  {ex}: {detail}"
            if note:
                line += f" — {note}"
            lines.append(line)

    return "\n".join(lines)


def _diet_block(s: Dict, measurements: InBodyMeasurements) -> str:
    """식단 관련 룰 블록 (Goal diet + BodyType1 diet + 대사 정보)"""
    bt1 = s["body_type1"]["rule"]
    goal = s["goal"]

    lines = ["[DIET RULES]"]

    # Goal → diet
    if goal["diet"]["require"]:
        lines.append(f"  목표 필수: {', '.join(goal['diet']['require'])}")
    if goal["diet"]["keep"]:
        lines.append(f"  목표 유지: {', '.join(goal['diet']['keep'])}")

    # BodyType1 → diet
    if bt1["diet"].get("require"):
        lines.append(f"  체형 필수: {', '.join(bt1['diet']['require'])}")
    if bt1["diet"].get("avoid"):
        lines.append(f"  체형 회피: {', '.join(bt1['diet']['avoid'])}")

    # 대사 정보
    if measurements.연구항목.기초대사량:
        lines.append(f"  기초대사량: {measurements.연구항목.기초대사량} kcal")
    if measurements.연구항목.권장섭취열량:
        lines.append(f"  권장 섭취열량: {measurements.연구항목.권장섭취열량} kcal")

    return "\n".join(lines)


def _coach_block(s: Dict) -> str:
    """코치 톤 블록 (BodyType1 + BodyType2)"""
    bt1_tone = s["body_type1"]["rule"].get("coach_tone", "")
    bt2_tone = s["body_type2"]["rule"].get("coach_tone", "")
    lines = ["[COACH TONE]"]
    if bt1_tone:
        lines.append(f"  체형: {bt1_tone}")
    if bt2_tone:
        lines.append(f"  밸런스: {bt2_tone}")
    return "\n".join(lines)


def _raw_block(s: Dict) -> str:
    """룰 매칭 안된 값 → 그대로 LLM에 참고용으로 전달 (빈 경우 빈 문자열)"""
    unmatched = s.get("unmatched", {})
    if not unmatched:
        return ""
    lines = ["[참고 - 룰 매칭 안됨, 그대로 참고하세요]"]
    if "health" in unmatched:
        lines.append(f"  건강 관련: {', '.join(unmatched['health'])}")
    if "health_detail" in unmatched:
        lines.append(f"  건강 상세: {unmatched['health_detail'][0]}")
    if "goal" in unmatched:
        lines.append(f"  목표: {', '.join(unmatched['goal'])}")
    if "activity_level" in unmatched:
        lines.append(f"  활동레벨: {unmatched['activity_level'][0]}")
    if "exercises" in unmatched:
        lines.append(f"  운동 종류: {', '.join(unmatched['exercises'])}")
    return "\n".join(lines)


# =============================================================================
# Prompt 1: 주간 목표 요약
# =============================================================================

def create_summary_prompt(
    goal_input: GoalPlanInput,
    measurements: InBodyMeasurements,
    rag_context: str = "",
    user_profile: Optional[Dict[str, Any]] = None,
) -> Tuple[str, str]:
    """주간 목표 요약 — 전체 룰을 종합하여 핵심 전략 3가지 정리"""

    s = _synthesize(goal_input, user_profile or {})

    system_prompt = """당신은 체형과 건강 상태를 종합하여 주간 핵심 전략을 정리하는 PT입니다.
존댓말로 작성합니다.

반드시 준수:
- forbid 항목은 전략에 절대 포함하지 않습니다.
- require 항목은 반드시 반영합니다.
- prefer 항목은 가능하면 반영합니다.
"""

    user_prompt = f"""# 사용자 정보

{_facts_block(s, goal_input)}

# 신체 정보
- 체중: {measurements.체중관리.체중}kg
- BMI: {measurements.비만분석.BMI}
- 골격근량: {measurements.체중관리.골격근량}kg
- 체지방률: {measurements.비만분석.체지방률}%
{"- 기초대사량: " + str(measurements.연구항목.기초대사량) + "kcal" if measurements.연구항목.기초대사량 else ""}

---

# 룰 기반 전략 (모두 참고)

{_health_block(s)}

{_workout_block(s)}

{_diet_block(s, measurements)}

{_coach_block(s)}

{_raw_block(s)}

{rag_context}

---

출력 형식:

🎯 주간 목표 (한 줄 요약)

💪 핵심 전략 1:
🔥 핵심 전략 2:
🍽  핵심 전략 3:
"""
    return system_prompt, user_prompt


# =============================================================================
# Prompt 2: 요일별 운동 계획
# =============================================================================

def create_workout_prompt(
    goal_input: GoalPlanInput,
    measurements: InBodyMeasurements,
    rag_context: str = "",
    user_profile: Optional[Dict[str, Any]] = None,
) -> Tuple[str, str]:
    """요일별 운동 계획 — Health forbid를 절대 어기지 않고 운동 스케줄 작성"""

    s = _synthesize(goal_input, user_profile or {})

    system_prompt = """당신은 체형과 건강 상태를 고려한 요일별 운동 계획을 작성하는 퍼스널 트레이너입니다.

반드시 준수:
- [HEALTH RULES]의 forbid 항목은 운동 계획에 절대 포함하지 않습니다.
- require 항목은 반드시 계획에 포함합니다.
- 각 운동마다 세트×횟수, 중량/시간을 구체적으로 제시합니다.
- 휴식일도 명시합니다.
- [WORKOUT RULES]의 선호/회피 방향을 반영합니다.
"""

    available_days = goal_input.available_days_per_week or 5
    available_time = goal_input.available_time_per_session or 60

    user_prompt = f"""# 사용자 정보

{_facts_block(s, goal_input)}

- 주당 운동 가능: {available_days}일
- 회당 시간: {available_time}분
- 체중: {measurements.체중관리.체중}kg
- 골격근량: {measurements.체중관리.골격근량}kg

---

# 운동 관련 룰 (반드시 준수)

{_health_block(s)}

{_workout_block(s)}

{_raw_block(s)}

{rag_context}

---

출력 형식:

🏋️ **요일별 운동 계획** (주 {available_days}일, 휴식일 포함)

**월요일:**
- 메인: [운동명] [세트×횟수] [중량/시간]
- 보조: [운동명] [세트×횟수]
- 마무리: [스트레칭/유산소]

**화요일:**
...

(주당 {available_days}일 기준, 휴식일 포함하여 7일 전체 작성)
"""
    return system_prompt, user_prompt


# =============================================================================
# Prompt 3: 식단 계획
# =============================================================================

def create_diet_prompt(
    goal_input: GoalPlanInput,
    measurements: InBodyMeasurements,
    rag_context: str = "",
    user_profile: Optional[Dict[str, Any]] = None,
) -> Tuple[str, str]:
    """식단 계획 — Goal diet + BodyType1 diet 룰을 기반으로 식단 가이드 작성"""

    s = _synthesize(goal_input, user_profile or {})

    system_prompt = """당신은 체형과 목표에 맞는 식단 계획을 작성하는 영양 전문가입니다.

반드시 준수:
- [DIET RULES]의 require 항목은 반드시 식단에 반영합니다.
- avoid 항목은 식단에 포함하지 않습니다.
- 기초대사량과 권장 섭취열량을 기준으로 칼로리를 설정합니다.
- 단백질/탄수화물/지방 비율과 일일 단백질 목표를 명시합니다.
"""

    user_prompt = f"""# 사용자 정보

{_facts_block(s, goal_input)}

- 체중: {measurements.체중관리.체중}kg
- 골격근량: {measurements.체중관리.골격근량}kg
- 체지방률: {measurements.비만분석.체지방률}%

---

# 식단 관련 룰 (반드시 준수)

{_diet_block(s, measurements)}

{_raw_block(s)}

{rag_context}

---

출력 형식:

🍽 **식단 계획**

**일일 목표 칼로리:** XXX kcal
**영양소 비율:** 단백질 XX% / 탄수화물 XX% / 지방 XX%
**일일 단백질 목표:** XXg

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


# =============================================================================
# Prompt 4: 생활 습관 팁 및 동기부여
# =============================================================================

def create_lifestyle_prompt(
    goal_input: GoalPlanInput,
    measurements: InBodyMeasurements,
    rag_context: str = "",
    user_profile: Optional[Dict[str, Any]] = None,
) -> Tuple[str, str]:
    """생활 습관 팁 및 동기부여 — BodyType 코치 톤을 참고하여 작성"""

    s = _synthesize(goal_input, user_profile or {})

    system_prompt = """당신은 건강한 생활 습관을 돕는 친절한 라이프 코치입니다.

작성 지침:
- 실천 가능한 생활 습관 팁을 3~5가지 작성합니다.
- 수면, 수분, 스트레스 관리를 반드시 포함합니다.
- [COACH TONE]을 참고하여 사용자의 체형과 상황에 맞게 톤을 조정합니다.
- 마지막에 강력하고 긍정적인 동기부여 문장으로 끝냅니다.
"""

    user_prompt = f"""# 사용자 정보

{_facts_block(s, goal_input)}

- 체지방률: {measurements.비만분석.체지방률}%
- 골격근량: {measurements.체중관리.골격근량}kg
{"- 기초대사량: " + str(measurements.연구항목.기초대사량) + "kcal" if measurements.연구항목.기초대사량 else ""}

---

# 코치 톤 참고

{_coach_block(s)}

{_raw_block(s)}

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
[강력하고 긍정적인 동기부여 문장 2~3줄]
"""
    return system_prompt, user_prompt
