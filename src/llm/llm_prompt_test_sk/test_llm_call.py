"""
실제 LLM 호출 테스트 (GPT-4o-mini)
- 샘플 데이터로 프롬프트 생성
- OpenAI API 호출
- 실제 응답 확인
"""

import os
import time
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

# .env 파일 로드 (프로젝트 루트에서 찾기)
env_path = Path(__file__).parent.parent.parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
    print(f"✅ .env 파일 로드: {env_path}")
else:
    # 현재 디렉토리에서도 찾기
    load_dotenv()
    print("⚠️  .env 파일을 찾지 못했습니다. 환경변수를 직접 설정해주세요.")
from sample_data import SAMPLE_USER, SAMPLE_PROFILES, SAMPLE_MEASUREMENTS, SAMPLE_GOAL
from schemas_inbody import InBodyData
from schemas import GoalPlanInput
from prompt_generator_rag import (
    create_weekly_plan_summary_prompt_with_rag,
    create_workout_plan_prompt_with_rag,
    create_diet_plan_prompt_with_rag,
    create_lifestyle_motivation_prompt_with_rag
)
from rule_based_prompts import (
    create_summary_prompt,
    create_workout_prompt,
    create_diet_prompt,
    create_lifestyle_prompt
)


def test_single_profile_with_llm(profile_name: str, profile_data: dict):
    """단일 프로필로 실제 LLM 호출 테스트"""

    print("\n" + "=" * 80)
    print(f"🤖 LLM 호출 테스트: {profile_name}")
    print("=" * 80)
    print(f"체형: {profile_data['body_type1']} / {profile_data['body_type2']}")
    print(f"목표: {profile_data.get('goal_type', '미설정')} | 건강: {profile_data.get('health_specifics') or '특이사항 없음'}")
    print()

    # OpenAI 클라이언트 초기화
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    # 데이터 변환
    measurements = InBodyData(**SAMPLE_MEASUREMENTS)
    goal_input = GoalPlanInput(**SAMPLE_GOAL)

    # ========================================================================
    # Prompt 1: 주간 목표 요약
    # ========================================================================
    print("-" * 80)
    print("🎯 Prompt 1: 주간 목표 요약 (3가지 핵심 전략)")
    print("-" * 80)

    # system_prompt_1, user_prompt_1 = create_weekly_plan_summary_prompt_with_rag(
    #     goal_input=goal_input,
    #     measurements=measurements,
    #     rag_context="",
    #     user_profile=profile_data
    # )

    system_prompt_1, user_prompt_1 = create_summary_prompt(
        goal_input=goal_input,
        measurements=measurements,
        rag_context="",
        user_profile=profile_data
    )

    print("\n[LLM 호출 중...]")
    time_1_start = time.time()

    try:
        response_1 = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt_1},
                {"role": "user", "content": user_prompt_1}
            ],
            temperature=1,
            max_tokens=3000
        )

        time_1 = time.time() - time_1_start
        summary_result = response_1.choices[0].message.content

        print("\n[LLM 응답]")
        print(summary_result)
        print(f"\n사용 토큰: {response_1.usage.total_tokens} | 소요 시간: {time_1:.2f}s")

    except Exception as e:
        time_1 = time.time() - time_1_start
        print(f"\n❌ LLM 호출 실패: {e} ({time_1:.2f}s)")
        summary_result = None

    # ========================================================================
    # Prompt 2: 요일별 운동 계획
    # ========================================================================
    print("\n" + "-" * 80)
    print("🏋️ Prompt 2: 요일별 운동 계획")
    print("-" * 80)

    # system_prompt_2_workout, user_prompt_2_workout = create_workout_plan_prompt_with_rag(
    #     goal_input=goal_input,
    #     measurements=measurements,
    #     rag_context="",
    #     user_profile=profile_data
    # )

    system_prompt_2_workout, user_prompt_2_workout = create_workout_prompt(
        goal_input=goal_input,
        measurements=measurements,
        rag_context="",
        user_profile=profile_data
    )

    # 운동 계획에만 집중하도록 수정
    # system_prompt_2_workout = system_prompt_2_workout + "\n\n**이번 응답은 요일별 운동 계획에만 집중해주세요. 식단이나 생활습관은 제외하고 운동 내용만 작성해주세요.**"

    print("\n[LLM 호출 중...]")
    time_2_start = time.time()

    try:
        response_2 = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt_2_workout},
                {"role": "user", "content": user_prompt_2_workout}
            ],
            temperature=1,
            max_tokens=4000
        )

        time_2 = time.time() - time_2_start
        workout_result = response_2.choices[0].message.content

        print("\n[LLM 응답]")
        print(workout_result)
        print(f"\n사용 토큰: {response_2.usage.total_tokens} | 소요 시간: {time_2:.2f}s")

    except Exception as e:
        time_2 = time.time() - time_2_start
        print(f"\n❌ LLM 호출 실패: {e} ({time_2:.2f}s)")
        workout_result = None

    # ========================================================================
    # Prompt 3: 식단 계획
    # ========================================================================
    print("\n" + "-" * 80)
    print("🍽️ Prompt 3: 식단 계획")
    print("-" * 80)

    # system_prompt_3_diet, user_prompt_3_diet = create_diet_plan_prompt_with_rag(
    #     goal_input=goal_input,
    #     measurements=measurements,
    #     rag_context="",
    #     user_profile=profile_data
    # )
    system_prompt_3_diet, user_prompt_3_diet = create_diet_prompt(
        goal_input=goal_input,
        measurements=measurements,
        rag_context="",
        user_profile=profile_data
    )


    # 식단 계획에만 집중하도록 수정
    # system_prompt_3_diet = system_prompt_3_diet + "\n\n**이번 응답은 식단 계획에만 집중해주세요. 운동이나 생활습관은 제외하고 식단 내용만 작성해주세요.**"

    print("\n[LLM 호출 중...]")
    time_3_start = time.time()

    try:
        response_3 = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt_3_diet},
                {"role": "user", "content": user_prompt_3_diet}
            ],
            temperature=1,
            max_tokens=4000
        )

        time_3 = time.time() - time_3_start
        diet_result = response_3.choices[0].message.content

        print("\n[LLM 응답]")
        print(diet_result)
        print(f"\n사용 토큰: {response_3.usage.total_tokens} | 소요 시간: {time_3:.2f}s")

    except Exception as e:
        time_3 = time.time() - time_3_start
        print(f"\n❌ LLM 호출 실패: {e} ({time_3:.2f}s)")
        diet_result = None

    # ========================================================================
    # Prompt 4: 생활 습관 팁 및 동기부여
    # ========================================================================
    print("\n" + "-" * 80)
    print("💡 Prompt 4: 생활 습관 팁 및 동기부여")
    print("-" * 80)

    # system_prompt_4_lifestyle, user_prompt_4_lifestyle = create_lifestyle_motivation_prompt_with_rag(
    #     goal_input=goal_input,
    #     measurements=measurements,
    #     rag_context="",
    #     user_profile=profile_data
    # )
    system_prompt_4_lifestyle, user_prompt_4_lifestyle = create_lifestyle_prompt(
        goal_input=goal_input,
        measurements=measurements,
        rag_context="",
        user_profile=profile_data
    )

    # 생활 습관 및 동기부여에만 집중하도록 수정
    # system_prompt_4_lifestyle = system_prompt_4_lifestyle + "\n\n**이번 응답은 생활 습관 개선 팁과 동기부여 문장에만 집중해주세요. 운동이나 식단은 제외하고 일상 관리와 동기부여 내용만 작성해주세요.**"

    print("\n[LLM 호출 중...]")
    time_4_start = time.time()

    try:
        response_4 = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt_4_lifestyle},
                {"role": "user", "content": user_prompt_4_lifestyle}
            ],
            temperature=1,
            max_tokens=3000
        )

        time_4 = time.time() - time_4_start
        lifestyle_result = response_4.choices[0].message.content

        print("\n[LLM 응답]")
        print(lifestyle_result)
        print(f"\n사용 토큰: {response_4.usage.total_tokens} | 소요 시간: {time_4:.2f}s")

    except Exception as e:
        time_4 = time.time() - time_4_start
        print(f"\n❌ LLM 호출 실패: {e} ({time_4:.2f}s)")
        lifestyle_result = None

    # ========================================================================
    # 소요 시간 요약
    # ========================================================================
    total_time = time_1 + time_2 + time_3 + time_4
    print("\n" + "-" * 80)
    print("⏱️  소요 시간 요약")
    print("-" * 80)
    print(f"  Call 1 (주간 목표 요약):        {time_1:.2f}s")
    print(f"  Call 2 (요일별 운동 계획):      {time_2:.2f}s")
    print(f"  Call 3 (식단 계획):            {time_3:.2f}s")
    print(f"  Call 4 (생활 습관 팁 및 동기부여): {time_4:.2f}s")
    print(f"  ─────────────────────────────")
    print(f"  총 소요 시간:                  {total_time:.2f}s")

    # ========================================================================
    # 결과 저장
    # ========================================================================
    if summary_result and workout_result and diet_result and lifestyle_result:
        from pathlib import Path
        import json
        from datetime import datetime

        # datetime 객체를 문자열로 변환하는 함수
        def json_serial(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Type {type(obj)} not serializable")

        output_dir = Path(__file__).parent / "output"
        output_dir.mkdir(exist_ok=True)

        # profile_data를 JSON 직렬화 가능하게 변환
        profile_serializable = {
            k: v.isoformat() if isinstance(v, datetime) else v
            for k, v in profile_data.items()
        }

        output_file = output_dir / f"llm_result_{profile_name}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                "profile": profile_serializable,
                "summary": summary_result,
                "workout": workout_result,
                "diet": diet_result,
                "lifestyle": lifestyle_result,
                "tokens_summary": response_1.usage.total_tokens,
                "tokens_workout": response_2.usage.total_tokens,
                "tokens_diet": response_3.usage.total_tokens,
                "tokens_lifestyle": response_4.usage.total_tokens,
                "tokens_total": (response_1.usage.total_tokens +
                                response_2.usage.total_tokens +
                                response_3.usage.total_tokens +
                                response_4.usage.total_tokens)
            }, f, ensure_ascii=False, indent=2)

        print(f"\n💾 결과 저장: {output_file.name}")

    return summary_result, workout_result, diet_result, lifestyle_result


def test_quick_single():
    """빠른 단일 테스트 (SAMPLE_USER만)"""

    # API 키 확인
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")
        print("\n설정 방법:")
        print("  export OPENAI_API_KEY='your-api-key'")
        return

    print("🚀 빠른 테스트 모드 (SAMPLE_USER)")
    test_single_profile_with_llm("SAMPLE_USER", SAMPLE_USER)



if __name__ == "__main__":


    test_quick_single()

    print("\n" + "=" * 80)
    print("✅ 테스트 완료")
    print("=" * 80)
    print("\n결과 파일 확인:")
    print("  - output/llm_result_*.json")
    print()
