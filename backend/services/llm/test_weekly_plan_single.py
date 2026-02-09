"""
LLM 호출 성능 테스트 - Single Call 방식
4개의 프롬프트를 하나로 합쳐서 1번의 LLM Call로 처리
"""

import time
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

from services.llm.llm_clients import create_llm_client
from services.llm.rule_based_prompts import (
    create_summary_prompt,
    create_workout_prompt,
    create_diet_prompt,
    create_lifestyle_prompt,
)
from schemas.llm import GoalPlanInput
from schemas.inbody import InBodyData as InBodyMeasurements


# 테스트 데이터 생성
def create_test_data():
    """테스트용 샘플 데이터 생성"""
    measurements_dict = {
        "기본정보": {"성별": "남성", "연령": 30, "신장": 175},
        "체중관리": {
            "체중": 75.0,
            "골격근량": 32.5,
            "적정체중": 70.0,
            "체중조절": -5.0,
            "지방조절": -3.5,
            "근육조절": 1.5
        },
        "체성분": {
            "체수분": 45.0,
            "단백질": 12.0,
            "무기질": 3.5,
            "체지방": 15.0
        },
        "비만분석": {
            "BMI": 24.5,
            "체지방률": 20.0,
            "복부지방률": 0.85,
            "내장지방레벨": 8,
            "비만도": 107
        },
        "연구항목": {
            "기초대사량": 1650,
            "권장섭취열량": 2200
        },
        "부위별근육분석": {
            "오른팔": "보통",
            "왼팔": "보통",
            "몸통": "부족",
            "오른다리": "우수",
            "왼다리": "우수"
        },
        "부위별체지방분석": {
            "오른팔": "표준",
            "왼팔": "표준",
            "몸통": "과다",
            "오른다리": "표준",
            "왼다리": "표준"
        }
    }

    plan_input_dict = {
        "user_goal_type": "감량",
        "user_goal_description": "건강하게 5kg 감량하기",
        "record_id": 1,
        "user_id": 1,
        "measured_at": datetime.now(),
        "measurements": measurements_dict,
        "status_analysis_result": "현재 체지방률이 높고 복부지방이 과다합니다.",
        "status_analysis_id": 1,
        "user_profile": {
            "body_type1": "비만형",
            "body_type2": "표준형",
            "health_specifics": "",
            "preferences": ""
        }
    }

    measurements = InBodyMeasurements(**measurements_dict)
    plan_input = GoalPlanInput(**plan_input_dict)
    user_profile = plan_input_dict["user_profile"]

    return plan_input, measurements, user_profile


def test_single_combined():
    """Single Call 방식 테스트 - 모든 프롬프트를 하나로 합침"""
    print("\n" + "="*80)
    print("🔹 Single Call 방식 (4개 프롬프트 합쳐서 1번 호출)")
    print("="*80)

    # 테스트 데이터 준비
    plan_input, measurements, user_profile = create_test_data()
    llm_client = create_llm_client()

    # 시작 시간 기록
    start_time = time.time()
    start_datetime = datetime.now()
    print(f"⏰ 시작 시각: {start_datetime.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}")

    # 4가지 프롬프트 생성
    summary_prompts = create_summary_prompt(
        goal_input=plan_input, measurements=measurements, rag_context="", user_profile=user_profile
    )
    workout_prompts = create_workout_prompt(
        goal_input=plan_input, measurements=measurements, rag_context="", user_profile=user_profile
    )
    diet_prompts = create_diet_prompt(
        goal_input=plan_input, measurements=measurements, rag_context="", user_profile=user_profile
    )
    lifestyle_prompts = create_lifestyle_prompt(
        goal_input=plan_input, measurements=measurements, rag_context="", user_profile=user_profile
    )

    prompt_gen_time = time.time()
    print(f"📝 개별 프롬프트 생성 완료: {(prompt_gen_time - start_time):.3f}초")

    # 모든 system_prompt와 user_prompt를 하나로 합치기
    combined_system_prompt = f"""당신은 전문 퍼스널 트레이너입니다.
사용자의 주간 건강 계획을 다음 4가지 섹션으로 나누어 작성해주세요:

1. 주간 목표 핵심 전략 (Summary)
2. 요일별 운동 계획 (Workout)
3. 일일 식단 계획 (Diet)
4. 생활 습관 및 동기부여 (Lifestyle)

각 섹션은 아래의 지침을 따라 작성해주세요:

---
[1. Summary 섹션 지침]
{summary_prompts[0]}

---
[2. Workout 섹션 지침]
{workout_prompts[0]}

---
[3. Diet 섹션 지침]
{diet_prompts[0]}

---
[4. Lifestyle 섹션 지침]
{lifestyle_prompts[0]}
"""

    combined_user_prompt = f"""다음 사용자 정보를 바탕으로 4가지 섹션을 모두 작성해주세요:

---
[Summary용 사용자 정보]
{summary_prompts[1]}

---
[Workout용 사용자 정보]
{workout_prompts[1]}

---
[Diet용 사용자 정보]
{diet_prompts[1]}

---
[Lifestyle용 사용자 정보]
{lifestyle_prompts[1]}

---

출력 형식:
반드시 다음 형식으로 작성해주세요:

### 📝 주간 목표 핵심 전략
[여기에 summary 내용]

### 🏋️‍♀️ 요일별 운동 계획
[여기에 workout 내용]

### 🍽️ 일일 식단 계획
[여기에 diet 내용]

### 💡 생활 습관 및 동기부여
[여기에 lifestyle 내용]
"""

    combine_time = time.time()
    print(f"🔗 프롬프트 통합 완료: {(combine_time - prompt_gen_time):.3f}초")
    print(f"   - Combined system_prompt: {len(combined_system_prompt)} characters")
    print(f"   - Combined user_prompt: {len(combined_user_prompt)} characters")

    # 단일 LLM 호출
    llm_start_time = time.time()
    print(f"\n🤖 통합 LLM 호출 중...", end=" ")

    response = llm_client.generate_chat(combined_system_prompt, combined_user_prompt)

    llm_end_time = time.time()
    print(f"완료 ({(llm_end_time - llm_start_time):.3f}초)")

    # 종료 시간 기록
    end_time = time.time()
    end_datetime = datetime.now()

    # 결과 출력
    print(f"⏰ 종료 시각: {end_datetime.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}")
    print(f"\n📊 총 소요 시간: {(end_time - start_time):.3f}초")
    print(f"   - 개별 프롬프트 생성: {(prompt_gen_time - start_time):.3f}초")
    print(f"   - 프롬프트 통합: {(combine_time - prompt_gen_time):.3f}초")
    print(f"   - LLM 호출 (단일): {(llm_end_time - llm_start_time):.3f}초")
    print(f"   - 후처리: {(end_time - llm_end_time):.3f}초")

    # 결과 길이 출력
    print(f"\n📏 생성된 콘텐츠 길이:")
    print(f"   - 전체 응답: {len(response)} characters")

    # 샘플 출력 (처음 500자)
    print(f"\n📄 응답 샘플 (처음 500자):")
    print("-" * 80)
    print(response[:500])
    if len(response) > 500:
        print(f"... (총 {len(response)}자 중 500자만 표시)")
    print("-" * 80)

    print("="*80 + "\n")

    return end_time - start_time


if __name__ == "__main__":
    total_time = test_single_combined()
    print(f"✅ Single Call 방식 총 소요 시간: {total_time:.3f}초")
