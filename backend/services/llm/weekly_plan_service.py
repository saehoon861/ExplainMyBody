"""
주간 계획 서비스
LLM2를 사용하여 주간 계획을 생성하고 관리
"""
from sqlalchemy.orm import Session
from datetime import date, timedelta
import json
from typing import Dict, Any

from services.llm.llm_service import LLMService
from services.common.health_service import HealthService
from repositories.llm.weekly_plan_repository import WeeklyPlanRepository
from repositories.common.health_record_repository import HealthRecordRepository
from schemas.llm import (
    WeeklyPlanCreate, 
    GoalPlanRequest, 
    GoalPlanInput, 
    WeeklyPlanFeedbackRequest,
    LLMInteractionCreate
)
from schemas.human_feedback import HumanFeedbackCreate
from repositories.llm.llm_interaction_repository import LLMInteractionRepository
from repositories.llm.human_feedback_repository import HumanFeedbackRepository

# 가장 최신 주간 계획이 있는지 없는지 확인

# 있다면 가장 최신 주간 계획 가져오기


# 주간 계획이 현재 진행중인지 확인 (start_date <= today <= end_date)
# 새로운 inbody 측정값이 있는지 확인 (start_date <= measured_at)

# 하나라도 True면 새로운 주간 계획서 작성
# 둘 다 False면 새로운 주간 계획서 작성하지 않음 & 기존 주간 계획서 반환


class WeeklyPlanService :
    def __init__(self):
        self.llm_service = LLMService()
        self.health_service = HealthService()

    def _should_create_new_plan(
        self, 
        db: Session, 
        user_id: int, 
        latest_plan # 타입 힌트 없음.
    ) -> bool:
        """새 주간 계획 생성이 필요한지 판단"""
        if not latest_plan:
            return True
        
        today = date.today()
        
        # 트리거 1: 계획 기간 만료
        if today > latest_plan.end_date:
            return True
        
        # 트리거 2: 새로운 인바디 측정
        latest_inbody = HealthRecordRepository.get_latest(db, user_id)
        if latest_inbody and latest_inbody.measured_at > latest_plan.created_at:
            return True
    
        return False


    async def generate_plan(
        self,
        db: Session,
        user_id: int,
        request_data: GoalPlanRequest
    ):
        """
        주간 계획 생성 (LLM 호출)
        """
        #fixme : 기존 계획 재사용 시 이후 대화에서 LLM이 기존 주간 계획을 알지 못하는 문제 발생.
        # 해결 방안: 
        # 1. LLM이 대화할 때마다 최신 주간 계획을 함께 전달
        # 2. LLM에게 현재 진행중인 주간 계획을 알려주는 기능 추가
        # Early return: 기존 계획 재사용
        latest_plan = WeeklyPlanRepository.get_latest(db, user_id)
        if not self._should_create_new_plan(db, user_id, latest_plan):
            return {
                "weekly_plan": latest_plan,
                "thread_id": latest_plan.thread_id,
                "initial_llm_interaction_id": latest_plan.initial_llm_interaction_id
            }

        # 1. LLM 입력 데이터 준비 (HealthService 활용)
        prepared_response = self.health_service.prepare_goal_plan(
            db=db,
            user_id=user_id,
            record_id=request_data.record_id,
            user_goal_type=request_data.user_goal_type,
            user_goal_description=request_data.user_goal_description
        )
        
        if not prepared_response:
            raise ValueError("건강 기록을 찾을 수 없거나 권한이 없습니다.")
            
        llm_input: GoalPlanInput = prepared_response.input_data

        # 2. LLM 호출 (주간 계획 생성) 및 초기 LLM 상호작용 저장
        llm_response = await self.llm_service.call_goal_plan_llm(db, llm_input)
        
        # 3. 데이터 저장
        today = date.today()
        next_monday = today + timedelta(days=(7 - today.weekday()))
        
        plan_create = WeeklyPlanCreate(
            thread_id=llm_response["thread_id"],
            initial_llm_interaction_id=llm_response["llm_interaction_id"],
            week_number=1, # 로직에 따라 계산 필요
            start_date=next_monday,
            end_date=next_monday + timedelta(days=6),
            plan_data={
                "content": llm_response["plan_text"],
                "raw_response": llm_response["plan_text"]
            },
            model_version=self.llm_service.model_version
        )
        
        new_plan = WeeklyPlanRepository.create(db, user_id, plan_create)
        
        return {
            "weekly_plan": new_plan,
            "thread_id": llm_response["thread_id"],
            "initial_llm_interaction_id": llm_response["llm_interaction_id"]
        }

    async def chat_with_plan(
        self,
        db: Session,
        user_id: int,
        plan_id: int, 
        thread_id: str,
        message: str
    ) -> str:
        """
        주간 계획에 대한 수정 요청/질의응답 (DB 저장 포함)
        """
        # 1. LLM Service 호출 (LangGraph 실행)
        response_text = await self.llm_service.chat_with_plan(thread_id, message)
        
        # 2. 결과 DB 저장 (이력 추적)
        # LLMInteraction 저장
        interaction_schema = LLMInteractionCreate(
            llm_stage="llm2",  # 주간 계획 단계
            source_type="weekly_plan_chat",
            source_id=plan_id,
            output_text=response_text,
            model_version=self.llm_service.model_version,
            parent_interaction_id=None # 필요하다면 이전 interaction ID를 추적해야 하지만, 현재는 단순 채팅 저장이 목적
        )
        LLMInteractionRepository.create(db, user_id, interaction_schema)

        return response_text

    async def refine_plan_with_feedback(
        self,
        db: Session,
        user_id: int,
        request: WeeklyPlanFeedbackRequest
    ) -> str:
        """
        구조화된 피드백을 받아 주간 계획을 수정하고, 모든 과정을 DB에 기록합니다.
        """
        # 1. 사용자 피드백을 DB에 저장
        feedback_schema = HumanFeedbackCreate(
            llm_interaction_id=request.parent_interaction_id,
            feedback_category=request.feedback_category,
            feedback_text=request.feedback_text
        )
        saved_feedback = HumanFeedbackRepository.create(db, user_id, feedback_schema)

        # 2. LangGraph 에이전트 호출을 위한 상태 준비
        state_update = {
            "feedback_category": request.feedback_category,
            "feedback_text": request.feedback_text,
        }

        # 3. LLMService를 통해 LangGraph 에이전트 호출
        new_plan_text = await self.llm_service.refine_plan(
            thread_id=request.thread_id,
            state_update=state_update
        )

        # 4. 새로운 LLM 상호작용 결과를 DB에 저장 (이력 추적)
        interaction_schema = LLMInteractionCreate(
            llm_stage="llm2",  # 주간 계획 단계
            source_type="weekly_plan_feedback",
            output_text=new_plan_text,
            model_version=self.llm_service.model_version,
            parent_interaction_id=request.parent_interaction_id,
            triggering_feedback_id=saved_feedback.id
        )
        LLMInteractionRepository.create(db, user_id, interaction_schema)

        # 5. 최종적으로 생성된 텍스트 응답 반환
        return new_plan_text
