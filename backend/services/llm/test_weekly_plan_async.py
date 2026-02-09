"""
LLM 호출 성능 테스트 - Async 병렬 방식 (현재 구현)
4개의 LLM Call을 asyncio.gather()로 병렬 실행
"""

import asyncio
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


async def test_async_parallel():
    """Async 병렬 방식 테스트"""
    print("\n" + "="*80)
    print("🔹 Async 병렬 방식 (asyncio.gather)")
    print("="*80)

    # 테스트 데이터 준비
    plan_input, measurements, user_profile = create_test_data()
    llm_client = create_llm_client()

    # 시작 시간 기록
    start_time = time.time()
    start_datetime = datetime.now()
    print(f"⏰ 시작 시각: {start_datetime.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}")

    # 4가지 프롬프트 생성
    prompts = {
        "summary": create_summary_prompt(
            goal_input=plan_input, measurements=measurements, rag_context="", user_profile=user_profile
        ),
        "workout": create_workout_prompt(
            goal_input=plan_input, measurements=measurements, rag_context="", user_profile=user_profile
        ),
        "diet": create_diet_prompt(
            goal_input=plan_input, measurements=measurements, rag_context="", user_profile=user_profile
        ),
        "lifestyle": create_lifestyle_prompt(
            goal_input=plan_input, measurements=measurements, rag_context="", user_profile=user_profile
        ),
    }

    prompt_gen_time = time.time()
    print(f"📝 프롬프트 생성 완료: {(prompt_gen_time - start_time):.3f}초")

    # LLM 비동기 호출 태스크 생성
    tasks = []
    for key, (system_prompt, user_prompt) in prompts.items():
        task = llm_client.agenerate_chat(system_prompt, user_prompt, key)
        tasks.append(task)

    # 모든 LLM 호출을 병렬로 실행
    llm_start_time = time.time()
    results = await asyncio.gather(*tasks)
    llm_end_time = time.time()

    # 결과 처리
    plan_results = {res['key']: res['content'] for res in results}

    # 종료 시간 기록
    end_time = time.time()
    end_datetime = datetime.now()

    # 결과 출력
    print(f"🤖 LLM 호출 완료: {(llm_end_time - llm_start_time):.3f}초")
    print(f"⏰ 종료 시각: {end_datetime.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}")
    print(f"\n📊 총 소요 시간: {(end_time - start_time):.3f}초")
    print(f"   - 프롬프트 생성: {(prompt_gen_time - start_time):.3f}초")
    print(f"   - LLM 호출 (병렬): {(llm_end_time - llm_start_time):.3f}초")
    print(f"   - 후처리: {(end_time - llm_end_time):.3f}초")

    # 각 결과 길이 출력
    print("\n📏 생성된 콘텐츠 길이:")
    for key, content in plan_results.items():
        print(f"   - {key}: {len(content)} characters")

    print("="*80 + "\n")

    return end_time - start_time


if __name__ == "__main__":
    total_time = asyncio.run(test_async_parallel())
    print(f"✅ Async 병렬 방식 총 소요 시간: {total_time:.3f}초")
