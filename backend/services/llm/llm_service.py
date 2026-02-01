"""
LLM 서비스
AI 분석 및 계획 생성 (LangGraph 에이전트 사용)
"""

from typing import Dict, Any, Optional
from datetime import datetime
import os
from dotenv import load_dotenv

from schemas.llm import StatusAnalysisInput
from services.llm.llm_clients import create_llm_client
from .agent_graph import create_analysis_agent

load_dotenv()


class LLMService:
    """LLM API 호출 서비스 (현재는 input 데이터 반환용)"""

    def __init__(self):
        """LLM 에이전트 및 클라이언트 초기화"""
        self.model_version = "gpt-4o-mini"  # 또는 설정에서 가져옴
        self.llm_client = create_llm_client(self.model_version)
        self.analysis_agent = create_analysis_agent(self.llm_client)

        # 챗봇 대화 이력 저장소 (메모리 기반)
        # {thread_id: [("user", "메시지"), ("assistant", "응답"), ...]}
        self.conversation_history = {}

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
        LLM1: 건강 상태 분석용 input 데이터 준비

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
        LLM2: 주간 계획서 생성용 input 데이터 준비

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
    # 아래는 팀원이 LLM API 연동 시 구현할 메서드들
    # =====================================================

    async def call_status_analysis_llm(
        self,
        input_data: StatusAnalysisInput
    ) -> Dict[str, Any]:
        """
        LangGraph 에이전트를 호출하여 건강 상태 분석 수행

        Args:
            input_data: StatusAnalysisInput 스키마 객체

        Returns:
            {
                "analysis_text": str,
                "embedding": {"embedding_1536": [...], "embedding_1024": [...]},
                "thread_id": str
            }
        """
        # 1. 각 분석 세션을 위한 고유 스레드 ID 생성
        thread_id = f"analysis_{input_data.user_id}_{input_data.record_id}_{datetime.now().timestamp()}"
        config = {"configurable": {"thread_id": thread_id}}

        # 2. LangGraph 에이전트 호출 (최초 분석)
        initial_state = self.analysis_agent.invoke(
            {"analysis_input": input_data},
            config=config
        )

        # 3. 결과 추출
        analysis_text = initial_state['messages'][-1].content
        embedding = initial_state.get("embedding")

        return {"analysis_text": analysis_text, "embedding": embedding, "thread_id": thread_id}

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
        # messages 키에 새로운 사용자 메시지 추가
        result = self.analysis_agent.invoke(
            {"messages": [("human", user_message)]},
            config=config
        )
        
        # 마지막 AI 응답 반환
        return result["messages"][-1].content

    async def call_goal_plan_llm(
        self,
        input_data: Dict[str, Any]
    ) -> str:
        """
        TODO: 팀원이 구현 예정
        LLM2: 주간 계획서 생성 API 호출

        Args:
            input_data: prepare_goal_plan_input()의 반환값

        Returns:
            LLM이 생성한 주간 계획서 텍스트
        """
        raise NotImplementedError("LLM API 연동 미구현 - 팀원이 구현 예정")

    async def chatbot_conversation(
        self,
        bot_type: str,
        user_message: str,
        thread_id: Optional[str] = None,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        챗봇 대화 처리

        Args:
            bot_type: 챗봇 유형 ("inbody-analyst" 또는 "workout-planner")
            user_message: 사용자 메시지
            thread_id: 기존 대화 스레드 ID (없으면 새로 생성)
            user_id: 사용자 ID (옵션)

        Returns:
            {
                "response": str,  # AI 응답
                "thread_id": str  # 대화 스레드 ID
            }
        """
        # 1. Thread ID 생성 또는 재사용
        if not thread_id:
            import uuid
            thread_id = f"chatbot_{bot_type}_{user_id or 'guest'}_{uuid.uuid4().hex[:8]}"

        # 2. 봇 타입별 시스템 프롬프트 설정
        SYSTEM_PROMPTS = {
            "inbody-analyst": """당신은 친근하고 전문적인 인바디 분석 전문가입니다.
사용자의 체성분 데이터를 분석하고, 건강한 신체를 위한 맞춤형 조언을 제공합니다.
식단, 운동, 생활습관에 대해 구체적이고 실용적인 정보를 제공하세요.
답변은 친근하면서도 전문적인 톤으로 작성하고, 이모지를 적절히 사용하세요.""",

            "workout-planner": """당신은 열정적이고 전문적인 운동 플래너 전문가입니다.
사용자의 목표와 현재 체력 수준에 맞는 최적의 운동 루틴을 제안합니다.
올바른 자세, 운동 빈도, 강도 조절에 대해 구체적인 조언을 제공하세요.
답변은 동기부여가 되는 톤으로 작성하고, 이모지를 적절히 사용하세요."""
        }

        system_prompt = SYSTEM_PROMPTS.get(bot_type, SYSTEM_PROMPTS["inbody-analyst"])

        # 3. 대화 이력 불러오기 또는 새로 생성
        if thread_id not in self.conversation_history:
            self.conversation_history[thread_id] = []

        # 4. 사용자 메시지 추가 (튜플 형태: role, content)
        self.conversation_history[thread_id].append(("user", user_message))

        # 5. OpenAI API 호출 (대화 이력 포함)
        try:
            ai_response = self.llm_client.generate_chat_with_history(
                system_prompt=system_prompt,
                messages=self.conversation_history[thread_id]
            )

            # 6. AI 응답을 대화 이력에 저장
            self.conversation_history[thread_id].append(("assistant", ai_response))

            return {
                "response": ai_response,
                "thread_id": thread_id
            }

        except Exception as e:
            # 오류 시 폴백 응답 (대화 이력에서 마지막 사용자 메시지 제거)
            self.conversation_history[thread_id].pop()
            return {
                "response": "죄송합니다. 일시적인 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
                "thread_id": thread_id
            }
