"""
주간 계획 생성용 프롬프트
"""

from typing import List, Dict, Any, Tuple
from shared.models import UserGoal, UserPreferences
from datetime import datetime, timedelta


def create_weekly_plan_prompt(
    user_goals: List[UserGoal],
    user_preferences: UserPreferences,
    inbody_context: List[Dict[str, Any]],
    week_number: int = 1,
    start_date: str = None,
) -> Tuple[str, str]:
    """
    주간 운동/식단 계획 생성 프롬프트

    Args:
        user_goals: 사용자 목표 리스트
        user_preferences: 사용자 선호도
        inbody_context: RAG 검색된 인바디 분석 결과
        week_number: 주차
        start_date: 시작 날짜 (YYYY-MM-DD)

    Returns:
        (system_prompt, user_prompt)
    """

    system_prompt = """당신은 20년 경력의 퍼스널 트레이너이자 영양 전문가입니다.

사용자의 **InBody 분석 결과**, **목표**, **선호도**, **건강 특이사항**을 종합하여
실현 가능하고 효과적인 **주간 운동 및 식단 계획**을 작성하세요.

## 계획 수립 원칙

1. **개인 맞춤화**
   - InBody 분석 결과 기반 약점 보완
   - 사용자 목표에 최적화 (체중 감량, 근육 증가 등)
   - 선호도와 제약사항 반드시 고려

2. **점진적 발전**
   - 초기 주차: 기본 체력 및 적응
   - 중기 주차: 강도 상승
   - 후기 주차: 목표 달성 집중

3. **실현 가능성**
   - 사용자의 운동 빈도/시간 준수
   - 식단 제한사항 엄수 (알레르기, 채식 등)
   - 부상 위험 최소화

4. **균형**
   - 운동: 근력 + 유산소 + 스트레칭 균형
   - 식단: 3대 영양소 균형
   - 휴식: 적절한 회복 시간



```json
{
  "weekly_summary": "이번 주 전체 요약 및 목표",
  "weekly_goal": "이번 주 구체적 목표",
  "tips": ["팁1", "팁2", "팁3"],
  "daily_plans": [
    {
      "day_of_week": "월요일",
      "exercises": [
        {
          "name": "벤치프레스",
          "category": "웨이트",
          "target_muscle": "가슴",
          "sets": 3,
          "reps": "12회",
          "rest_seconds": 60,
          "notes": "천천히 수축"
        }
      ],
      "meals": [
        {
          "meal_type": "아침",
          "foods": ["현미밥 1공기", "계란 2개", "샐러드"],
          "calories": 450,
          "protein_g": 25,
          "carbs_g": 50,
          "fat_g": 12,
          "notes": "운동 2시간 전 섭취"
        }
      ],
      "total_calories": 1800,
      "notes": "상체 집중 날"
    }
  ]
}
```

**중요**:
- 모든 요일 (월~일) 포함
- 구체적인 수치 제시 (세트, 횟수, 칼로리 등)
- 실행 가능한 운동과 음식 추천"""

    # User prompt 생성
    user_prompt_parts = []

    # 1. 기간 정보
    user_prompt_parts.append(f"# 주간 계획 생성 요청\n")
    user_prompt_parts.append(f"## 기간 정보")
    user_prompt_parts.append(f"- 주차: {week_number}주차")

    if start_date:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = start + timedelta(days=6)
        user_prompt_parts.append(f"- 시작: {start.strftime('%Y년 %m월 %d일')}")
        user_prompt_parts.append(f"- 종료: {end.strftime('%Y년 %m월 %d일')}")
    else:
        user_prompt_parts.append(f"- 시작: 다음 주 월요일")

    # 2. InBody 분석 결과 (RAG Context)
    user_prompt_parts.append("\n## InBody 분석 결과 (참고용)")

    if inbody_context:
        latest = inbody_context[0]
        user_prompt_parts.append(f"\n### 최신 분석 ({latest.get('generated_at', 'N/A')})")
        user_prompt_parts.append(latest.get("analysis_text", ""))

        # 측정 데이터 요약
        if "measurements" in latest:
            m = latest["measurements"]
            user_prompt_parts.append("\n### 주요 수치")
            user_prompt_parts.append(f"- BMI: {m.get('BMI', 'N/A')}")
            user_prompt_parts.append(f"- 체지방률: {m.get('체지방률', 'N/A')}%")
            user_prompt_parts.append(f"- 골격근량: {m.get('골격근량', 'N/A')} kg")
            user_prompt_parts.append(
                f"- 체형: {m.get('stage2_근육보정체형', 'N/A')} / {m.get('stage3_상하체밸런스', 'N/A')}"
            )
    else:
        user_prompt_parts.append("  (분석 결과 없음)")

    # 3. 사용자 목표
    user_prompt_parts.append("\n## 사용자 목표")

    if user_goals:
        for i, goal in enumerate(user_goals, 1):
            user_prompt_parts.append(f"\n### 목표 {i}")
            user_prompt_parts.append(f"- 유형: {goal.goal_type}")
            if goal.target_weight:
                user_prompt_parts.append(f"- 목표 체중: {goal.target_weight} kg")
            if goal.target_body_fat:
                user_prompt_parts.append(f"- 목표 체지방률: {goal.target_body_fat}%")
            if goal.target_muscle:
                user_prompt_parts.append(f"- 목표 골격근량: {goal.target_muscle} kg")
            if goal.deadline:
                user_prompt_parts.append(f"- 기한: {goal.deadline}")
            user_prompt_parts.append(f"- 우선순위: {goal.priority}")
    else:
        user_prompt_parts.append("  (목표 설정 안 함)")

    # 4. 운동 선호도
    user_prompt_parts.append("\n## 운동 선호도")
    user_prompt_parts.append(
        f"- 선호 운동: {', '.join(user_preferences.preferred_exercise_types) if user_preferences.preferred_exercise_types else '제한 없음'}"
    )
    user_prompt_parts.append(
        f"- 주간 운동 횟수: {user_preferences.exercise_frequency or '유연'}회"
    )
    user_prompt_parts.append(
        f"- 1회 운동 시간: {user_preferences.exercise_duration or '유연'}분"
    )
    user_prompt_parts.append(f"- 운동 강도: {user_preferences.exercise_intensity}")

    # 5. 식단 선호도
    user_prompt_parts.append("\n## 식단 선호도")
    user_prompt_parts.append(
        f"- 식단 제한: {', '.join(user_preferences.dietary_restrictions) if user_preferences.dietary_restrictions else '없음'}"
    )
    user_prompt_parts.append(
        f"- 선호 음식: {', '.join(user_preferences.preferred_cuisine) if user_preferences.preferred_cuisine else '제한 없음'}"
    )
    user_prompt_parts.append(
        f"- 비선호 음식: {', '.join(user_preferences.disliked_foods) if user_preferences.disliked_foods else '없음'}"
    )
    user_prompt_parts.append(
        f"- 하루 식사 횟수: {user_preferences.meal_frequency or '3'}회"
    )

    # 6. 건강 특이사항
    user_prompt_parts.append("\n## 건강 특이사항")

    if user_preferences.health_conditions:
        user_prompt_parts.append(
            f"- 건강 상태: {', '.join(user_preferences.health_conditions)}"
        )
    if user_preferences.injuries:
        user_prompt_parts.append(f"- 부상 이력: {', '.join(user_preferences.injuries)}")
    if user_preferences.medications:
        user_prompt_parts.append(
            f"- 복용 약물: {', '.join(user_preferences.medications)}"
        )

    if (
        not user_preferences.health_conditions
        and not user_preferences.injuries
        and not user_preferences.medications
    ):
        user_prompt_parts.append("  (특이사항 없음)")

    # 7. 요청사항
    user_prompt_parts.append("\n## 요청사항")
    user_prompt_parts.append("위 정보를 바탕으로 **주간 운동 및 식단 계획**을 JSON 형식으로 생성해주세요.")
    user_prompt_parts.append("- 요일별 (월~일) 운동 및 식단 포함")
    user_prompt_parts.append("- 구체적인 운동 종목, 세트/횟수, 칼로리/영양소 수치 포함")
    user_prompt_parts.append("- 사용자 제약사항 및 선호도 반드시 준수")

    user_prompt = "\n".join(user_prompt_parts)

    return system_prompt, user_prompt
