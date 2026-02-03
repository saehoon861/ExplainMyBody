"""
사용자 프로필 기반 프롬프트 생성 테스트
- sample_data의 다양한 프로필로 프롬프트 확인
- 실제 LLM 호출 전 프롬프트 검증용
"""

from sample_data import SAMPLE_USER, SAMPLE_PROFILES, SAMPLE_MEASUREMENTS, SAMPLE_GOAL
from schemas_inbody import InBodyData
from schemas import GoalPlanInput
from prompt_generator_rag import (
    create_weekly_plan_summary_prompt_with_rag,
    create_weekly_plan_detail_prompt_with_rag
)


def test_single_profile(profile_name: str, profile_data: dict):
    """단일 프로필로 프롬프트 생성 테스트"""

    print("=" * 80)
    print(f"📋 프로필: {profile_name}")
    print("=" * 80)
    print(f"체형: {profile_data['body_type1']} / {profile_data['body_type2']}")
    print(f"장소: {profile_data['workout_place']}")
    if profile_data.get('preferred_sport'):
        print(f"스포츠: {profile_data['preferred_sport']}")
    print()

    # InBody 데이터 변환
    measurements = InBodyData(**SAMPLE_MEASUREMENTS)

    # Goal 데이터 변환
    goal_input = GoalPlanInput(**SAMPLE_GOAL)

    # Prompt 1: 주간 목표 요약
    print("-" * 80)
    print("🎯 Prompt 1: 주간 목표 요약")
    print("-" * 80)

    system_prompt_1, user_prompt_1 = create_weekly_plan_summary_prompt_with_rag(
        goal_input=goal_input,
        measurements=measurements,
        rag_context="",
        user_profile=profile_data
    )

    print("\n[System Prompt]")
    print(system_prompt_1[:200] + "...")

    print("\n[User Prompt - 전략 섹션만 발췌]")
    lines = user_prompt_1.split('\n')
    strategy_start = False
    for line in lines:
        if '[전체 체형 전략]' in line:
            strategy_start = True
        if strategy_start:
            print(line)
            if '[선택 스포츠:' in line or (strategy_start and line.strip() == "" and "[운동 장소:" not in line):
                break

    # Prompt 2: 주간 계획 세부사항
    print("\n" + "-" * 80)
    print("📅 Prompt 2: 주간 계획 세부사항")
    print("-" * 80)

    system_prompt_2, user_prompt_2 = create_weekly_plan_detail_prompt_with_rag(
        goal_input=goal_input,
        measurements=measurements,
        rag_context="",
        user_profile=profile_data
    )

    print("\n[System Prompt]")
    print(system_prompt_2[:200] + "...")

    print("\n[User Prompt - 전략 포함 확인]")
    if '[전체 체형 전략]' in user_prompt_2:
        print("✅ 전략 텍스트 포함됨")
    else:
        print("❌ 전략 텍스트 없음")

    print("\n")


def test_all_profiles():
    """모든 샘플 프로필 테스트"""

    print("\n" + "=" * 80)
    print("🧪 사용자 프로필 기반 프롬프트 생성 테스트")
    print("=" * 80 + "\n")

    # 기본 프로필 (SAMPLE_USER)
    test_single_profile("SAMPLE_USER (기본)", SAMPLE_USER)

    # 다양한 프로필
    for name, profile in SAMPLE_PROFILES.items():
        test_single_profile(name, profile)


def test_strategy_extraction():
    """전략 텍스트만 추출해서 확인"""
    from user_profile_strategy import build_strategy_text_from_dict

    print("\n" + "=" * 80)
    print("📊 전략 텍스트 단독 테스트")
    print("=" * 80 + "\n")

    for name, profile in SAMPLE_PROFILES.items():
        print(f"[{name}]")
        print("-" * 40)
        strategy = build_strategy_text_from_dict(profile)
        print(strategy)
        print("\n")


def test_without_profile():
    """프로필 없이 프롬프트 생성 (기존 방식)"""

    print("\n" + "=" * 80)
    print("🔄 프로필 없이 프롬프트 생성 (하위 호환성 테스트)")
    print("=" * 80 + "\n")

    measurements = InBodyData(**SAMPLE_MEASUREMENTS)
    goal_input = GoalPlanInput(**SAMPLE_GOAL)

    system_prompt, user_prompt = create_weekly_plan_summary_prompt_with_rag(
        goal_input=goal_input,
        measurements=measurements,
        rag_context="",
        user_profile=None  # 프로필 없음
    )

    if '[전체 체형 전략]' in user_prompt:
        print("❌ 실패: 프로필 없는데 전략 포함됨")
    else:
        print("✅ 성공: 프로필 없으면 전략 제외")

    print("\n[User Prompt 일부]")
    print(user_prompt[:500] + "...")


if __name__ == "__main__":
    # 1. 모든 프로필 테스트
    test_all_profiles()

    # 2. 전략 텍스트 단독 확인
    test_strategy_extraction()

    # 3. 하위 호환성 테스트
    test_without_profile()

    print("\n" + "=" * 80)
    print("✅ 테스트 완료")
    print("=" * 80)
    print("\n다음 단계:")
    print("1. 프롬프트 검증 완료 후 실제 LLM 호출")
    print("2. DB 연동 시 user_profile dict를 DB에서 가져오기")
    print("3. Pydantic 모델로 검증 추가")
    print()
