from typing import TypedDict, Annotated
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


# --- 3. 그래프 생성 ---
def create_weekly_plan_agent(llm_client):
    """주간 계획 생성 에이전트 그래프 생성"""
    
    # --- 2. 노드 정의 ---
    def generate_initial_plan(state: PlanState) -> dict:
        """Node 1: 주간 계획 초안 생성"""
        print("--- LLM2: 주간 계획 생성 ---")
        plan_input = state["plan_input"]
        
        # InBody 데이터 모델 변환
        measurements = InBodyMeasurements(**plan_input.measurements)

        # 프롬프트 생성
        system_prompt, user_prompt = create_weekly_plan_prompt(
            goal_input=plan_input,
            measurements=measurements
        )

        # LLM 호출
        response = llm_client.generate_chat(system_prompt, user_prompt)

        # 결과 반환 (대화 기록에 추가)
        return {"messages": [("human", user_prompt), ("ai", response)]}

    def _generate_qa_response(state: PlanState, category_name: str, system_prompt: str) -> dict:
        """공통 Q&A 답변 생성 로직"""
        print(f"--- LLM2: 주간 계획 Q&A ({category_name}) ---")

        # 대화 기록 변환
        history = []
        for msg in state["messages"]:
            role = "user" if msg.type == "human" else "assistant"
            history.append((role, msg.content))

        # LLM 호출 (히스토리 포함)
        response = llm_client.generate_chat_with_history(
            system_prompt=system_prompt,
            messages=history
        )

        return {"messages": [("ai", response)]}

    def qa_exercise_guide(state: PlanState) -> dict:
        """Node 2-1: 운동 방법 가이드"""
        system_prompt = """당신은 전문 트레이너입니다. 
        사용자가 특정 운동 동작에 대해 질문했습니다. 
        해당 운동의 올바른 자세, 자극 부위, 호흡법, 그리고 주의사항을 초보자도 이해하기 쉽게 구체적으로 설명해주세요."""
        return _generate_qa_response(state, "운동 가이드", system_prompt)

    def qa_plan_adjustment(state: PlanState) -> dict:
        """Node 2-2: 운동 플랜 조정"""
        system_prompt = """당신은 전문 트레이너입니다. 
        사용자가 운동 플랜(일정, 종목, 분할 방식 등)의 조정을 요청했습니다. 
        사용자가 요청 사항을 반영하여 수정된 구체적인 운동 계획을 제시해주세요. 
        수정된 이유도 함께 설명하면 좋습니다."""
        return _generate_qa_response(state, "플랜 조정", system_prompt)

    def qa_diet_adjustment(state: PlanState) -> dict:
        """Node 2-3: 식단 조정"""
        system_prompt = """당신은 영양 전문가입니다. 
        사용자가 식단 계획의 조정을 요청했습니다. 
        사용자의 기호, 알레르기, 또는 상황(외식, 편의점 등)을 고려하여 대체 식단이나 수정된 메뉴를 제안해주세요. 
        칼로리와 영양 밸런스를 고려하여 조언해주세요."""
        return _generate_qa_response(state, "식단 조정", system_prompt)

    def qa_intensity_adjustment(state: PlanState) -> dict:
        """Node 2-4: 강도 조정"""
        system_prompt = """당신은 전문 트레이너입니다. 
        사용자가 운동 강도(무게, 횟수, 세트, 휴식 시간 등)의 조정을 요청했습니다. 
        사용자가 느끼는 난이도에 맞춰 강도를 높이거나 낮추는 구체적인 가이드를 제공해주세요. 
        부상 방지를 위한 조언도 포함해주세요."""
        return _generate_qa_response(state, "강도 조정", system_prompt)

    def qa_general(state: PlanState) -> dict:
        """Node 2-5: 일반 Q&A"""
        system_prompt = """당신은 사용자의 주간 운동 및 식단 계획을 담당하는 퍼스널 트레이너입니다.
        사용자가 생성된 계획에 대해 질문하거나 수정을 요청하면, 전문적이고 친절하게 답변해주세요.
        이전 대화 맥락(사용자의 신체 정보, 목표, 생성된 계획)을 모두 고려해야 합니다."""
        return _generate_qa_response(state, "일반", system_prompt)

    def finalize_plan(state: PlanState) -> dict:
        """Node 3: 계획 확정 및 저장"""
        print("--- LLM2: 계획 확정 ---")
        return {"messages": [("ai", "네, 현재 계획으로 확정하여 저장하겠습니다. 일주일 동안 화이팅하세요!")]}

    def route_qa(state: PlanState) -> str:
        """사용자 질문 카테고리에 따른 라우팅"""
        user_question = state["messages"][-1].content.strip()

        if user_question.startswith("1"):
            return "qa_exercise_guide"
        elif user_question.startswith("2"):
            return "qa_plan_adjustment"
        elif user_question.startswith("3"):
            return "qa_diet_adjustment"
        elif user_question.startswith("4"):
            return "qa_intensity_adjustment"
        elif user_question.startswith("5"):
            return "finalize_plan"
        else:
            return "qa_general"

    workflow = StateGraph(PlanState)

    workflow.add_node("initial_plan", generate_initial_plan)
    
    # Q&A 노드 추가
    workflow.add_node("qa_exercise_guide", qa_exercise_guide)
    workflow.add_node("qa_plan_adjustment", qa_plan_adjustment)
    workflow.add_node("qa_diet_adjustment", qa_diet_adjustment)
    workflow.add_node("qa_intensity_adjustment", qa_intensity_adjustment)
    workflow.add_node("qa_general", qa_general)
    workflow.add_node("finalize_plan", finalize_plan)

    workflow.set_entry_point("initial_plan")

    # 라우팅 맵 정의
    qa_routing_map = {
        "qa_exercise_guide": "qa_exercise_guide",
        "qa_plan_adjustment": "qa_plan_adjustment",
        "qa_diet_adjustment": "qa_diet_adjustment",
        "qa_intensity_adjustment": "qa_intensity_adjustment",
        "qa_general": "qa_general",
        "finalize_plan": "finalize_plan",
        END: END
    }

    # 1. 초기 계획 생성 후 라우팅
    workflow.add_conditional_edges(
        "initial_plan",
        route_qa,
        qa_routing_map
    )

    # 2. 각 Q&A 노드 실행 후 다시 라우팅 (대화 루프)
    for node_name in ["qa_exercise_guide", "qa_plan_adjustment", "qa_diet_adjustment", "qa_intensity_adjustment", "qa_general"]:
        workflow.add_conditional_edges(
            node_name,
            route_qa,
            qa_routing_map
        )

    # 확정 후 종료
    workflow.add_edge("finalize_plan", END)

    memory = MemorySaver()
    
    # 각 단계 후 중단하여 사용자 피드백 대기
    return workflow.compile(
        checkpointer=memory, 
        interrupt_after=[
            "initial_plan", 
            "qa_exercise_guide", 
            "qa_plan_adjustment", 
            "qa_diet_adjustment", 
            "qa_intensity_adjustment", 
            "qa_general"
        ]
    )