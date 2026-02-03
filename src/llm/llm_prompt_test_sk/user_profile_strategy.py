"""
사용자 프로필 기반 전략 텍스트 생성
- user_profile_rules.py의 룰을 사용하여 전략 생성
- 샘플 데이터와 실제 DB 데이터 모두 호환
- weekly_plan_system.py와는 독립적으로 운영
"""

from typing import Optional, Dict, Any
from user_profile_rules import (
    BODY_TYPE1_RULES,
    BODY_TYPE2_RULES,
    WORKOUT_PLACE_RULES,
    SPORT_SUPPLEMENT_RULES,
    BodyType1,
    BodyType2,
    WorkoutPlace,
    SportType,
)


def build_strategy_text_from_dict(user_data: Dict[str, Any]) -> str:
    """
    딕셔너리 형태의 사용자 데이터를 받아 전략 텍스트 생성

    Args:
        user_data: {
            "body_type1": str,
            "body_type2": str,
            "workout_place": str,
            "preferred_sport": Optional[str]
        }

    Returns:
        전략 텍스트 (프롬프트에 삽입 가능)

    Example:
        >>> from sample_data import SAMPLE_USER
        >>> strategy = build_strategy_text_from_dict(SAMPLE_USER)
        >>> print(strategy)
    """
    body_type1 = user_data.get("body_type1", "알 수 없음")
    body_type2 = user_data.get("body_type2", "표준형")
    workout_place = user_data.get("workout_place", "헬스장")
    preferred_sport = user_data.get("preferred_sport")

    # Fallback으로 안전하게 룰 가져오기
    t1 = BODY_TYPE1_RULES.get(body_type1, BODY_TYPE1_RULES["알 수 없음"])  # type: ignore
    t2 = BODY_TYPE2_RULES.get(body_type2, BODY_TYPE2_RULES["표준형"])  # type: ignore
    tp = WORKOUT_PLACE_RULES.get(workout_place, WORKOUT_PLACE_RULES["헬스장"])  # type: ignore

    strategy_text = f"""
[전체 체형 전략]
- 목표: {t1['goal']}
- 식단: {t1['diet']}
- 운동: {t1['training']}
- ⚠️ 주의: {t1['warning']}
- 💬 코치: {t1['coach']}

[상하체 밸런스]
- 포커스: {t2['focus']}
- 루틴 조정: {t2['training_adjust']}
- 💬 코치: {t2['coach']}

[운동 장소: {workout_place}]
- 환경: {tp['environment']}
- 스타일: {tp['routine_style']}
- 주의: {tp['constraints']}
- 💬 코치: {tp['coach']}
"""

    # 스포츠 선택 시 보완 운동 추가
    if workout_place == "스포츠" and preferred_sport:
        sport = SPORT_SUPPLEMENT_RULES.get(preferred_sport, SPORT_SUPPLEMENT_RULES["기타"])  # type: ignore
        strategy_text += f"""
[선택 스포츠: {preferred_sport}]
- 집중 부위: {sport['focus']}
- 보완 운동: {sport['supplement']}
- ⚠️ 부상 주의: {sport['warning']}
"""

    return strategy_text.strip()


def get_strategy_summary(user_data: Dict[str, Any]) -> Dict[str, str]:
    """
    전략의 핵심 요약만 추출 (프롬프트에서 선택적으로 사용)

    Returns:
        {
            "goal": "목표",
            "focus": "포커스",
            "environment": "운동 환경",
            "coach_tip": "코치 조언"
        }
    """
    body_type1 = user_data.get("body_type1", "알 수 없음")
    body_type2 = user_data.get("body_type2", "표준형")
    workout_place = user_data.get("workout_place", "헬스장")

    t1 = BODY_TYPE1_RULES.get(body_type1, BODY_TYPE1_RULES["알 수 없음"])  # type: ignore
    t2 = BODY_TYPE2_RULES.get(body_type2, BODY_TYPE2_RULES["표준형"])  # type: ignore
    tp = WORKOUT_PLACE_RULES.get(workout_place, WORKOUT_PLACE_RULES["헬스장"])  # type: ignore

    return {
        "goal": t1["goal"],
        "focus": t2["focus"],
        "environment": tp["environment"],
        "coach_tip": t1["coach"]
    }


# =============================================================================
# 테스트용 함수
# =============================================================================

def test_strategy_generation():
    """샘플 데이터로 전략 텍스트 생성 테스트"""
    from sample_data import SAMPLE_USER, SAMPLE_PROFILES

    print("=" * 60)
    print("📋 SAMPLE_USER 전략 텍스트")
    print("=" * 60)
    print(build_strategy_text_from_dict(SAMPLE_USER))

    print("\n" + "=" * 60)
    print("📋 SAMPLE_PROFILES 테스트")
    print("=" * 60)

    for name, profile in SAMPLE_PROFILES.items():
        print(f"\n[{name}]")
        print("-" * 40)
        strategy = build_strategy_text_from_dict(profile)
        # 간략히 출력
        lines = strategy.split('\n')
        for line in lines[:3]:  # 처음 3줄만
            print(line)
        print("...")

    print("\n" + "=" * 60)
    print("📊 전략 요약 테스트")
    print("=" * 60)
    summary = get_strategy_summary(SAMPLE_USER)
    for key, value in summary.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    test_strategy_generation()
