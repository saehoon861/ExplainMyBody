"""
주간 계획 서비스 (RAG 버전)
LLM2 (RAG)를 사용하여 주간 계획을 생성하고 관리
"""
from sqlalchemy.orm import Session
from datetime import date, timedelta
import json
from typing import Dict, Any

from services.llm.llm_service_rag import LLMServiceRAG
from services.common.health_service_rag import HealthServiceRAG
from repositories.llm.weekly_plan_repository import WeeklyPlanRepository
from schemas.llm import WeeklyPlanCreate, GoalPlanRequest, GoalPlanInput

class WeeklyPlanServiceRAG:
    def __init__(self):
        self.llm_service_rag = LLMServiceRAG(model_version="gpt-4o-mini", use_rag=True)
        self.health_service_rag = HealthServiceRAG()

    async def generate_plan(
        self,
        db: Session,
        user_id: int,
        request_data: GoalPlanRequest
    ):
        """
        주간 계획 생성 (LLM RAG 호출)
        """
        # 1. LLM 입력 데이터 준비 (HealthServiceRAG 활용)
        # prepare_goal_plan은 Response 객체를 반환하므로 input_data만 추출
        prepared_response = self.health_service_rag.prepare_goal_plan(
            db=db,
            user_id=user_id,
            record_id=request_data.record_id,
            user_goal_type=request_data.user_goal_type,
            user_goal_description=request_data.user_goal_description
        )

        if not prepared_response:
            raise ValueError("건강 기록을 찾을 수 없거나 권한이 없습니다.")

        llm_input: GoalPlanInput = prepared_response.input_data

        # 2. LLM RAG 호출 (주간 계획 생성)
        thread_id = f"weekly_plan_rag_{request_data.record_id}"

        result = await self.llm_service_rag.call_goal_plan_llm(
            plan_input=llm_input,
            thread_id=thread_id
        )

        plan_text = result["plan_text"]
        rag_context = result.get("rag_context", "")

        # 3. 데이터 저장
        # LLM이 준 텍스트를 plan_data의 'content' 필드에 저장
        # 프론트엔드에서는 이 content를 마크다운으로 렌더링
        today = date.today()
        next_monday = today + timedelta(days=(7 - today.weekday()))

        plan_create = WeeklyPlanCreate(
            week_number=1, # 로직에 따라 계산 필요
            start_date=next_monday,
            end_date=next_monday + timedelta(days=6),
            plan_data={
                "content": plan_text,
                "raw_response": plan_text,
                "rag_context": rag_context
            },
            model_version="gpt-4o-mini-rag"
        )

        new_plan = WeeklyPlanRepository.create(db, user_id, plan_create)
        return new_plan

    async def chat_with_plan(
        self,
        plan_id: int, # DB 조회용 (스레드 ID 매핑 필요 시)
        thread_id: str,
        message: str
    ) -> str:
        """
        주간 계획에 대한 수정 요청/질의응답
        """
        # LangGraph 상태 유지를 위해 thread_id 사용
        response = await self.llm_service_rag.chat_with_plan(message, thread_id)
        return response
