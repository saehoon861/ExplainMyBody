"""
Analysis Agent with RAG Support
- backend/services/llm/agent_graph.py 기반
- RAG 논문 검색 추가
- 기존 LangGraph 구조 유지
"""

from typing import TypedDict, Optional, Annotated, Dict, List
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from dotenv import load_dotenv

load_dotenv()

from llm_clients import create_llm_client, OpenAIClient
from schemas import StatusAnalysisInput
from prompt_generator_rag import (
    create_inbody_analysis_summary_prompt_with_rag,
    create_inbody_analysis_detail_prompt_with_rag
)
from schemas_inbody import InBodyData as InBodyMeasurements
from rag_retriever import SimpleRAGRetriever


# --- 1. 상태 정의 ---
class AnalysisStateRAG(TypedDict):
    """RAG가 추가된 건강 상태 분석 에이전트의 상태"""
    # 입력: 건강 기록 데이터
    analysis_input: StatusAnalysisInput
    # 대화 기록 (HumanMessage, AIMessage의 리스트)
    messages: Annotated[list, add_messages]
    # 생성된 임베딩 벡터
    embedding: Optional[Dict[str, List[float]]]
    # RAG 검색 결과 (논문 컨텍스트)
    rag_context: Optional[str]


# --- 3. 그래프 생성 ---
def create_analysis_agent_with_rag(llm_client, use_rag: bool = True):
    """
    RAG가 추가된 건강 분석 및 휴먼 피드백 Q&A 에이전트 그래프를 생성하고 컴파일합니다.

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
            use_rag = False

    # --- 2. 노드(그래프의 각 단계) 정의 ---
    def generate_initial_analysis(state: AnalysisStateRAG) -> dict:
        """Node 1: RAG 검색 + 최초 분석 결과 생성 및 임베딩 (2단계)"""
        print("--- LLM1 (RAG): 최초 분석 생성 (2단계 프롬프트) ---")
        analysis_input = state["analysis_input"]

        # 1. InBodyMeasurements 모델로 변환
        measurements = InBodyMeasurements(**analysis_input.measurements)

        # 2. RAG 검색 (논문 검색)
        rag_context = ""
        if use_rag and rag_retriever:
            try:
                # 검색 쿼리 생성 (사용자의 체성분 특징 기반)
                query = _generate_rag_query(measurements)

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

        # 3-1. 프롬프트 1: 5줄 요약 생성
        print("\n  [Step 1] 5줄 요약 생성...")
        system_prompt_1, user_prompt_1 = create_inbody_analysis_summary_prompt_with_rag(
            measurements,
            body_type1=analysis_input.body_type1,
            body_type2=analysis_input.body_type2,
            rag_context=rag_context
        )
        summary_response = llm_client.generate_chat(system_prompt_1, user_prompt_1)
        print(f"  ✓ 요약 완료 ({len(summary_response)} 문자)")

        # 3-2. 프롬프트 2: 세부 리포트 생성
        print("\n  [Step 2] 세부 리포트 생성...")
        system_prompt_2, user_prompt_2 = create_inbody_analysis_detail_prompt_with_rag(
            measurements,
            body_type1=analysis_input.body_type1,
            body_type2=analysis_input.body_type2,
            prev_inbody="",  # TODO: 이전 기록 연동 시 추가
            health_notes="",  # TODO: 건강 특이사항 연동 시 추가
            rag_context=rag_context
        )
        detail_response = llm_client.generate_chat(system_prompt_2, user_prompt_2)
        print(f"  ✓ 세부 리포트 완료 ({len(detail_response)} 문자)")

        # 3-3. 두 응답 결합
        combined_response = f"{summary_response}\n\n---\n\n{detail_response}"

        # 4. 임베딩 생성 (결합된 응답 기준)
        embedding_1536 = None
        embedding_1024 = None

        try:
            openai_client = OpenAIClient()
            embedding_1536 = openai_client.create_embedding(text=combined_response)
            print(f"  ✓ 임베딩 생성 완료 (1536D)")
        except Exception as e:
            print(f"  ⚠️  임베딩 생성 실패: {e}")

        final_embedding = {
            "embedding_1536": embedding_1536,
            "embedding_1024": embedding_1024,
        }

        return {
            "messages": [("human", user_prompt_1 + "\n\n" + user_prompt_2), ("ai", combined_response)],
            "embedding": final_embedding,
            "rag_context": rag_context
        }

    def _generate_rag_query(measurements: InBodyMeasurements) -> str:
        """
        InBody 측정값에서 RAG 검색 쿼리 생성

        기존 prompt_generator.py 방식과 동일하게 중첩 구조 접근
        """
        query_parts = []

        # 성별, 나이
        성별 = measurements.기본정보.성별
        연령 = measurements.기본정보.연령
        query_parts.append(f"{성별} {연령}세")

        # BMI 상태
        BMI = measurements.비만분석.BMI
        if BMI < 18.5:
            query_parts.append("저체중 개선")
        elif BMI >= 25:
            query_parts.append("과체중 비만 관리")

        # 체지방률
        체지방률 = measurements.비만분석.체지방률
        if 성별 == "남성" and 체지방률 > 25:
            query_parts.append("체지방 감소")
        elif 성별 == "여성" and 체지방률 > 30:
            query_parts.append("체지방 감소")

        # 근육조절
        if measurements.체중관리.근육조절 and measurements.체중관리.근육조절 > 0:
            query_parts.append("근육량 증가 근성장")

        # 내장지방
        if measurements.비만분석.내장지방레벨 and measurements.비만분석.내장지방레벨 > 10:
            query_parts.append("내장지방 감소")

        # 기본 쿼리
        if not query_parts:
            query_parts.append("체성분 개선 건강 관리")

        return " ".join(query_parts)

    def _generate_qa_response(state: AnalysisStateRAG, category_name: str, system_prompt: str) -> dict:
        """공통 Q&A 답변 생성 로직 (기존과 동일)"""
        print(f"--- LLM1 (RAG): Q&A 답변 생성 ({category_name}) ---")

        history = []
        for msg in state["messages"]:
            role = "user" if msg.type == "human" else "assistant"
            history.append((role, msg.content))

        response = llm_client.generate_chat_with_history(
            system_prompt=system_prompt,
            messages=history
        )

        return {"messages": [("ai", response)]}

    # Q&A 노드들 (기존과 동일)
    def qa_strength_weakness(state: AnalysisStateRAG) -> dict:
        """Node 2-1: 강점/약점 Q&A"""
        system_prompt = """당신은 데이터 기반의 체성분 분석 전문가입니다.
        사용자가 자신의 신체 강점과 약점에 대해 질문했습니다.
        이전 대화에서 제공된 인바디 데이터와 최초 분석 결과를 바탕으로, 다음 항목에 대해 구체적인 수치를 들어 설명해주세요.
        - **강점**: 표준 범위 이상이거나 긍정적인 지표
        - **약점**: 개선이 필요한 지표
        - **종합 평가**: 현재 신체의 가장 큰 특징을 요약해주세요."""
        return _generate_qa_response(state, "강점/약점", system_prompt)

    def qa_health_status(state: AnalysisStateRAG) -> dict:
        """Node 2-2: 건강 상태 Q&A"""
        system_prompt = """당신은 예방 의학 관점에서 조언하는 건강 컨설턴트입니다.
        사용자가 현재 자신의 전반적인 건강 상태에 대해 질문했습니다.
        이전 대화 내용을 바탕으로, 건강 관점에서 긍정적인 부분과 잠재적인 위험 요소를 나누어 설명해주세요."""
        return _generate_qa_response(state, "건강 상태", system_prompt)

    def qa_impact(state: AnalysisStateRAG) -> dict:
        """Node 2-3: 일상/운동 영향 Q&A"""
        system_prompt = """당신은 운동생리학자이자 라이프스타일 코치입니다.
        사용자가 현재 신체 상태가 일상과 운동 수행능력에 미치는 영향에 대해 질문했습니다.
        이전 대화 내용을 바탕으로, 현재 체성분 상태가 어떤 결과로 이어질 수 있는지 구체적인 예시를 들어 설명해주세요."""
        return _generate_qa_response(state, "일상/운동 영향", system_prompt)

    def qa_priority(state: AnalysisStateRAG) -> dict:
        """Node 2-4: 개선 우선순위 Q&A"""
        system_prompt = """당신은 동기부여가 뛰어난 현실적인 퍼스널 트레이너입니다.
        사용자가 가장 먼저 개선해야 할 우선순위에 대해 질문했습니다.
        이전 대화 내용을 종합하여, 가장 시급하고 효과가 큰 '액션 아이템'을 3가지 우선순위로 제시해주세요."""
        return _generate_qa_response(state, "개선 우선순위", system_prompt)

    def qa_general(state: AnalysisStateRAG) -> dict:
        """Node 2-5: 일반 Q&A"""
        system_prompt = """당신은 전문 피트니스 코치입니다.
        이전 대화의 맥락을 유지하면서 사용자의 질문에 답변해주세요."""
        return _generate_qa_response(state, "일반", system_prompt)

    def finalize_analysis(state: AnalysisStateRAG) -> dict:
        """Node 3: 분석 확정 및 저장"""
        print("--- LLM1 (RAG): 분석 확정 ---")
        return {"messages": [("ai", "네, 분석 결과를 확정하고 저장하겠습니다. 추가적인 질문이 있다면 언제든 다시 찾아주세요.")]}

    def route_qa(state: AnalysisStateRAG) -> str:
        """사용자 질문에 따라 적절한 Q&A 노드로 라우팅"""
        user_question = state["messages"][-1].content.strip()

        if user_question.startswith("1"):
            return "qa_strength_weakness"
        elif user_question.startswith("2"):
            return "qa_health_status"
        elif user_question.startswith("3"):
            return "qa_impact"
        elif user_question.startswith("4"):
            return "qa_priority"
        elif user_question.startswith("6"):
            return "finalize_analysis"
        else:
            return "qa_general"

    # 라우팅 맵 정의
    routing_map = {
        "qa_strength_weakness": "qa_strength_weakness",
        "qa_health_status": "qa_health_status",
        "qa_impact": "qa_impact",
        "qa_priority": "qa_priority",
        "qa_general": "qa_general",
        "finalize_analysis": "finalize_analysis",
    }

    workflow = StateGraph(AnalysisStateRAG)

    # 노드 추가
    workflow.add_node("initial_analysis", generate_initial_analysis)
    workflow.add_node("qa_strength_weakness", qa_strength_weakness)
    workflow.add_node("qa_health_status", qa_health_status)
    workflow.add_node("qa_impact", qa_impact)
    workflow.add_node("qa_priority", qa_priority)
    workflow.add_node("qa_general", qa_general)
    workflow.add_node("finalize_analysis", finalize_analysis)

    # 진입점 설정
    workflow.set_entry_point("initial_analysis")

    # 엣지 연결
    workflow.add_conditional_edges(
        "initial_analysis",
        route_qa,
        routing_map
    )

    qa_nodes = ["qa_strength_weakness", "qa_health_status", "qa_impact", "qa_priority", "qa_general"]
    for node in qa_nodes:
        workflow.add_conditional_edges(node, route_qa, routing_map)

    workflow.add_edge("finalize_analysis", END)

    # 체크포인터 설정
    memory = MemorySaver()

    # 휴먼 피드백을 위해 각 단계 후 중단
    agent = workflow.compile(checkpointer=memory, interrupt_after=["initial_analysis"] + qa_nodes)

    return agent
