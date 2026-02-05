"""
주간 계획 생성을 위한 병렬 처리 LangGraph 노드
- 4개의 LLM 호출(요약, 운동, 식단, 생활)을 비동기 병렬로 처리하여 초기 계획을 생성합니다.
"""

import asyncio
import sys
from pathlib import Path
from typing import TypedDict, Annotated

# --- 프로젝트 루트 경로를 sys.path에 추가 ---
# backend와 src 모듈을 모두 가져오기 위함
# 이 파일의 위치: backend/services/llm/initial_plan_node.py
project_root = Path(__file__).parent.parent.parent.parent
src_path = project_root / "src"

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))
# -----------------------------------------

from langgraph.graph.message import add_messages

from backend.schemas.inbody import InBodyData as InBodyMeasurements
from backend.schemas.llm import GoalPlanInput
# `llm.rule_based_prompts`는 `src` 디렉토리 아래에 있습니다.
from llm.rule_based_prompts import (
    create_summary_prompt,
    create_workout_prompt,
    create_diet_prompt,
    create_lifestyle_prompt,
)


# --- 1. 상태 정의 (weekly_plan_graph.py와 동일하게 유지) ---
class PlanState(TypedDict):
    """LLM2 (주간 계획 / Q&A) 에이전트의 상태"""
    plan_input: GoalPlanInput
    messages: Annotated[list, add_messages]


# --- 2. 새로운 비동기 노드 정의 ---
async def generate_initial_plan_concurrently(state: PlanState, llm_client) -> dict:
    """
    Node: 주간 계획 초안 병렬 생성
    4개의 LLM Call(요약, 운동, 식단, 라이프스타일)을 동시에 실행하여 결과를 취합합니다.
    """
    print("--- LLM2: 주간 계획 병렬 생성 시작 ---")
    plan_input = state["plan_input"]

    # InBody 데이터 모델 변환
    measurements = InBodyMeasurements(**plan_input.measurements)
    # 사용자 프로필 데이터 추출 (test_llm_call.py의 profile_data와 유사)
    # GoalPlanInput에 user_profile이 포함되어 있다고 가정합니다.
    # 만약 없다면, PlanState에 추가해야 합니다.
    user_profile = plan_input.user_profile if hasattr(plan_input, 'user_profile') else {}

    # --- 4가지 프롬프트 생성 ---
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

    # --- LLM 비동기 호출 태스크 생성 ---
    # llm_client에 `agenerate_chat`과 같은 비동기 메서드가 있다고 가정합니다.
    tasks = []
    for key, (system_prompt, user_prompt) in prompts.items():
        # llm_client의 비동기 메서드를 호출합니다.
        # (예: agenerate_chat, generate_chat_async 등)
        task = llm_client.agenerate_chat(system_prompt, user_prompt, key)
        tasks.append(task)

    # --- 모든 LLM 호출을 병렬로 실행 ---
    print("--- LLM2: 4개 계획 동시 생성 중... ---")
    results = await asyncio.gather(*tasks)
    
    # 결과를 딕셔너리로 재구성
    plan_results = {res['key']: res['content'] for res in results}
    summary_result = plan_results.get("summary", "주간 목표 요약 생성에 실패했습니다.")
    workout_result = plan_results.get("workout", "운동 계획 생성에 실패했습니다.")
    diet_result = plan_results.get("diet", "식단 계획 생성에 실패했습니다.")
    lifestyle_result = plan_results.get("lifestyle", "생활 습관 및 동기부여 메시지 생성에 실패했습니다.")

    # --- 최종 결과 포맷팅 ---
    combined_response = f"""### 📝 주간 목표 핵심 전략
{summary_result}

### 🏋️‍♀️ 요일별 운동 계획
{workout_result}

### 🍽️ 일일 식단 계획
{diet_result}

### 💡 생활 습관 및 동기부여
{lifestyle_result}

---
위 계획에 대해 궁금한 점이 있거나 수정을 원하시면 언제든지 말씀해주세요!
"""
    print("--- LLM2: 주간 계획 병렬 생성 완료 ---")

    # --- 상태 업데이트 ---
    # weekly_plan_graph.py의 기존 노드와 동일한 형식으로 반환
    # 초기 사용자 질문을 "human" 메시지로 추가
    initial_user_message = state["messages"][-1].content if state["messages"] and state["messages"][-1].type == "human" else "주간 계획을 만들어주세요."

    return {"messages": [("human", initial_user_message), ("ai", combined_response)]}
