from typing import TypedDict, Annotated, Optional
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from dotenv import load_dotenv

load_dotenv()

from services.llm.llm_clients import create_llm_client
from schemas.llm import GoalPlanInput
from schemas.inbody import InBodyData as InBodyMeasurements
from services.llm.prompt_generator import create_weekly_plan_prompt


# --- 1. 상태 정의 ---
class PlanState(TypedDict):
    """LLM2 (주간 계획 / Q&A) 에이전트의 상태"""
    plan_input: GoalPlanInput
    messages: Annotated[list, add_messages]
    # 사용자 피드백을 명시적으로 관리하기 위한 필드 추가
    feedback_category: Optional[str]
    feedback_text: Optional[str]


# --- 3. 그래프 생성 ---
def create_weekly_plan_agent(llm_client):
    """주간 계획 생성 및 수정을 위한 에이전트 그래프 생성"""
    
    # --- 2. 노드 정의 ---
    def generate_initial_plan(state: PlanState) -> dict:
        """Node 1: 주간 계획 초안 생성"""
        print("--- LLM2: 주간 계획 생성 ---")
        plan_input = state["plan_input"]
        
        measurements = InBodyMeasurements(**plan_input.measurements)

        system_prompt, user_prompt = create_weekly_plan_prompt(
            goal_input=plan_input,
            measurements=measurements
        )

        response = llm_client.generate_chat(system_prompt, user_prompt)
        
        return {"messages": [("human", user_prompt), ("ai", response)]}

    def _generate_feedback_response(state: PlanState, category_name: str, system_prompt: str) -> dict:
        """공통 피드백 기반 답변 생성 로직"""
        print(f"--- LLM2: 주간 계획 피드백 반영 ({category_name}) ---")

        history = []
        for msg in state["messages"]:
            role = "user" if msg.type == "human" else "assistant"
            history.append((role, msg.content))
        
        feedback_text = state.get("feedback_text", "피드백 내용이 없습니다.")
        history.append(("user", feedback_text))
        
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
        category = state.get("feedback_category")

        if not category:
            print("--- 라우팅: 피드백 대기 (중단) ---")
            return END

        print(f"--- 라우팅: {category} ---")
        if category == "운동 플랜 조정":
            return "adjust_exercise_plan"
        elif category == "식단 조정":
            return "adjust_diet_plan"
        elif category == "강도 조정":
            return "adjust_intensity"
        elif category == "최종 플랜으로 저장":
            return "finalize_plan"
        else:
            return "qa_general"

    workflow = StateGraph(PlanState)

    workflow.add_node("initial_plan", generate_initial_plan)
    workflow.add_node("router", router)
    workflow.add_node("adjust_exercise_plan", adjust_exercise_plan)
    workflow.add_node("adjust_diet_plan", adjust_diet_plan)
    workflow.add_node("adjust_intensity", adjust_intensity)
    workflow.add_node("qa_general", qa_general)
    workflow.add_node("finalize_plan", finalize_plan)

    workflow.set_entry_point("initial_plan")
    
    # 초기 계획 생성 후 라우터로 이동
    workflow.add_edge("initial_plan", "router")
    
    # 각 피드백 조정 후 다시 라우터로 이동하여 루프 형성
    workflow.add_edge("adjust_exercise_plan", "router")
    workflow.add_edge("adjust_diet_plan", "router")
    workflow.add_edge("adjust_intensity", "router")
    workflow.add_edge("qa_general", "router")

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
    
    memory = MemorySaver()
    
    # compile() 호출 시 checkpointer를 전달하면,
    # 라우터가 END를 반환할 때 자동으로 대화가 중단되고 상태가 저장됩니다.
    return workflow.compile(checkpointer=memory)