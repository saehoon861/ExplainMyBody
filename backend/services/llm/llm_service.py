"""
LLM 서비스
AI 분석 및 계획 생성 (LangGraph 에이전트 사용)
"""

from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from datetime import datetime
import os
from dotenv import load_dotenv

from schemas.llm import StatusAnalysisInput, GoalPlanInput, LLMInteractionCreate
from repositories.llm.llm_interaction_repository import LLMInteractionRepository
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

    async def chat_with_analysis(
        self,
        thread_id: str,
        user_message: str
    ) -> str:
        """
        LLM1 에 대한
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
        db: Session,
        input_data: GoalPlanInput
    ) -> dict:
        """
        LLM2: 주간 계획서 생성 API 호출 및 초기 상호작용 저장
        """
        # 1. 스레드 ID 생성
        thread_id = f"plan_{input_data.user_id}_{input_data.record_id}_{datetime.now().timestamp()}"
        config = {"configurable": {"thread_id": thread_id}}



        # 2. LangGraph 에이전트 호출
        initial_state = self.weekly_plan_agent.invoke(
            {"plan_input": input_data},
            config=config
        )
        
        # (
        #     {"plan_input": input_data},
        #     config=config
        # )
        
        plan_text = initial_state['messages'][-1].content

        # 3. 초기 LLM 상호작용 DB에 저장
        interaction_schema = LLMInteractionCreate(
            llm_stage="llm2",
            source_type="weekly_plan_initial",
            source_id=input_data.record_id,
            output_text=plan_text,
            model_version=self.model_version
        )
        new_interaction = LLMInteractionRepository.create(db, input_data.user_id, interaction_schema)

        # 4. 결과 반환
        return {
            "plan_text": plan_text,
            "thread_id": thread_id,
            "llm_interaction_id": new_interaction.id
        }

    async def chat_with_plan(
        self,
        thread_id: str,
        user_message: str,
        existing_plan: Optional[str] = None
    ) -> str:
        """
        LLM2 휴먼 피드백 (Q&A) 처리: 주간 계획 수정 및 질의응답
        """
        import re
        print(f"--- [DEBUG] chat_with_plan 진입 ---")
        print(f"--- [DEBUG] thread_id: {thread_id}")
        print(f"--- [DEBUG] raw user_message: {user_message}")

        config = {"configurable": {"thread_id": thread_id}}
        
        # 메시지 파싱 ([Category: ...] 분리)
        category = None
        clean_message = user_message
        
        # Regex로 [Category: ...] 패턴 추출
        match = re.match(r"^\[Category:\s*(.*?)\]\s*(.*)$", user_message, re.DOTALL)
        if match:
            category_label = match.group(1).strip()
            clean_message = match.group(2).strip()
            print(f"--- [DEBUG] Parsed Category Label: {category_label}")
            print(f"--- [DEBUG] Clean Message: {clean_message}")
            
            # 카테고리 라벨을 내부 키로 매핑 (필요시)
            # 현재는 단순 매핑 또는 그대로 전달. 그래프의 router 로직에 의존.
            # 그래프에서는 "운동 플랜 조정", "식단 조정" 등을 기대함.
            # 프론트엔드 라벨: "📅 주간 계획", "🏋️ 부위별 운동" 등.
            # 여기서는 우선 매핑 없이 전달하거나, 간단한 변환 로직 추가 가능.
            
            # 임시 매핑 로직 (프론트 라벨 -> 그래프 내부 카테고리)
            if "운동" in category_label or "플랜" in category_label or "계획" in category_label: # 예: 운동 플랜 조정
                category = "adjust_exercise_plan"
            elif "식단" in category_label:
                category = "adjust_diet_plan"
            elif "강도" in category_label:
                category = "adjust_intensity"
            else:
                # 그 외 (주간 계획, 부위별 운동 등)은 일반 Q&A로 처리하되,
                # 그래프 라우터가 "qa_general"로 폴백하도록 None 또는 "qa_general" 전달
                category = "qa_general"
            
            print(f"--- [DEBUG] Mapped Category Key: {category}")
            
        else:
            print("--- [DEBUG] No Category prefix found. Treating as general message.")
            category = "qa_general"

        # 상태 업데이트 준비
        input_payload = {
            "messages": [("human", clean_message)],
            # feedback_category를 업데이트하여 라우터가 올바른 경로를 타도록 함
            "feedback_category": category,
            "existing_plan": existing_plan
        }
        
        print(f"--- [DEBUG] llm_service: existing_plan 전달 여부: {bool(existing_plan)} ---")
        if existing_plan:
            print(f"--- [DEBUG] llm_service: existing_plan preview: {existing_plan[:100]}... ---")
        print(f"--- [DEBUG] Invoking weekly_plan_agent with payload: {input_payload}")

        # LangGraph 실행 (이전 상태에서 이어서 실행)
        try:
            result = self.weekly_plan_agent.invoke(
                input_payload,
                config=config
            )
            print("--- [DEBUG] LangGraph invocation successful")
            # print(f"--- [DEBUG] Result messages: {result.get('messages')}")
            
            last_message = result["messages"][-1].content
            print(f"--- [DEBUG] Last AI Message: {last_message[:100]}...") # 길면 자름
            
            return last_message
            
        except Exception as e:
            print(f"--- [ERROR] LangGraph invocation failed: {e}")
            import traceback
            traceback.print_exc()
            raise e

    async def refine_plan(
        self,
        thread_id: str,
        state_update: dict
    ) -> str:
        """
        LLM2 휴먼 피드백: 구조화된 피드백으로 주간 계획 수정
        """
        print(f"--- [DEBUG] refine_plan 진입 ---")
        print(f"--- [DEBUG] thread_id: {thread_id}")
        print(f"--- [DEBUG] state_update: {state_update}")

        config = {"configurable": {"thread_id": thread_id}}
        
        # LangGraph 실행 (전달받은 state_update로 상태 업데이트)
        try:
            result = self.weekly_plan_agent.invoke(
                state_update,
                config=config
            )
            print("--- [DEBUG] LangGraph invocation successful")
            
            last_message = result["messages"][-1].content
            print(f"--- [DEBUG] Last AI Message: {last_message[:100]}...")
            
            return last_message
        except Exception as e:
            print(f"--- [ERROR] LangGraph invocation failed: {e}")
            import traceback
            traceback.print_exc()
            raise e
