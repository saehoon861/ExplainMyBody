"""
LLM 서비스
AI 분석 및 계획 생성 (LangGraph 에이전트 사용)
"""

from typing import Dict, Any, Optional
from datetime import datetime
import os
from dotenv import load_dotenv

from schemas.llm import StatusAnalysisInput, GoalPlanInput
from services.llm.llm_clients import create_llm_client
from .agent_graph import create_analysis_agent
from .weekly_plan_graph import create_weekly_plan_agent

load_dotenv()


class LLMService:
    """LLM API 호출 서비스"""

    def __init__(self):
        """LLM 에이전트 및 클라이언트 초기화"""
        self.model_version = "gpt-4o-mini"  # 또는 설정에서 가져옴
        self.llm_client = create_llm_client(self.model_version)
        self.analysis_agent = create_analysis_agent(self.llm_client)
        self.weekly_plan_agent = create_weekly_plan_agent(self.llm_client)

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

    # 체크포인트 소실 시 폴백용 시스템 프롬프트
    _ANALYSIS_QA_FALLBACK_PROMPT = """당신은 데이터 기반의 체성분 분석 및 피트니스 전문가입니다.
위에서 제공된 인바디 분석 결과를 참고하여 사용자의 질문에 답변합니다.

답변 가이드:
- 근육 관련: 부위별 근육 수준, 골격근량과 강점/약점을 구체적인 수치로 설명
- 체지방 관련: 체지방률, 복부지방률, 내장지방 레벨과 건강 위험도를 설명
- 균형/불균형 관련: 상체·하체, 좌·우 근육·체지방 불균형과 그 영향을 설명
- 기타: 분석 결과를 맥락으로 활용하여 답변

수치와 근거를 들어 구체적이고 실용적인 답변을 제시하세요."""

    async def chat_with_analysis(
        self,
        thread_id: str,
        user_message: str,
        report_context: str = None
    ) -> str:
        """
        LLM1 휴먼 피드백 (Q&A) 처리

        - 체크포인트가 있으면: LangGraph resume (중단 지점 이후 재개)
        - 체크포인트가 없으면: report_context를 대화 맥락으로 직접 LLM 호출 (폴백)
        """
        print(f"[DEBUG][chat_with_analysis] thread_id={thread_id!r}, user_message='{user_message[:80]}'")
        print(f"[DEBUG][chat_with_analysis] report_context present: {report_context is not None}")

        if thread_id:
            config = {"configurable": {"thread_id": thread_id}}
            print(f"[DEBUG][chat_with_analysis] → agent.invoke() 시작 (thread_id={thread_id})")
            try:
                result = self.analysis_agent.invoke(
                    {"messages": [("human", user_message)]},
                    config=config
                )
                print(f"[DEBUG][chat_with_analysis] → agent.invoke() 완료")
                return result["messages"][-1].content
            except KeyError as e:
                # 체크포인트 소실 (서버 재시작 등) → 폴백으로 진행
                print(f"[DEBUG][chat_with_analysis] !! KeyError: {e} — 체크포인트 소실, 폴백으로 진행")
            except Exception as e:
                print(f"[DEBUG][chat_with_analysis] !! Exception: {type(e).__name__}: {e} — 폴백으로 진행")
        else:
            print("[DEBUG][chat_with_analysis] !! thread_id 없음 → 폴백으로 진행")

        # 폴백: report_context를 대화 맥락으로 직접 LLM 호출
        print("[DEBUG][chat_with_analysis] → 폴백 LLM 호출 시작")
        messages = [("assistant", report_context)] if report_context else []
        messages.append(("user", user_message))
        return self.llm_client.generate_chat_with_history(
            system_prompt=self._ANALYSIS_QA_FALLBACK_PROMPT,
            messages=messages
        )

    async def call_goal_plan_llm(
        self,
        input_data: GoalPlanInput
    # ) -> str:
    ) -> Dict[str, Any]:
        """
        LLM2: 주간 계획서 생성 API 호출

        Args:
            input_data: GoalPlanInput 스키마 객체

        Returns:
            {
                "plan_text": str,
                "thread_id": str
            }
        """
        # 1. 스레드 ID 생성 (필요 시)
        thread_id = f"plan_{input_data.user_id}_{input_data.record_id}_{datetime.now().timestamp()}"
        config = {"configurable": {"thread_id": thread_id}}

        # 2. LangGraph 에이전트 호출
        # initial_state = self.weekly_plan_agent.invoke(
        #     {"plan_input": input_data},
        #     config=config
        # )
        initial_state = await self.weekly_plan_agent.ainvoke(
            {"plan_input": input_data},
            config=config
        )


        # 3. 결과 반환 (마지막 AI 메시지)
        # return initial_state['messages'][-1].content
        return {
            "plan_text": initial_state['messages'][-1].content,
            "thread_id": thread_id
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

        result = self.weekly_plan_agent.invoke(
            {"messages": [("human", user_message)]},
            config=config
        )

        # 마지막 AI 응답 반환
        return result["messages"][-1].content
