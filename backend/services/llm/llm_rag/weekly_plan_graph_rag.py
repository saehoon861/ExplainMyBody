"""
Weekly Plan Agent with RAG Support
- backend/services/llm/weekly_plan_graph.py 기반
- RAG 논문 검색 추가
- 기존 LangGraph 구조 유지
"""

from typing import TypedDict, Annotated, Optional
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from dotenv import load_dotenv

load_dotenv()

from services.llm.llm_clients import create_llm_client
from schemas.llm import GoalPlanInput
from schemas.inbody import InBodyData as InBodyMeasurements
from .prompt_generator_rag import create_weekly_plan_prompt_with_rag
from .rag_retriever import SimpleRAGRetriever


# --- 1. 상태 정의 ---
class PlanStateRAG(TypedDict):
    """RAG가 추가된 주간 계획 에이전트의 상태"""
    plan_input: GoalPlanInput
    messages: Annotated[list, add_messages]
    # RAG 검색 결과 (논문 컨텍스트)
    rag_context: Optional[str]


# --- 3. 그래프 생성 ---
def create_weekly_plan_agent_with_rag(llm_client, use_rag: bool = True):
    """
    RAG가 추가된 주간 계획 생성 에이전트 그래프 생성

    Args:
        llm_client: LLM 클라이언트
        use_rag: RAG 사용 여부 (기본: True)
    """

    # RAG Retriever 초기화
    rag_retriever = None
    if use_rag:
        try:
            rag_retriever = SimpleRAGRetriever()
        except Exception as e:
            print(f"RAG 초기화 실패: {e}")
            use_rag = False

    # --- 2. 노드 정의 ---
    def generate_initial_plan(state: PlanStateRAG) -> dict:
        """Node 1: RAG 검색 + 주간 계획 초안 생성"""
        print("--- LLM2 (RAG): 주간 계획 생성 ---")
        plan_input = state["plan_input"]

        # InBody 데이터 모델 변환
        measurements = InBodyMeasurements(**plan_input.measurements)

        # 1. RAG 검색 (논문 검색)
        rag_context = ""
        if use_rag and rag_retriever:
            try:
                # 검색 쿼리 생성 (사용자의 목표 기반)
                query = _generate_rag_query_from_goal(plan_input, measurements)

                # 논문 검색
                papers = rag_retriever.retrieve_relevant_papers(
                    query=query,
                    top_k=5,
                    lang="ko"
                )

                # 프롬프트 형식으로 변환
                if papers:
                    rag_context = rag_retriever.format_papers_for_prompt(papers)

            except Exception as e:
                print(f"RAG 검색 실패: {e}")
                rag_context = ""

        # 2. 프롬프트 생성 (RAG 컨텍스트 포함)
        system_prompt, user_prompt = create_weekly_plan_prompt_with_rag(
            goal_input=plan_input,
            measurements=measurements,
            rag_context=rag_context
        )

        # 3. LLM 호출
        response = llm_client.generate_chat(system_prompt, user_prompt)

        # 결과 반환 (대화 기록에 추가)
        return {
            "messages": [("human", user_prompt), ("ai", response)],
            "rag_context": rag_context
        }

        # 사용자 목표설정으로부터 RAG로 논문 검색하는 메소드. 선택사항
        # 혹은 추가할 goal 관련 규칙기반 항목이 있으면 더 적용 가능
    def _generate_rag_query_from_goal(
        plan_input: GoalPlanInput,
        measurements: InBodyMeasurements
    ) -> str:
        """
        사용자 목표 및 체성분에서 RAG 검색 쿼리 생성

        Args:
            plan_input: 사용자 목표 입력
            measurements: InBody 측정 데이터

        Returns:
            검색 쿼리 문자열
        """
        query_parts = []

        # 주요 목표
        if plan_input.main_goal:
            query_parts.append(plan_input.main_goal)

        # 선호 운동 종류
        if plan_input.preferred_exercise_types:
            query_parts.extend(plan_input.preferred_exercise_types)

        # 체성분 상태 기반 키워드 추가
        성별 = measurements.기본정보.성별
        체지방률 = measurements.비만분석.체지방률
        if (체지방률 > 25 and 성별 == "남성") or (체지방률 > 30 and 성별 == "여성"):
            query_parts.append("체지방 감소")

        # 근육조절 (선택 필드이므로 if 체크)
        if measurements.체중관리.근육조절 and measurements.체중관리.근육조절 > 0:
            query_parts.append("근육량 증가")

        # 기본 쿼리
        if not query_parts:
            query_parts.append("운동 계획 효과")

        return " ".join(query_parts)

    def _generate_qa_response(state: PlanStateRAG, category_name: str, system_prompt: str) -> dict:
        """공통 Q&A 답변 생성 로직 (기존과 동일)"""
        print(f"--- LLM2 (RAG): 주간 계획 Q&A ({category_name}) ---")

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

    # Q&A 노드들 (기존과 동일)
    def qa_exercise_guide(state: PlanStateRAG) -> dict:
        """Node 2-1: 운동 방법 가이드"""
        system_prompt = """당신은 전문 트레이너입니다.
        사용자가 특정 운동 동작에 대해 질문했습니다.
        해당 운동의 올바른 자세, 자극 부위, 호흡법, 그리고 주의사항을 초보자도 이해하기 쉽게 구체적으로 설명해주세요."""
        return _generate_qa_response(state, "운동 가이드", system_prompt)

    def qa_plan_adjustment(state: PlanStateRAG) -> dict:
        """Node 2-2: 운동 플랜 조정"""
        system_prompt = """당신은 전문 트레이너입니다.
        사용자가 운동 플랜(일정, 종목, 분할 방식 등)의 조정을 요청했습니다.
        사용자가 요청 사항을 반영하여 수정된 구체적인 운동 계획을 제시해주세요."""
        return _generate_qa_response(state, "플랜 조정", system_prompt)

    def qa_diet_adjustment(state: PlanStateRAG) -> dict:
        """Node 2-3: 식단 조정"""
        system_prompt = """당신은 영양 전문가입니다.
        사용자가 식단 계획의 조정을 요청했습니다.
        사용자의 기호, 알레르기, 또는 상황(외식, 편의점 등)을 고려하여 대체 식단이나 수정된 메뉴를 제안해주세요."""
        return _generate_qa_response(state, "식단 조정", system_prompt)

    def qa_intensity_adjustment(state: PlanStateRAG) -> dict:
        """Node 2-4: 강도 조정"""
        system_prompt = """당신은 전문 트레이너입니다.
        사용자가 운동 강도(무게, 횟수, 세트, 휴식 시간 등)의 조정을 요청했습니다.
        사용자가 느끼는 난이도에 맞춰 강도를 높이거나 낮추는 구체적인 가이드를 제공해주세요."""
        return _generate_qa_response(state, "강도 조정", system_prompt)

    def qa_general(state: PlanStateRAG) -> dict:
        """Node 2-5: 일반 Q&A"""
        system_prompt = """당신은 사용자의 주간 운동 및 식단 계획을 담당하는 퍼스널 트레이너입니다.
        사용자가 생성된 계획에 대해 질문하거나 수정을 요청하면, 전문적이고 친절하게 답변해주세요."""
        return _generate_qa_response(state, "일반", system_prompt)

    def finalize_plan(state: PlanStateRAG) -> dict:
        """Node 3: 계획 확정 및 저장"""
        print("--- LLM2 (RAG): 계획 확정 ---")
        return {"messages": [("ai", "네, 현재 계획으로 확정하여 저장하겠습니다. 일주일 동안 화이팅하세요!")]}

    def route_qa(state: PlanStateRAG) -> str:
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

    workflow = StateGraph(PlanStateRAG)

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
