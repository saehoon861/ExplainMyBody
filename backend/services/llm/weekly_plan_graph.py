import asyncio
from typing import TypedDict, Annotated, Optional
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from dotenv import load_dotenv

load_dotenv()

from services.llm.llm_clients import create_llm_client
from schemas.llm import GoalPlanInput
from schemas.inbody import InBodyData as InBodyMeasurements
from .rule_based_prompts import (
    create_summary_prompt,
    create_workout_prompt,
    create_diet_prompt,
    create_lifestyle_prompt,
)


# --- 1. 상태 정의 ---
class PlanState(TypedDict):
    """LLM2 (주간 계획 / Q&A) 에이전트의 상태"""
    plan_input: GoalPlanInput
    messages: Annotated[list, add_messages]
    # 사용자 피드백을 명시적으로 관리하기 위한 필드 추가
    feedback_category: Optional[str]
    feedback_text: Optional[str]
    # 기존 계획 내용 주입용 (새 세션에서 맥락 제공)
    existing_plan: Optional[str]


# --- 2. 병렬 비동기 초기 계획 생성 함수 ---
async def generate_initial_plan_concurrently(state: PlanState, llm_client) -> dict:
    """
    Node: 주간 계획 초안 병렬 생성
    4개의 LLM Call(요약, 운동, 식단, 라이프스타일)을 동시에 실행하여 결과를 취합합니다.
    """
    print("\n" + "="*80)
    print("--- [DEBUG] generate_initial_plan_concurrently 함수 진입 ---")
    print("--- LLM2: 주간 계획 생성 (병렬 실행) ---")
    print(f"--- [DEBUG] state 타입: {type(state)}")
    print(f"--- [DEBUG] llm_client 타입: {type(llm_client)}")
    print("="*80 + "\n")

    plan_input = state["plan_input"]
    print(f"--- [DEBUG] plan_input 추출 완료: {type(plan_input)}")

    # InBody 데이터 모델 변환
    measurements = InBodyMeasurements(**plan_input.measurements)
    print(f"--- [DEBUG] measurements 변환 완료: {type(measurements)}")

    user_profile = plan_input.user_profile if hasattr(plan_input, 'user_profile') else {}
    print(f"--- [DEBUG] user_profile: {user_profile}")

    # --- 4가지 프롬프트 생성 ---
    print("--- [DEBUG] 4가지 프롬프트 생성 시작 ---")
    prompts = {}

    try:
        print("--- [DEBUG] summary 프롬프트 생성 중... ---")
        prompts["summary"] = create_summary_prompt(
            goal_input=plan_input, measurements=measurements, rag_context="", user_profile=user_profile
        )
        print(f"--- [DEBUG] summary 프롬프트 생성 완료: {type(prompts['summary'])} ---")
    except Exception as e:
        print(f"--- [ERROR] summary 프롬프트 생성 실패: {type(e).__name__}: {str(e)} ---")
        raise

    try:
        print("--- [DEBUG] workout 프롬프트 생성 중... ---")
        prompts["workout"] = create_workout_prompt(
            goal_input=plan_input, measurements=measurements, rag_context="", user_profile=user_profile
        )
        print(f"--- [DEBUG] workout 프롬프트 생성 완료: {type(prompts['workout'])} ---")
    except Exception as e:
        print(f"--- [ERROR] workout 프롬프트 생성 실패: {type(e).__name__}: {str(e)} ---")
        raise

    try:
        print("--- [DEBUG] diet 프롬프트 생성 중... ---")
        prompts["diet"] = create_diet_prompt(
            goal_input=plan_input, measurements=measurements, rag_context="", user_profile=user_profile
        )
        print(f"--- [DEBUG] diet 프롬프트 생성 완료: {type(prompts['diet'])} ---")
    except Exception as e:
        print(f"--- [ERROR] diet 프롬프트 생성 실패: {type(e).__name__}: {str(e)} ---")
        raise

    try:
        print("--- [DEBUG] lifestyle 프롬프트 생성 중... ---")
        prompts["lifestyle"] = create_lifestyle_prompt(
            goal_input=plan_input, measurements=measurements, rag_context="", user_profile=user_profile
        )
        print(f"--- [DEBUG] lifestyle 프롬프트 생성 완료: {type(prompts['lifestyle'])} ---")
    except Exception as e:
        print(f"--- [ERROR] lifestyle 프롬프트 생성 실패: {type(e).__name__}: {str(e)} ---")
        raise

    print(f"--- [DEBUG] 모든 프롬프트 생성 완료, 총 {len(prompts)}개 ---")

    # --- LLM 비동기 호출 태스크 생성 ---
    print("--- [DEBUG] LLM 비동기 태스크 생성 시작 ---")
    tasks = []
    for key, (system_prompt, user_prompt) in prompts.items():
        print(f"--- [DEBUG] 태스크 생성 중: {key}")
        task = llm_client.agenerate_chat(system_prompt, user_prompt, key)
        print(f"--- [DEBUG] 태스크 타입: {type(task)}")
        tasks.append(task)
    print(f"--- [DEBUG] 총 {len(tasks)}개 태스크 생성 완료")

    # --- 모든 LLM 호출을 병렬로 실행 ---
    print("--- [DEBUG] asyncio.gather() 호출 시작 ---")
    try:
        results = await asyncio.gather(*tasks)
        print(f"--- [DEBUG] asyncio.gather() 완료, 결과 개수: {len(results)}")
    except Exception as e:
        print(f"--- [ERROR] asyncio.gather() 실패: {type(e).__name__}: {str(e)}")
        raise

    # 결과를 딕셔너리로 재구성
    print("--- [DEBUG] 결과 재구성 시작 ---")
    plan_results = {res['key']: res['content'] for res in results}
    print(f"--- [DEBUG] plan_results keys: {list(plan_results.keys())}")

    summary_result = plan_results.get("summary", "주간 목표 요약 생성에 실패했습니다.")
    workout_result = plan_results.get("workout", "운동 계획 생성에 실패했습니다.")
    diet_result = plan_results.get("diet", "식단 계획 생성에 실패했습니다.")
    lifestyle_result = plan_results.get("lifestyle", "생활 습관 및 동기부여 메시지 생성에 실패했습니다.")
    print("--- [DEBUG] 4가지 결과 추출 완료")

    # --- 최종 결과 포맷팅 ---
    print("--- [DEBUG] 최종 응답 포맷팅 시작 ---")
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

    # 사용자 프롬프트는 생략하고 AI 응답만 반환
    print(f"--- [DEBUG] combined_response 길이: {len(combined_response)} characters")
    result = {"messages": [("ai", combined_response)]}
    print(f"--- [DEBUG] 반환 결과 타입: {type(result)}")
    print("--- [DEBUG] generate_initial_plan_concurrently 함수 정상 종료 ---\n")
    return result


# --- 3. 그래프 생성 ---
def create_weekly_plan_agent(llm_client):
    """주간 계획 생성 및 수정을 위한 에이전트 그래프 생성"""
    print("\n" + "="*80)
    print("--- [DEBUG] create_weekly_plan_agent 함수 호출됨 ---")
    print(f"--- [DEBUG] llm_client 타입: {type(llm_client)}")
    print("="*80 + "\n")

    # --- 2. 노드 정의 ---
    def _generate_feedback_response(state: PlanState, category_name: str, system_prompt: str) -> dict:
        """공통 피드백 기반 답변 생성 로직"""
        print(f"--- LLM2: 주간 계획 피드백 반영 ({category_name}) ---")

        # [강력 조치] 시스템 프롬프트에 직접 현재 계획 정보 주입
        existing_plan = state.get("existing_plan")
        if existing_plan:
            system_prompt += f"\n\n[참고: 현재 사용자의 주간 계획 정보]\n{existing_plan}\n\n사용자의 질문이나 요청이 위 계획과 관련이 있다면, 이 내용을 바탕으로 답변하거나 수정해주세요."
            print(f"--- [DEBUG] 시스템 프롬프트에 existing_plan 컨텍스트 주입 완료 ---")

        for i, msg in enumerate(state["messages"]):
            msg_content = msg.content if msg.content else ""
            print(f"--- [DEBUG] msg[{i}] type={msg.type}, content={msg_content[:50].replace(chr(10), ' ')}... ---")

        history = []

        # AI 메시지(기존 계획)가 히스토리에 없고 existing_plan이 있으면 맥락으로 주입
        has_ai_message = any(msg.type == "ai" for msg in state["messages"])
        if not has_ai_message and existing_plan:
            print("--- [DEBUG] 히스토리에 기존 계획 주입 (Assistant 메시지로 추가) ---")
            history.append(("assistant", existing_plan))
        else:
            print(f"--- [DEBUG] 히스토리 주입 스킵: has_ai_msg={has_ai_message}, has_plan={bool(existing_plan)} ---")

        for msg in state["messages"]:
            role = "user" if msg.type == "human" else "assistant"
            # OpenAI API는 content가 None인 것을 허용하지 않으므로, None일 경우 빈 문자열로 변환합니다.
            content = msg.content if msg.content is not None else ""
            history.append((role, content))

        feedback_text = state.get("feedback_text")
        if feedback_text:
            history.append(("user", feedback_text))

        print(f"--- [DEBUG] LLM 호출 직전 히스토리 총 메시지 수: {len(history)} ---")

        response = llm_client.generate_chat_with_history(
            system_prompt=system_prompt,
            messages=history
        )

        # 피드백 처리 후 상태 초기화
        return {"messages": [("ai", response)], "feedback_category": None, "feedback_text": None}

    def adjust_exercise_plan(state: PlanState) -> dict:
        """Node 2-1: 운동 플랜 조정"""
        system_prompt = """당신은 전문 트레이너입니다.
        사용자가 운동 플랜(일정, 종목, 분할 방식 등)의 조정을 요청했습니다.
        기존 계획과 사용자의 피드백을 바탕으로 수정된 **구체적인 전체 주간 운동 계획표**를 다시 제시해주세요.
        수정된 이유도 함께 설명하면 좋습니다."""
        return _generate_feedback_response(state, "운동 플랜 조정", system_prompt)

    def adjust_diet_plan(state: PlanState) -> dict:
        """Node 2-2: 식단 조정"""
        system_prompt = """당신은 영양 전문가입니다.
        사용자가 식단 계획의 조정을 요청했습니다.
        기존 계획과 사용자의 피드백(기호, 알레르기, 상황 등)을 바탕으로 수정된 **구체적인 전체 주간 식단 계획표**를 다시 제시해주세요.
        칼로리와 영양 밸런스를 고려하여 조언해주세요."""
        return _generate_feedback_response(state, "식단 조정", system_prompt)

    def adjust_intensity(state: PlanState) -> dict:
        """Node 2-3: 강도 조정"""
        system_prompt = """당신은 전문 트레이너입니다.
        사용자가 운동 강도(무게, 횟수, 세트, 휴식 시간 등)의 조정을 요청했습니다.
        기존 계획과 사용자의 피드백을 바탕으로 강도를 높이거나 낮춘 **구체적인 전체 주간 운동 계획표**를 다시 제시해주세요.
        부상 방지를 위한 조언도 포함해주세요."""
        return _generate_feedback_response(state, "강도 조정", system_prompt)

    def qa_general(state: PlanState) -> dict:
        """Node 2-4: 일반 Q&A"""
        system_prompt = """당신은 사용자의 주간 운동 및 식단 계획을 담당하는 퍼스널 트레이너입니다.
        사용자가 생성된 계획에 대해 질문하면, 전문적이고 친절하게 답변해주세요.
        이전 대화 맥락(사용자의 신체 정보, 목표, 생성된 계획)을 모두 고려해야 합니다."""
        return _generate_feedback_response(state, "일반 Q&A", system_prompt)

    def router(state: PlanState) -> dict:
        """라우팅을 위한 빈 노드. 상태 변경 없음."""
        print("--- 라우터 진입 ---")
        return {}

    def finalize_plan(state: PlanState) -> dict:
        """Node 3: 계획 확정 및 저장"""
        print("--- LLM2: 계획 확정 ---")
        final_plan_message = state["messages"][-1].content
        return {
            "messages": [
                ("ai", f"네, 알겠습니다. 현재 계획을 최종 플랜으로 저장하겠습니다.\n\n{final_plan_message}")
            ]
        }

    def route_feedback(state: PlanState) -> str:
        """사용자 피드백 카테고리에 따른 라우팅"""
        print("\n" + "="*80)
        print("--- [DEBUG] route_feedback function called ---")
        category = state.get("feedback_category")
        print(f"--- [DEBUG] Current State 'feedback_category': {category}")
        print(f"--- [DEBUG] State type: {type(state)}")
        print(f"--- [DEBUG] State keys: {list(state.keys()) if isinstance(state, dict) else 'N/A'}")

        if not category:
            # feedback_category가 없을 경우, 일반 Q&A 요청으로 간주
            # 기존 chat API 호출은 여기에 해당하며 qa_general 노드로 라우팅
            print("--- 라우팅: 피드백 카테고리 없음, 일반 Q&A (폴백) ---")
            print("="*80 + "\n")
            return "qa_general" # 기존 chat API 호환성을 위해 qa_general로 바로 라우팅

        print(f"--- 라우팅: {category} ---")
        if category == "운동 플랜 조정" or category == "adjust_exercise_plan":
            print("="*80 + "\n")
            return "adjust_exercise_plan"
        elif category == "식단 조정" or category == "adjust_diet_plan":
            print("="*80 + "\n")
            return "adjust_diet_plan"
        elif category == "강도 조정" or category == "adjust_intensity":
            print("="*80 + "\n")
            return "adjust_intensity"
        elif category == "최종 플랜으로 저장" or category == "finalize_plan":
            print("="*80 + "\n")
            return "finalize_plan"
        else:
            # 정의되지 않은 카테고리의 경우에도 일반 Q&A로 처리
            print(f"--- 라우팅: 알 수 없는 카테고리 '{category}', 일반 Q&A로 처리 ---")
            print("="*80 + "\n")
            return "qa_general"

    print("--- [DEBUG] StateGraph 생성 ---")
    workflow = StateGraph(PlanState)

    # 비동기 노드 추가 (async wrapper 함수 사용)
    print("--- [DEBUG] initial_plan 노드 추가 시작 ---")
    print("--- [DEBUG] ✅ Async wrapper 함수 사용으로 LangGraph가 async를 올바르게 감지 ---")

    async def _initial_plan_wrapper(state: PlanState) -> dict:
        """Initial plan 노드를 위한 async wrapper"""
        print("--- [DEBUG] _initial_plan_wrapper 호출됨 ---")
        result = await generate_initial_plan_concurrently(state, llm_client)
        print("--- [DEBUG] _initial_plan_wrapper 완료, 결과 반환 ---")
        return result

    print(f"--- [DEBUG] _initial_plan_wrapper 타입: {type(_initial_plan_wrapper)}")
    workflow.add_node("initial_plan", _initial_plan_wrapper)
    print("--- [DEBUG] initial_plan 노드 추가 완료 ---")
    print("--- [DEBUG] 나머지 노드 추가 시작 ---")
    workflow.add_node("router", router)
    workflow.add_node("adjust_exercise_plan", adjust_exercise_plan)
    workflow.add_node("adjust_diet_plan", adjust_diet_plan)
    workflow.add_node("adjust_intensity", adjust_intensity)
    workflow.add_node("qa_general", qa_general)
    workflow.add_node("finalize_plan", finalize_plan)
    print("--- [DEBUG] 모든 노드 추가 완료 ---")

    def decide_entry_point(state: PlanState) -> str:
        """진입점 결정 로직: 첫 실행(메시지 없음)이면 initial_plan, 아니면 router"""
        print("\n" + "="*80)
        print("--- [DEBUG] decide_entry_point 호출됨 ---")
        messages = state.get("messages", [])
        category = state.get("feedback_category")
        print(f"--- [DEBUG] state keys: {list(state.keys())}")
        print(f"--- [DEBUG] messages: {len(messages) if messages else 0}개")
        print(f"--- [DEBUG] category: {category}")

        # 메시지가 있거나 피드백 카테고리가 있으면 이미 진행 중인 대화 -> 라우터
        if (messages and len(messages) > 0) or category:
            print(f"--- [DEBUG] 진입점 결정: Router (msgs={len(messages)}, cat={category}) ---")
            print("="*80 + "\n")
            return "router"

        # 아무 기록도 없으면 초기 계획 생성
        print("--- [DEBUG] 진입점 결정: Initial Plan (첫 실행) ---")
        print("="*80 + "\n")
        return "initial_plan"

    print("--- [DEBUG] 조건부 진입점 설정 시작 ---")
    workflow.set_conditional_entry_point(
        decide_entry_point,
        {
            "router": "router",
            "initial_plan": "initial_plan"
        }
    )
    print("--- [DEBUG] 조건부 진입점 설정 완료 ---")

    # 초기 계획 생성 후 종료 (사용자 피드백 대기)
    print("--- [DEBUG] 엣지 추가 시작 ---")
    workflow.add_edge("initial_plan", END)

    # 각 피드백 조정 후 종료 (Request/Response 모델이므로 턴 종료)
    workflow.add_edge("adjust_exercise_plan", END)
    workflow.add_edge("adjust_diet_plan", END)
    workflow.add_edge("adjust_intensity", END)
    workflow.add_edge("qa_general", END)

    # 라우터에서 조건에 따라 분기
    feedback_routing_map = {
        "adjust_exercise_plan": "adjust_exercise_plan",
        "adjust_diet_plan": "adjust_diet_plan",
        "adjust_intensity": "adjust_intensity",
        "qa_general": "qa_general",
        "finalize_plan": "finalize_plan",
        END: END
    }
    workflow.add_conditional_edges("router", route_feedback, feedback_routing_map)

    # 최종 노드에서 그래프 종료
    workflow.add_edge("finalize_plan", END)
    print("--- [DEBUG] 모든 엣지 추가 완료 ---")

    print("--- [DEBUG] MemorySaver 생성 ---")
    memory = MemorySaver()

    # interrupt_before 제거 (라우터 진입 시 멈추지 않고 즉시 실행)
    print("--- [DEBUG] workflow.compile() 호출 시작 ---")
    compiled_graph = workflow.compile(checkpointer=memory)
    print("--- [DEBUG] workflow.compile() 완료 ---")
    print("="*80 + "\n")
    return compiled_graph
