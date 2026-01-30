from typing import TypedDict, Optional, Annotated, Dict
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from dotenv import load_dotenv

load_dotenv()

from services.llm.llm_clients import create_llm_client, OpenAIClient
from schemas.llm import StatusAnalysisInput, GoalPlanInput
from .prompt_generator import create_inbody_analysis_prompt
from schemas.inbody import InBodyData as InBodyMeasurements

# LLM 클라이언트 인스턴스 (실제로는 서비스에서 주입받는 것이 좋음)
llm_client = create_llm_client("gpt-4o-mini")


# --- 1. 상태 정의 ---
class AnalysisState(TypedDict):
    """LLM1 (건강 상태 분석 / Q&A) 에이전트의 상태"""
    # 입력: 건강 기록 데이터
    analysis_input: StatusAnalysisInput
    # 대화 기록 (HumanMessage, AIMessage의 리스트)
    # add_messages는 새로운 메시지를 기존 리스트에 추가하는 역할을 합니다.
    messages: Annotated[list, add_messages]
    # 생성된 임베딩 벡터
    embedding: Optional[Dict[str, list]]
    
    
# --- 2. 노드(그래프의 각 단계) 정의 ---
def generate_initial_analysis(state: AnalysisState) -> dict:
    """Node 1: 최초 분석 결과 생성 및 임베딩"""
    print("--- LLM1: 최초 분석 생성 ---")
    analysis_input = state["analysis_input"]

    # 1. InBodyMeasurements 모델로 변환 (prompt_generator가 요구하는 타입)
    measurements = InBodyMeasurements(**analysis_input.measurements)

    # 2. 프롬프트 생성 및 LLM 호출
    system_prompt, user_prompt = create_inbody_analysis_prompt(
        measurements,
        body_type1=analysis_input.body_type1,
        body_type2=analysis_input.body_type2
    )
    response = llm_client.generate_chat(system_prompt, user_prompt)
    
    # --- 3. 임베딩 생성 (embedder.py 로직 반영) ---
    # 이 단계에서는 벡터만 생성합니다.
    # 실제 DB 저장은 서비스 계층에서 이 노드의 결과(response, embedding)를 받아 처리합니다.
    print("\n임베딩 생성 중...")
    embedding_1536 = None
    embedding_1024 = None

    # 3-1. OpenAI 임베딩 생성 (1536차원)
    try:
        openai_client = OpenAIClient()
        embedding_1536 = openai_client.create_embedding(text=response)
        print(f"OpenAI 임베딩 생성 완료 (차원: {len(embedding_1536)})")
    except Exception as e:
        print(f"OpenAI 임베딩 생성 실패: {e}")

    final_embedding = {
        "embedding_1536": embedding_1536,
        "embedding_1024": embedding_1024,
    }

    # AI의 첫 답변과 생성된 임베딩을 상태에 추가
    # 서비스 계층에서는 이 응답(response)에 덧붙여 사용자에게 선택지를 보여줍니다.
    # 중요: Q&A 때 AI가 데이터를 알 수 있도록 'user_prompt(인바디 데이터)'도 대화 기록에 추가합니다.
    return {
        "messages": [("human", user_prompt), ("ai", response)],
        "embedding": final_embedding
    }

def _generate_qa_response(state: AnalysisState, category_name: str, system_prompt: str) -> dict:
    """공통 Q&A 답변 생성 로직"""
    print(f"--- LLM1: Q&A 답변 생성 ({category_name}) ---")

    # 사용자의 마지막 질문
    user_question = state["messages"][-1].content
    
    # LangGraph 메시지 객체를 LLM 클라이언트가 이해하는 튜플 리스트로 변환
    # LangChain Message.type: 'human' -> 'user', 'ai' -> 'assistant'
    history = []
    for msg in state["messages"]:
        role = "user" if msg.type == "human" else "assistant"
        history.append((role, msg.content))

    # 실제 LLM 호출 (대화 기록 포함)
    response = llm_client.generate_chat_with_history(
        system_prompt=system_prompt, 
        messages=history
    )

    return {"messages": [("ai", response)]}


def qa_strength_weakness(state: AnalysisState) -> dict:
    """Node 2-1: 강점/약점 Q&A"""
    system_prompt = """당신은 데이터 기반의 체성분 분석 전문가입니다.
    사용자가 자신의 신체 강점과 약점에 대해 질문했습니다.
    이전 대화에서 제공된 인바디 데이터와 최초 분석 결과를 바탕으로, 다음 항목에 대해 구체적인 수치를 들어 설명해주세요.
    - **강점**: 표준 범위 이상이거나 긍정적인 지표 (예: 높은 골격근량, 적정 체수분 등)
    - **약점**: 개선이 필요한 지표 (예: 높은 체지방률, 부위별 불균형, 낮은 기초대사량 등)
    - **종합 평가**: 현재 신체의 가장 큰 특징을 요약해주세요."""
    return _generate_qa_response(state, "강점/약점", system_prompt)

def qa_health_status(state: AnalysisState) -> dict:
    """Node 2-2: 건강 상태 Q&A"""
    system_prompt = """당신은 예방 의학 관점에서 조언하는 건강 컨설턴트입니다.
    사용자가 현재 자신의 전반적인 건강 상태에 대해 질문했습니다.
    이전 대화 내용을 바탕으로, 건강 관점에서 긍정적인 부분과 잠재적인 위험 요소를 나누어 설명해주세요.
    - **긍정적 신호**: 정상 범위에 있는 BMI, 근육량, 혈압 관련 지표 등
    - **주의/경고 신호**: 복부지방률, 내장지방레벨 등 건강 위험도와 직결되는 지표를 중심으로 설명하고, 어떤 질병의 위험을 높일 수 있는지 알려주세요. (의학적 진단이 아님을 명시)
    - **결론**: 현재 상태가 '매우 건강', '건강한 편', '주의 필요', '관리 필요' 중 어디에 가까운지 종합적으로 판단해주세요."""
    return _generate_qa_response(state, "건강 상태", system_prompt)

def qa_impact(state: AnalysisState) -> dict:
    """Node 2-3: 일상/운동 영향 Q&A"""
    system_prompt = """당신은 운동생리학자이자 라이프스타일 코치입니다.
    사용자가 현재 신체 상태가 일상과 운동 수행능력에 미치는 영향에 대해 질문했습니다.
    이전 대화 내용을 바탕으로, 현재 체성분 상태가 어떤 결과로 이어질 수 있는지 구체적인 예시를 들어 설명해주세요.
    - **운동 수행능력**: 현재 근육량과 체지방량이 근력, 지구력, 순발력 등에 미치는 영향 (예: '하체 근육이 발달하여 스쿼트나 등산에 유리하지만, 체중 대비 상체 근력이 부족하여 턱걸이 같은 운동은 어려울 수 있습니다.')
    - **일상 생활**: 기초대사량, 체력 수준이 일상적인 피로도, 활동성, 자세 유지 등에 미치는 영향 (예: '기초대사량이 낮아 쉽게 피로감을 느낄 수 있으며, 코어 근육 부족으로 오래 앉아있을 때 허리 통증을 유발할 수 있습니다.')"""
    return _generate_qa_response(state, "일상/운동 영향", system_prompt)

def qa_priority(state: AnalysisState) -> dict:
    """Node 2-4: 개선 우선순위 Q&A"""
    system_prompt = """당신은 동기부여가 뛰어난 현실적인 퍼스널 트레이너입니다.
    사용자가 가장 먼저 개선해야 할 우선순위에 대해 질문했습니다.
    이전 대화 내용을 종합하여, 가장 시급하고 효과가 큰 '액션 아이템'을 3가지 우선순위로 제시해주세요.
    - **1순위 (가장 시급)**: 건강 위험을 낮추거나, 가장 큰 불균형을 해소하기 위한 것 (예: 내장지방 감소를 위한 유산소 운동 시작)
    - **2순위 (체감 효과가 큰 것)**: 단기간에 변화를 느끼거나, 다른 운동 능력 향상에 기반이 되는 것 (예: 코어 근력 강화)
    - **3순위 (장기적 관점)**: 꾸준히 개선해나가야 할 생활 습관이나 보조적인 운동 (예: 식단 기록 시작, 수면 시간 확보)
    각 항목에 대해 '왜' 그것이 중요한지 이유를 명확히 설명해주세요."""
    return _generate_qa_response(state, "개선 우선순위", system_prompt)

def qa_general(state: AnalysisState) -> dict:
    """Node 2-5: 일반 Q&A"""
    system_prompt = """당신은 전문 피트니스 코치입니다. 
    이전 대화의 맥락을 유지하면서 사용자의 질문에 답변해주세요."""
    return _generate_qa_response(state, "일반", system_prompt)


def route_qa(state: AnalysisState) -> str:
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
    else:
        # 사용자가 카테고리 선택이 아닌 일반 질문을 한 경우
        # 또는 이전 카테고리 대화에 이어서 질문하는 경우,
        # 마지막 AI 답변의 컨텍스트를 보고 판단할 수도 있지만 여기서는 일반으로 보냅니다.
        return "qa_general"


# --- 3. 그래프 생성 ---
def create_analysis_agent():
    """
    건강 분석 및 휴먼 피드백 Q&A 에이전트 그래프를 생성하고 컴파일합니다.
    
    - `interrupt_after`를 사용하여 각 AI 응답 후에 멈추고 사용자 입력을 기다립니다.
    - 사용자가 '5. 괜찮습니다'를 선택하는 것은 서비스 계층에서 처리하며,
      더 이상 그래프를 호출하지 않는 방식으로 구현됩니다.
    """
    workflow = StateGraph(AnalysisState)
    
    # 노드 추가
    workflow.add_node("initial_analysis", generate_initial_analysis)
    workflow.add_node("qa_strength_weakness", qa_strength_weakness)
    workflow.add_node("qa_health_status", qa_health_status)
    workflow.add_node("qa_impact", qa_impact)
    workflow.add_node("qa_priority", qa_priority)
    workflow.add_node("qa_general", qa_general)
    
    # 진입점 설정
    workflow.set_entry_point("initial_analysis")
    
    # 엣지 연결
    # 최초 분석 후에는 사용자의 질문을 받아 라우팅합니다.
    workflow.add_conditional_edges(
        "initial_analysis",
        route_qa,
        {
            "qa_strength_weakness": "qa_strength_weakness",
            "qa_health_status": "qa_health_status",
            "qa_impact": "qa_impact",
            "qa_priority": "qa_priority",
            "qa_general": "qa_general",
        }
    )
    
    # 각 Q&A 노드는 다시 라우터를 거쳐 다음 질문을 처리합니다. (루프)
    workflow.add_conditional_edges("qa_strength_weakness", route_qa, {
        "qa_strength_weakness": "qa_strength_weakness", "qa_health_status": "qa_health_status", "qa_impact": "qa_impact", "qa_priority": "qa_priority", "qa_general": "qa_general"
    })
    workflow.add_conditional_edges("qa_health_status", route_qa, {
        "qa_strength_weakness": "qa_strength_weakness", "qa_health_status": "qa_health_status", "qa_impact": "qa_impact", "qa_priority": "qa_priority", "qa_general": "qa_general"
    })
    workflow.add_conditional_edges("qa_impact", route_qa, {
        "qa_strength_weakness": "qa_strength_weakness", "qa_health_status": "qa_health_status", "qa_impact": "qa_impact", "qa_priority": "qa_priority", "qa_general": "qa_general"
    })
    workflow.add_conditional_edges("qa_priority", route_qa, {
        "qa_strength_weakness": "qa_strength_weakness", "qa_health_status": "qa_health_status", "qa_impact": "qa_impact", "qa_priority": "qa_priority", "qa_general": "qa_general"
    })
    workflow.add_conditional_edges("qa_general", route_qa, {
        "qa_strength_weakness": "qa_strength_weakness", "qa_health_status": "qa_health_status", "qa_impact": "qa_impact", "qa_priority": "qa_priority", "qa_general": "qa_general"
    })

    # 체크포인터 설정 (인메모리 저장소)
    # 실제 운영 환경에서는 PostgresSaver 등을 사용하여 DB에 저장하는 것이 좋습니다.
    memory = MemorySaver()

    # 휴먼 피드백을 위해, LLM이 답변을 생성한 후에는 항상 멈춥니다.
    # 서비스(API)는 이 멈춘 지점에서 사용자 입력을 받아 다음 단계로 진행합니다.
    agent = workflow.compile(checkpointer=memory, interrupt_after=["initial_analysis", "qa_strength_weakness", "qa_health_status", "qa_impact", "qa_priority", "qa_general"])
    
    return agent
    
