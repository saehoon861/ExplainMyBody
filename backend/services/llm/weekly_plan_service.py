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
from schemas.llm import WeeklyPlanCreate, GoalPlanRequest, GoalPlanInput

# 가장 최신 주간 계획이 있는지 없는지 확인

# 있다면 가장 최신 주간 계획 가져오기

# 주간 계획이 현재 진행중인지 확인 (start_date <= today <= end_date)
# 새로운 inbody 측정값이 있는지 확인 (start_date <= measured_at)

# 하나라도 True면 새로운 주간 계획서 작성
# 둘 다 False면 새로운 주간 계획서 작성하지 않음 & 기존 주간 계획서 반환


class WeeklyPlanService:
    def __init__(self):
        self.llm_service = LLMService()
        # self.health_service = HealthService()
        self.health_service = HealthService(llm_service=self.llm_service)

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
        
        # Early return: 기존 계획 재사용
        latest_plan = WeeklyPlanRepository.get_latest(db, user_id)
        if not self._should_create_new_plan(db, user_id, latest_plan):
            return latest_plan



        # 1. LLM 입력 데이터 준비 (HealthService 활용)
        # prepare_goal_plan은 Response 객체를 반환하므로 input_data만 추출
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

        # 2. LLM 호출 (주간 계획 생성)
        # plan_text = await self.llm_service.call_goal_plan_llm(llm_input)
        result = await self.llm_service.call_goal_plan_llm(llm_input)
        plan_text = result["plan_text"]
        thread_id = result["thread_id"]
        
        # 3. 데이터 저장
        # LLM이 준 텍스트를 plan_data의 'content' 필드에 저장 (임시)
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
                "thread_id": thread_id # thread_id를 plan_data에 추가
            },
            model_version=self.llm_service.model_version
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
        response = await self.llm_service.chat_with_plan(thread_id, message)
        return response