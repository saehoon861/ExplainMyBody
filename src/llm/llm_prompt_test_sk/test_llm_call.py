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


def test_single_profile_with_llm(profile_name: str, profile_data: dict):
    """단일 프로필로 실제 LLM 호출 테스트"""

    print("\n" + "=" * 80)
    print(f"🤖 LLM 호출 테스트: {profile_name}")
    print("=" * 80)
    print(f"체형: {profile_data['body_type1']} / {profile_data['body_type2']}")
    print(f"장소: {profile_data['workout_place']}")
    if profile_data.get('preferred_sport'):
        print(f"스포츠: {profile_data['preferred_sport']}")
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

    system_prompt_1, user_prompt_1 = create_weekly_plan_summary_prompt_with_rag(
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

    system_prompt_2_workout, user_prompt_2_workout = create_workout_plan_prompt_with_rag(
        goal_input=goal_input,
        measurements=measurements,
        rag_context="",
        user_profile=profile_data
    )

    # 운동 계획에만 집중하도록 수정
    system_prompt_2_workout = system_prompt_2_workout + "\n\n**이번 응답은 요일별 운동 계획에만 집중해주세요. 식단이나 생활습관은 제외하고 운동 내용만 작성해주세요.**"

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

    system_prompt_3_diet, user_prompt_3_diet = create_diet_plan_prompt_with_rag(
        goal_input=goal_input,
        measurements=measurements,
        rag_context="",
        user_profile=profile_data
    )

    # 식단 계획에만 집중하도록 수정
    system_prompt_3_diet = system_prompt_3_diet + "\n\n**이번 응답은 식단 계획에만 집중해주세요. 운동이나 생활습관은 제외하고 식단 내용만 작성해주세요.**"

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

    system_prompt_4_lifestyle, user_prompt_4_lifestyle = create_lifestyle_motivation_prompt_with_rag(
        goal_input=goal_input,
        measurements=measurements,
        rag_context="",
        user_profile=profile_data
    )

    # 생활 습관 및 동기부여에만 집중하도록 수정
    system_prompt_4_lifestyle = system_prompt_4_lifestyle + "\n\n**이번 응답은 생활 습관 개선 팁과 동기부여 문장에만 집중해주세요. 운동이나 식단은 제외하고 일상 관리와 동기부여 내용만 작성해주세요.**"

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


def test_all_profiles_with_llm():
    """모든 샘플 프로필로 LLM 호출"""

    print("\n" + "=" * 80)
    print("🧪 실제 LLM 호출 테스트 (GPT-4o-mini)")
    print("=" * 80)

    # API 키 확인
    if not os.getenv("OPENAI_API_KEY"):
        print("\n❌ OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")
        print("\n설정 방법:")
        print("  export OPENAI_API_KEY=your-api-key")
        return

    print("\n✅ OpenAI API 키 확인됨")
    print("⚠️  주의: 실제 API 호출이 이루어지며 비용이 발생합니다.")

    # 사용자 확인
    confirm = input("\n계속하시겠습니까? (y/n): ")
    if confirm.lower() != 'y':
        print("취소됨")
        return

    # 기본 프로필 테스트
    test_single_profile_with_llm("SAMPLE_USER", SAMPLE_USER)

    # 추가 프로필 테스트 여부
    print("\n" + "=" * 80)
    confirm = input("다른 프로필도 테스트하시겠습니까? (y/n): ")
    if confirm.lower() == 'y':
        for name, profile in SAMPLE_PROFILES.items():
            test_single_profile_with_llm(name, profile)


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


def test_random_profiles(count: int = 1):
    """
    랜덤 프로필 테스트

    Args:
        count: 테스트할 프로필 개수 (기본: 1)
    """
    import random

    # API 키 확인
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")
        print("\n설정 방법:")
        print("  export OPENAI_API_KEY='your-api-key'")
        return

    print("\n" + "=" * 80)
    print(f"🎲 랜덤 프로필 테스트 ({count}개)")
    print("=" * 80)
    print(f"\n전체 프로필: {len(SAMPLE_PROFILES)}개")
    print(f"테스트 대상: {count}개 (랜덤 선택)")

    # 사용 가능한 프로필 목록
    all_profiles = list(SAMPLE_PROFILES.items())

    # count가 전체보다 크면 전체 개수로 제한
    count = min(count, len(all_profiles))

    # 랜덤 샘플링
    selected = random.sample(all_profiles, count)

    print("\n선택된 프로필:")
    for i, (name, _) in enumerate(selected, 1):
        print(f"  {i}. {name}")

    # 사용자 확인
    print(f"\n⚠️  주의: {count}개 프로필 × 4개 프롬프트 = {count*4}회 API 호출")
    print(f"예상 비용: 약 ${count * 0.006:.4f} (~{int(count * 0.006 * 1300)}원)")

    confirm = input("\n계속하시겠습니까? (y/n): ")
    if confirm.lower() != 'y':
        print("취소됨")
        return

    # 선택된 프로필 테스트
    results = []
    for i, (name, profile) in enumerate(selected, 1):
        print(f"\n{'='*80}")
        print(f"[{i}/{count}] {name}")
        print(f"{'='*80}")

        summary, workout, diet, lifestyle = test_single_profile_with_llm(name, profile)
        results.append({
            "name": name,
            "profile": profile,
            "success": all([summary, workout, diet, lifestyle])
        })

    # 결과 요약
    print("\n" + "=" * 80)
    print("📊 테스트 결과 요약")
    print("=" * 80)

    success_count = sum(1 for r in results if r["success"])
    print(f"\n성공: {success_count}/{count}")
    print(f"실패: {count - success_count}/{count}")

    print("\n개별 결과:")
    for i, result in enumerate(results, 1):
        status = "✅" if result["success"] else "❌"
        print(f"  {i}. {status} {result['name']}")

    return results


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        arg = sys.argv[1]

        if arg == "--quick":
            # 빠른 모드: SAMPLE_USER만 테스트
            test_quick_single()

        elif arg.startswith("--random"):
            # 랜덤 모드: --random 또는 --random=N
            if "=" in arg:
                count = int(arg.split("=")[1])
            else:
                # --random N 형식
                count = int(sys.argv[2]) if len(sys.argv) > 2 else 1

            test_random_profiles(count)

        else:
            print("사용법:")
            print("  python test_llm_call.py              # 전체 프로필 테스트")
            print("  python test_llm_call.py --quick      # SAMPLE_USER만 테스트")
            print("  python test_llm_call.py --random     # 랜덤 1개 테스트")
            print("  python test_llm_call.py --random=3   # 랜덤 3개 테스트")
            print("  python test_llm_call.py --random 2   # 랜덤 2개 테스트")
            sys.exit(1)
    else:
        # 전체 모드: 모든 프로필 테스트
        test_all_profiles_with_llm()

    print("\n" + "=" * 80)
    print("✅ 테스트 완료")
    print("=" * 80)
    print("\n결과 파일 확인:")
    print("  - output/llm_result_*.json")
    print()
