"""
LLM 서비스 (RAG 버전)
AI 분석 및 계획 생성 (LangGraph 에이전트 + RAG 사용)
"""

from typing import Dict, Any, Optional
from datetime import datetime
import os
from dotenv import load_dotenv

from schemas.llm import StatusAnalysisInput, GoalPlanInput
from services.llm.llm_clients import create_llm_client
from .agent_graph_rag import create_analysis_agent_with_rag
from .weekly_plan_graph_rag import create_weekly_plan_agent_with_rag

load_dotenv()


class LLMServiceRAG:
    """LLM API 호출 서비스 (RAG 포함)"""

    def __init__(self, model_version: str = "gpt-4o-mini", use_rag: bool = True):
        """LLM 에이전트 및 클라이언트 초기화 (RAG 포함)"""
        self.model_version = model_version
        self.use_rag = use_rag
        self.llm_client = create_llm_client(self.model_version)
        self.analysis_agent = create_analysis_agent_with_rag(self.llm_client, use_rag=self.use_rag)
        self.weekly_plan_agent = create_weekly_plan_agent_with_rag(self.llm_client, use_rag=self.use_rag)

    def prepare_status_analysis_input(
        self,
        record_id: int,
        user_id: int,
        measured_at: datetime,
        measurements: Dict[str, Any],
        body_type1: Optional[str],
        body_type2: Optional[str]
    ) -> Dict[str, Any]:
        """
        LLM1 (RAG): 건강 상태 분석용 input 데이터 준비

        Args:
            record_id: 건강 기록 ID
            user_id: 사용자 ID
            measured_at: 측정 일시
            measurements: 인바디 측정 데이터(체형 분류 포함)
            body_type1: 1차 체형 분류
            body_type2: 2차 체형 분류

        Returns:
            LLM에 전달할 input 데이터 (프론트엔드에서 LLM API 호출 시 사용)
        """
        return {
            "record_id": record_id,
            "user_id": user_id,
            "measured_at": measured_at,
            "measurements": measurements,
            "body_type1": body_type1,
            "body_type2": body_type2,
        }

    def prepare_goal_plan_input(
        self,
        # 사용자 요구사항
        user_goal_type: Optional[str],
        user_goal_description: Optional[str],
        # 선택된 건강 기록
        record_id: int,
        user_id: int,
        measured_at: datetime,
        measurements: Dict[str, Any],
        # LLM1 분석 결과
        status_analysis_result: Optional[str] = None,
        status_analysis_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        LLM2 (RAG): 주간 계획서 생성용 input 데이터 준비

        Args:
            user_goal_type: 사용자 목표 타입
            user_goal_description: 사용자 목표 상세
            record_id: 선택된 건강 기록 ID
            user_id: 사용자 ID
            measured_at: 측정 일시
            measurements: 인바디 측정 데이터(체형 분류 포함)
            status_analysis_result: LLM1의 분석 결과 텍스트
            status_analysis_id: LLM1 분석 결과 ID

        Returns:
            LLM에 전달할 input 데이터 (프론트엔드에서 LLM API 호출 시 사용)
        """
        return {
            "user_goal_type": user_goal_type,
            "user_goal_description": user_goal_description,
            "record_id": record_id,
            "user_id": user_id,
            "measured_at": measured_at,
            "measurements": measurements,
            "status_analysis_result": status_analysis_result,
            "status_analysis_id": status_analysis_id
        }

    # =====================================================
    # RAG가 추가된 LLM API 메서드들
    # =====================================================

    async def call_status_analysis_llm(
        self,
        analysis_input: StatusAnalysisInput,
        thread_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        LangGraph 에이전트를 호출하여 건강 상태 분석 수행 (RAG 포함)

        Args:
            analysis_input: StatusAnalysisInput 스키마 객체
            thread_id: 대화 스레드 ID (선택)

        Returns:
            {
                "analysis_text": str,  # LLM 응답
                "embedding": {"embedding_1536": [...], "embedding_1024": [...]},
                "thread_id": str,
                "rag_context": str  # RAG 검색 결과
            }
        """
        # 1. 스레드 ID 생성 (제공되지 않은 경우)
        if not thread_id:
            thread_id = f"analysis_rag_{analysis_input.user_id}_{analysis_input.record_id}_{datetime.now().timestamp()}"

        config = {"configurable": {"thread_id": thread_id}}

        # 2. LangGraph 에이전트 호출 (최초 분석 + RAG)
        initial_state = self.analysis_agent.invoke(
            {
                "analysis_input": analysis_input,
                "messages": [],
                "embedding": None,
                "rag_context": None
            },
            config=config
        )

        # 3. 결과 추출
        analysis_text = initial_state['messages'][-1].content
        embedding = initial_state.get("embedding")
        rag_context = initial_state.get("rag_context", "")

        return {
            "analysis_text": analysis_text,
            "embedding": embedding,
            "thread_id": thread_id,
            "rag_context": rag_context
        }

    async def chat_with_analysis(
        self,
        thread_id: str,
        user_message: str
    ) -> str:
        """
        휴먼 피드백 (Q&A) 처리: 기존 스레드에 이어서 대화 수행
        """
        config = {"configurable": {"thread_id": thread_id}}

        # LangGraph 실행 (이전 상태에서 이어서 실행)
        result = self.analysis_agent.invoke(
            {"messages": [("human", user_message)]},
            config=config
        )

        # 마지막 AI 응답 반환
        return result["messages"][-1].content

    async def call_goal_plan_llm(
        self,
        plan_input: GoalPlanInput,
        thread_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        LLM2: 주간 계획서 생성 API 호출 (RAG 포함)

        Args:
            plan_input: GoalPlanInput 스키마 객체
            thread_id: 대화 스레드 ID (선택)

        Returns:
            {
                "plan_text": str,  # LLM이 생성한 주간 계획서
                "thread_id": str,
                "rag_context": str  # RAG 검색 결과
            }
        """
        # 1. 스레드 ID 생성 (제공되지 않은 경우)
        if not thread_id:
            thread_id = f"plan_rag_{plan_input.user_id}_{plan_input.record_id}_{datetime.now().timestamp()}"

        config = {"configurable": {"thread_id": thread_id}}

        # 2. LangGraph 에이전트 호출 (RAG 포함)
        initial_state = self.weekly_plan_agent.invoke(
            {
                "plan_input": plan_input,
                "messages": [],
                "rag_context": None
            },
            config=config
        )

        # 3. 결과 추출
        plan_text = initial_state['messages'][-1].content
        rag_context = initial_state.get("rag_context", "")

        return {
            "plan_text": plan_text,
            "thread_id": thread_id,
            "rag_context": rag_context
        }

    async def chat_with_plan(
        self,
        thread_id: str,
        user_message: str
    ) -> str:
        """
        LLM2 휴먼 피드백 (Q&A) 처리: 주간 계획 수정 및 질의응답
        """
        config = {"configurable": {"thread_id": thread_id}}

        # LangGraph 실행 (이전 상태에서 이어서 실행)
        result = self.weekly_plan_agent.invoke(
            {"messages": [("human", user_message)]},
            config=config
        )

        # 마지막 AI 응답 반환
        return result["messages"][-1].content
