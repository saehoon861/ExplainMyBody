"""
주간 계획 라우터
/api/weekly-plans/*
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from schemas.llm import (
    WeeklyPlanCreate, 
    WeeklyPlanResponse, 
    WeeklyPlanUpdate,
    GoalPlanRequest,
    GoalPlanResponse,
    WeeklyPlanChatRequest,
    WeeklyPlanChatResponse,
    WeeklyPlanFeedbackRequest,
    WeeklyPlanUnifiedRequest,
    WeeklyPlanUnifiedResponse,
    GenerateWeeklyPlanRequest,
    ChatWeeklyPlanRequest
)
from repositories.llm.weekly_plan_repository import WeeklyPlanRepository
from services.llm.weekly_plan_service import WeeklyPlanService
from typing import List, Union
from datetime import date
# Note: 현재는 Service가 ValueError/Exception을 발생시킴
# 향후 Service 레이어 개선 시 아래 예외들을 사용할 수 있음
# from exceptions import WeeklyPlanNotFoundError, WeeklyPlanGenerationError

router = APIRouter()
weekly_plan_service = WeeklyPlanService()


@router.post("/session", response_model=WeeklyPlanUnifiedResponse, status_code=200)
async def weekly_plan_session(
    user_id: int,
    request: WeeklyPlanUnifiedRequest,
    db: Session = Depends(get_db)
):
    """
    주간 계획 통합 세션 (생성 및 채팅)
    
    - **user_id**: 사용자 ID
    - **request**: 통합 요청 (action='generate' 또는 'chat'에 따라 분기)
    """
    try:
        # __root__를 통해 실제 요청 객체에 접근 (Pydantic의 RootModel 또는 Union 처리 방식에 따름)
        # 만약 request가 직접 Union 타입으로 파싱된다면 request 자체가 GenerateWeeklyPlanRequest 또는 ChatWeeklyPlanRequest 인스턴스임
        # 여기서는 FastAPI가 Union을 Body로 받을 때의 동작을 고려하여 request.__root__ 확인 (사용하지 않는 경우 request 자체 사용)
        
        actual_request = request.root
        print("====================================")
        print("actual_request: ", actual_request)
        print("====================================")
        if isinstance(actual_request, GenerateWeeklyPlanRequest):
            print("--- [DEBUG] 주간 계획 생성 ---")
            # 1. 주간 계획 생성
            result = await weekly_plan_service.generate_plan(db, user_id, actual_request)
            return WeeklyPlanUnifiedResponse(
                plan_id=result["weekly_plan"].id,
                report_id=1, # Placeholder
                weekly_plan=WeeklyPlanResponse.model_validate(result["weekly_plan"]).model_dump(),
                thread_id=result["thread_id"],
                initial_llm_interaction_id=result["initial_llm_interaction_id"]
            )
            
        elif isinstance(actual_request, ChatWeeklyPlanRequest):
            print("--- [DEBUG] 주간 계획 채팅 ---")
            # 2. 주간 계획 채팅
            # 계획 존재 여부 확인
            plan = WeeklyPlanRepository.get_by_id(db, actual_request.plan_id)
            if not plan:
                raise HTTPException(status_code=404, detail="주간 계획을 찾을 수 없습니다.")
                
            response_text = await weekly_plan_service.chat_with_plan(
                db=db,
                user_id=user_id,
                plan_id=actual_request.plan_id,
                thread_id=actual_request.thread_id,
                message=actual_request.message
            )
            
            return WeeklyPlanUnifiedResponse(
                plan_id=actual_request.plan_id,
                thread_id=actual_request.thread_id,
                response=response_text
            )
            
        else:
            raise HTTPException(status_code=400, detail="잘못된 요청 타입입니다.")
            
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"요청 처리 중 오류가 발생했습니다: {str(e)}")
    
    

@router.post("/feedback", response_model=WeeklyPlanChatResponse)
async def feedback_on_plan(
    user_id: int,
    request: WeeklyPlanFeedbackRequest,
    db: Session = Depends(get_db)
):
    """
    주간 계획에 대한 구조화된 피드백 제출 및 계획 수정
    
    - **user_id**: 사용자 ID
    - **request**: 피드백 요청 데이터
    """
    try:
        response_text = await weekly_plan_service.refine_plan_with_feedback(
            db=db,
            user_id=user_id,
            request=request
        )
        return WeeklyPlanChatResponse(response=response_text)
    except Exception as e:
        # TODO: 더 구체적인 예외 처리
        raise HTTPException(status_code=500, detail=f"피드백 처리 중 오류가 발생했습니다: {str(e)}")


@router.get("/{plan_id}", response_model=WeeklyPlanResponse)
def get_weekly_plan(plan_id: int, db: Session = Depends(get_db)):
    """
    특정 주간 계획 조회
    
    - **plan_id**: 계획 ID
    """
    plan = WeeklyPlanRepository.get_by_id(db, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="주간 계획을 찾을 수 없습니다.")
    return plan


@router.get("/user/{user_id}", response_model=List[WeeklyPlanResponse])
def get_user_weekly_plans(
    user_id: int,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """
    사용자의 주간 계획 목록 조회
    
    - **user_id**: 사용자 ID
    - **limit**: 조회할 최대 개수 (기본 10)
    """
    plans = WeeklyPlanRepository.get_by_user(db, user_id, limit)
    return plans


@router.get("/user/{user_id}/week/{week_number}", response_model=WeeklyPlanResponse)
def get_weekly_plan_by_week(
    user_id: int,
    week_number: int,
    db: Session = Depends(get_db)
):
    """
    특정 주차의 계획 조회
    
    - **user_id**: 사용자 ID
    - **week_number**: 주차 번호
    """
    plan = WeeklyPlanRepository.get_by_week(db, user_id, week_number)
    if not plan:
        raise HTTPException(
            status_code=404,
            detail=f"사용자 {user_id}의 {week_number}주차 계획을 찾을 수 없습니다."
        )
    return plan


@router.patch("/{plan_id}", response_model=WeeklyPlanResponse)
def update_weekly_plan(
    plan_id: int,
    plan_update: WeeklyPlanUpdate,
    db: Session = Depends(get_db)
):
    """
    주간 계획 수정
    
    - **plan_id**: 계획 ID
    - **plan_update**: 수정할 데이터
    """
    updated_plan = WeeklyPlanRepository.update(
        db, plan_id, **plan_update.model_dump(exclude_unset=True)
    )
    if not updated_plan:
        raise HTTPException(status_code=404, detail="주간 계획을 찾을 수 없습니다.")
    return updated_plan


@router.delete("/{plan_id}")
def delete_weekly_plan(plan_id: int, db: Session = Depends(get_db)):
    """
    주간 계획 삭제
    
    - **plan_id**: 계획 ID
    """
    success = WeeklyPlanRepository.delete(db, plan_id)
    if not success:
        raise HTTPException(status_code=404, detail="주간 계획을 찾을 수 없습니다.")
    return {"message": "주간 계획이 삭제되었습니다."}
