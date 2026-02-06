from typing import TypedDict, Optional, Annotated, Dict, List
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from dotenv import load_dotenv

load_dotenv()

from services.llm.llm_clients import BaseLLMClient
from schemas.llm import StatusAnalysisInput
from .prompt_generator import create_inbody_analysis_prompt
from schemas.inbody import InBodyData as InBodyMeasurements


# --- Custom Reducer: 기존 값 유지 ---
def keep_existing(existing, new):
    """
    기존 값이 있으면 유지, 없으면 새 값 사용
    이렇게 하면 analysis_input이 첫 invoke()에서 설정되면 계속 유지됨
    """
    return existing if existing is not None else new


# --- 1. 상태 정의 ---
class AnalysisState(TypedDict):
    """LLM1 (건강 상태 분석 / Q&A) 에이전트의 상태"""
    # 입력: 건강 기록 데이터 (첫 설정 후 계속 유지)
    analysis_input: Annotated[Optional[StatusAnalysisInput], keep_existing]
    # 대화 기록 (HumanMessage, AIMessage의 리스트)
    # add_messages는 새로운 메시지를 기존 리스트에 추가하는 역할을 합니다.
    messages: Annotated[list, add_messages]
    # 생성된 임베딩 벡터 (첫 설정 후 계속 유지)
    embedding: Annotated[Optional[Dict[str, List[float]]], keep_existing]
    
    
# --- 3. 그래프 생성 ---
def create_analysis_agent(llm_client: BaseLLMClient):
    """
    건강 분석 및 휴먼 피드백 Q&A 에이전트 그래프를 생성하고 컴파일합니다.
    
    - `interrupt_after`를 사용하여 각 AI 응답 후에 멈추고 사용자 입력을 기다립니다.
    - 사용자가 '5. 괜찮습니다'를 선택하는 것은 서비스 계층에서 처리하며,
      더 이상 그래프를 호출하지 않는 방식으로 구현됩니다.
    """
    
    # --- 2. 노드(그래프의 각 단계) 정의 ---
    def generate_initial_analysis(state: AnalysisState) -> dict:
        """Node 1: 최초 분석 결과 생성 및 임베딩"""
        print("[DEBUG][initial_analysis] ===== NODE ENTER =====")
        print(f"[DEBUG][initial_analysis] state keys: {list(state.keys())}")
        print(f"[DEBUG][initial_analysis] messages count: {len(state.get('messages', []))}")
        if state.get("messages"):
            last_msg = state["messages"][-1]
            print(f"[DEBUG][initial_analysis] last message: type={last_msg.type}, content[:80]='{str(last_msg.content)[:80]}'")

        # 🔧 Resume 방지: 이미 AI 메시지가 있으면 이미 분석 완료 → skip
        if state.get("messages"):
            for msg in state["messages"]:
                if msg.type == "ai":
                    print("[DEBUG][initial_analysis] !! AI 메시지 이미 존재 → 이미 분석 완료, PASSTHROUGH")
                    return {}

        analysis_input = state.get("analysis_input")
        print(f"[DEBUG][initial_analysis] analysis_input present: {analysis_input is not None}")
        if not analysis_input:
            # 체크포인트 소실 후 재실행된 경우 — route_qa로 패스스루
            print("[DEBUG][initial_analysis] !! PASSTHROUGH — analysis_input 없음, route_qa로 진행")
            return {}

        print(f"[DEBUG][initial_analysis] user_id={analysis_input.user_id}, record_id={analysis_input.record_id}")

        # 1. InBodyMeasurements 모델로 변환 (prompt_generator가 요구하는 타입)
        measurements = InBodyMeasurements(**analysis_input.measurements)

        # 2. 프롬프트 생성 및 LLM 호출
        system_prompt, user_prompt = create_inbody_analysis_prompt(
            measurements,
            body_type1=analysis_input.body_type1,
            body_type2=analysis_input.body_type2
        )
        print(f"[DEBUG][initial_analysis] prompt ready, calling LLM...")
        response = llm_client.generate_chat(system_prompt, user_prompt)
        print(f"[DEBUG][initial_analysis] LLM response length: {len(response)}, preview: '{response[:100]}'")

        # --- 3. 임베딩 생성 (embedder.py 로직 반영) ---
        print("[DEBUG][initial_analysis] 임베딩 생성 중...")
        embedding_1536 = None
        embedding_1024 = None

        # 3-1. OpenAI 임BE딩 생성 (1536차원)
        try:
            embedding_1536 = llm_client.create_embedding(text=response)
            print(f"[DEBUG][initial_analysis] OpenAI 임베딩 완료 (차원: {len(embedding_1536)})")
        except Exception as e:
            print(f"[DEBUG][initial_analysis] OpenAI 임베딩 실패: {e}")

        final_embedding = {
            "embedding_1536": embedding_1536,
            "embedding_1024": embedding_1024,
        }

        print("[DEBUG][initial_analysis] ===== NODE COMPLETE (interrupt_after 대기) =====")
        return {
            "messages": [("human", user_prompt), ("ai", response)],
            "embedding": final_embedding
        }

    def format_measurements(data: dict, indent: int = 0) -> list:
        """
        InBody 측정 데이터를 재귀적으로 포맷팅
        모든 필드를 자동으로 순회하여 구조화된 텍스트로 변환
        """
        lines = []
        prefix = "  " * indent

        for key, value in data.items():
            if isinstance(value, dict):
                # 중첩 객체 (부위별근육분석, 부위별체지방분석 등)
                lines.append(f"{prefix}**{key}:**")
                lines.extend(format_measurements(value, indent + 1))
            elif isinstance(value, list):
                # 리스트 (드물지만 처리)
                lines.append(f"{prefix}- {key}: {', '.join(map(str, value))}")
            else:
                # 단순 값 (숫자, 문자열 등)
                lines.append(f"{prefix}- {key}: {value}")

        return lines

    def _generate_qa_response(state: AnalysisState, category_name: str, system_prompt: str) -> dict:
        """공통 Q&A 답변 생성 로직"""
        print(f"\n[DEBUG][qa:{category_name}] ===== NODE ENTER =====")
        print(f"[DEBUG][qa:{category_name}] messages count: {len(state.get('messages', []))}")

        # 🔧 InBody 측정 데이터를 System Prompt에 추가 (모든 필드 자동 포함)
        analysis_input = state.get("analysis_input")
        if analysis_input and analysis_input.measurements:
            measurements = analysis_input.measurements

            # 모든 측정 데이터를 재귀적으로 포맷팅 (30개+ 필드 전부 포함)
            key_metrics_lines = ["**[사용자의 현재 InBody 측정 데이터]**"]
            key_metrics_lines.extend(format_measurements(measurements))
            key_metrics = "\n".join(key_metrics_lines)

            # System Prompt 강화
            enhanced_prompt = f"""{system_prompt}

{key_metrics}

⚠️ 위 측정값을 반드시 참고하여, 사용자의 구체적인 수치를 들어 답변해주세요.
일반적인 설명이 아닌, 위 데이터 기반의 개인화된 답변을 제공하세요."""
        else:
            enhanced_prompt = system_prompt
            print(f"[DEBUG][qa:{category_name}] ⚠️ analysis_input 없음, 기본 프롬프트 사용")

        # LangGraph 메시지 객체를 LLM 클라이언트가 이해하는 튜플 리스트로 변환
        history = []
        for msg in state["messages"]:
            role = "user" if msg.type == "human" else "assistant"
            history.append((role, msg.content))

        # 마지막 human 메시지 (사용자 질문) 출력
        last_human = next((c for r, c in reversed(history) if r == "user"), None)
        print(f"[DEBUG][qa:{category_name}] last human message: '{str(last_human)[:100]}'")
        print(f"[DEBUG][qa:{category_name}] history tuples: {len(history)} (roles: {[r for r, _ in history]})")

        # 실제 LLM 호출 (대화 기록 포함)
        print(f"[DEBUG][qa:{category_name}] calling LLM with history...")
        response = llm_client.generate_chat_with_history(
            system_prompt=enhanced_prompt,  # ← 강화된 프롬프트 사용
            messages=history
        )

        print(f"[DEBUG][qa:{category_name}] LLM response length: {len(response)}, preview: '{response[:100]}'")
        print(f"[DEBUG][qa:{category_name}] ===== NODE COMPLETE (interrupt_after 대기) =====\n")
        return {"messages": [("ai", response)]}

    def qa_strength_weakness(state: AnalysisState) -> dict:
        """Node 2-1: 인바디 종합의견 Q&A"""
        system_prompt = """당신은 데이터 기반의 체성분 분석 전문가입니다.
        사용자가 자신의 신체 강점과 약점에 대해 질문했습니다.
        이전 대화에서 제공된 인바디 데이터와 최초 분석 결과를 바탕으로, 다음 항목에 대해 구체적인 수치를 들어 설명해주세요.
        - **강점**: 표준 범위 이상이거나 긍정적인 지표 (예: 높은 골격근량, 적정 체수분 등)
        - **약점**: 개선이 필요한 지표 (예: 높은 체지방률, 부위별 불균형, 낮은 기초대사량 등)
        - **종합 평가**: 현재 신체의 가장 큰 특징을 요약해주세요.

        ⚠️ 중요: 구체적인 운동 계획이나 식단 계획은 절대 제시하지 마세요. 현재 상태 분석만 제공하세요."""
        return _generate_qa_response(state, "강점/약점", system_prompt)

    def qa_health_status(state: AnalysisState) -> dict:
        """Node 2-2: 이전 인바디와 비교 Q&A"""
        system_prompt = """당신은 예방 의학 관점에서 조언하는 건강 컨설턴트입니다.
        사용자가 현재 자신의 전반적인 건강 상태에 대해 질문했습니다.
        이전 대화 내용을 바탕으로, 건강 관점에서 긍정적인 부분과 잠재적인 위험 요소를 나누어 설명해주세요.
        - **긍정적 신호**: 정상 범위에 있는 BMI, 근육량, 혈압 관련 지표 등
        - **주의/경고 신호**: 복부지방률, 내장지방레벨 등 건강 위험도와 직결되는 지표를 중심으로 설명하고, 어떤 질병의 위험을 높일 수 있는지 알려주세요. (의학적 진단이 아님을 명시)
        - **결론**: 현재 상태가 '매우 건강', '건강한 편', '주의 필요', '관리 필요' 중 어디에 가까운지 종합적으로 판단해주세요.

        ⚠️ 중요: 구체적인 운동 계획이나 식단 계획은 절대 제시하지 마세요. 현재 상태 분석만 제공하세요."""
        return _generate_qa_response(state, "건강 상태", system_prompt)

    def qa_impact(state: AnalysisState) -> dict:
        """Node 2-3: 질병 및 특이사항"""
        system_prompt = """당신은 운동생리학자이자 라이프스타일 코치입니다.
        사용자가 현재 신체 상태가 일상과 운동 수행능력에 미치는 영향에 대해 질문했습니다.
        이전 대화 내용을 바탕으로, 현재 체성분 상태가 어떤 결과로 이어질 수 있는지 구체적인 예시를 들어 설명해주세요.
        - **운동 수행능력**: 현재 근육량과 체지방량이 근력, 지구력, 순발력 등에 미치는 영향 (예: '하체 근육이 발달하여 스쿼트나 등산에 유리하지만, 체중 대비 상체 근력이 부족하여 턱걸이 같은 운동은 어려울 수 있습니다.')
        - **일상 생활**: 기초대사량, 체력 수준이 일상적인 피로도, 활동성, 자세 유지 등에 미치는 영향 (예: '기초대사량이 낮아 쉽게 피로감을 느낄 수 있으며, 코어 근육 부족으로 오래 앉아있을 때 허리 통증을 유발할 수 있습니다.')

        ⚠️ 중요: 구체적인 운동 계획이나 식단 계획은 절대 제시하지 마세요. 영향 분석만 제공하세요."""
        return _generate_qa_response(state, "일상/운동 영향", system_prompt)

    def qa_priority(state: AnalysisState) -> dict:
        """Node 2-4: 개선 사항 Q&A"""
        system_prompt = """당신은 동기부여가 뛰어난 현실적인 체성분 분석가입니다.
        사용자가 가장 먼저 개선해야 할 우선순위에 대해 질문했습니다.
        이전 대화 내용을 종합하여, 가장 시급하고 효과가 큰 '개선 영역'을 3가지 우선순위로 제시해주세요.
        - **1순위 (가장 시급)**: 건강 위험을 낮추거나, 가장 큰 불균형을 해소해야 할 영역 (예: 내장지방 감소 필요, 복부비만 개선 필요)
        - **2순위 (체감 효과가 큰 것)**: 단기간에 변화를 느끼거나, 다른 능력 향상에 기반이 되는 영역 (예: 코어 근력 부족, 하체 근육 불균형)
        - **3순위 (장기적 관점)**: 꾸준히 개선해나가야 할 영역 (예: 전반적인 근육량 증가, 기초대사량 향상)
        각 항목에 대해 '왜' 그것이 중요한지 이유를 명확히 설명해주세요.

        ⚠️ 중요: "무슨 운동을 하세요", "무엇을 드세요"와 같은 구체적인 실천 방법은 절대 제시하지 마세요. 개선이 필요한 영역과 이유만 설명하세요."""
        return _generate_qa_response(state, "개선 우선순위", system_prompt)

    def qa_general(state: AnalysisState) -> dict:
        """Node 2-5: 일반 Q&A"""
        system_prompt = """당신은 전문 체성분 분석가입니다.
        이전 대화의 맥락을 유지하면서 사용자의 질문에 답변해주세요.

        ⚠️ 중요: 구체적인 운동 계획이나 식단 계획은 절대 제시하지 마세요. 현재 상태 분석과 개선 필요 영역만 설명하세요."""
        return _generate_qa_response(state, "일반", system_prompt)

    def finalize_analysis(state: AnalysisState) -> dict:
        """Node 3: 분석 확정 및 저장"""
        print(f"\n[DEBUG][finalize] ===== NODE ENTER =====")
        print(f"[DEBUG][finalize] messages count: {len(state.get('messages', []))}")
        print(f"[DEBUG][finalize] → END로 종료\n")
        return {"messages": [("ai", "네, 분석 결과를 확정하고 저장하겠습니다. 추가적인 질문이 있다면 언제든 다시 찾아주세요.")]}

    def route_qa(state: AnalysisState) -> str:
        """사용자 질문에 따라 적절한 Q&A 노드로 라우팅"""
        print(f"\n[DEBUG][route_qa] ===== ROUTING =====")
        print(f"[DEBUG][route_qa] total messages: {len(state.get('messages', []))}")

        # 🔧 수정: 가장 최근 HUMAN 메시지만 선택 (초기 프롬프트 제외)
        last_human_msg = None
        for msg in reversed(state["messages"]):
            if msg.type == "human":
                # 초기 분석 프롬프트 제외 (매우 길거나 "# InBody"로 시작)
                content = msg.content.strip()
                if not (content.startswith("# InBody") or content.startswith("##") or len(content) > 1000):
                    # 실제 사용자 질문 (짧고 간결)
                    last_human_msg = msg
                    break

        # human 메시지가 없으면 initial_analysis 직후 첫 실행 → 기본 노드로
        if not last_human_msg:
            print(f"[DEBUG][route_qa] !! 사용자 질문 없음 (initial_analysis 직후) → qa_general로 기본 라우팅")
            return "qa_general"

        user_question = last_human_msg.content.strip()
        print(f"[DEBUG][route_qa] last human message found: '{user_question[:120]}'")

        # 프론트엔드 카테고리 버튼 키워드 매칭
        if "근육" in user_question:
            destination = "qa_strength_weakness"
        elif "체지방" in user_question:
            destination = "qa_health_status"
        elif "균형" in user_question or "불균형" in user_question:
            destination = "qa_impact"
        elif "우선순위" in user_question or "개선" in user_question:
            destination = "qa_priority"
        elif "확정" in user_question:
            destination = "finalize_analysis"
        # 숫자 기반 라우팅 (하위 호환)
        elif user_question.startswith("1"):
            destination = "qa_strength_weakness"
        elif user_question.startswith("2"):
            destination = "qa_health_status"
        elif user_question.startswith("3"):
            destination = "qa_impact"
        elif user_question.startswith("4"):
            destination = "qa_priority"
        elif user_question.startswith("6"):
            destination = "finalize_analysis"
        else:
            destination = "qa_general"

        print(f"[DEBUG][route_qa] → routing to: {destination}\n")
        return destination

    # 라우팅 맵 정의
    routing_map = {
        "qa_strength_weakness": "qa_strength_weakness",
        "qa_health_status": "qa_health_status",
        "qa_impact": "qa_impact",
        "qa_priority": "qa_priority",
        "qa_general": "qa_general",
        "finalize_analysis": "finalize_analysis",
    }

    workflow = StateGraph(AnalysisState)
    
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
    # 최초 분석 후에는 사용자의 질문을 받아 라우팅합니다.
    workflow.add_conditional_edges(
        "initial_analysis",
        route_qa,
        routing_map
    )
    
    # 각 Q&A 노드는 다시 라우터를 거쳐 다음 질문을 처리합니다. (루프)
    qa_nodes = ["qa_strength_weakness", "qa_health_status", "qa_impact", "qa_priority", "qa_general"]
    for node in qa_nodes:
        workflow.add_conditional_edges(node, route_qa, routing_map)

    # 확정 후 종료
    workflow.add_edge("finalize_analysis", END)

    # 체크포인터 설정 (인메모리 저장소)
    # 실제 운영 환경에서는 PostgresSaver 등을 사용하여 DB에 저장하는 것이 좋습니다.
    memory = MemorySaver()

    # 휴먼 피드백을 위해, LLM이 답변을 생성한 후에는 항상 멈춥니다.
    # 서비스(API)는 이 멈춘 지점에서 사용자 입력을 받아 다음 단계로 진행합니다.
    # initial_analysis는 제외 (PASSTHROUGH 시 다음 노드로 계속 진행되어야 함)
    agent = workflow.compile(checkpointer=memory, interrupt_after=qa_nodes)
    
    return agent
    
