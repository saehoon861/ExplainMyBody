"""
목표 라우터
/api/goals/*
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from schemas.llm import UserDetailCreate, UserDetailResponse, UserDetailUpdate, GoalPlanRequest, GoalPlanResponse
from repositories.llm.user_detail_repository import UserDetailRepository
from services.llm.llm_service import LLMService
from services.common.health_service import HealthService
from repositories.common.health_record_repository import HealthRecordRepository
from repositories.llm.analysis_report_repository import AnalysisReportRepository
from typing import List
from datetime import datetime

router = APIRouter()
llm_service = LLMService()
health_service = HealthService()


@router.post("/", response_model=UserDetailResponse, status_code=201)
def create_goal(
    user_id: int,
    goal_data: UserDetailCreate,
    db: Session = Depends(get_db)
):
    """
    사용자 목표/상세정보 생성

    - **user_id**: 사용자 ID
    - **goal_data**: 목표 데이터
    """
    new_goal = UserDetailRepository.create(db, user_id, goal_data)
    return new_goal


@router.post("/plan/prepare", response_model=GoalPlanResponse)
def prepare_goal_plan(
    user_id: int,
    request: GoalPlanRequest,
    db: Session = Depends(get_db)
):
    """
    LLM2: 주간 계획서 생성용 input 데이터 준비 (goal_plan)

    - 사용자 요구사항 + 선택된 건강 기록 + status_analysis 결과를 반환
    - 프론트엔드에서 이 데이터를 LLM API에 전달하여 주간 계획서 생성 요청

    Args:
        user_id: 사용자 ID
        request: GoalPlanRequest (record_id, user_goal_type, user_goal_description)

    Returns:
        GoalPlanResponse: LLM에 전달할 input 데이터
    """
    result = health_service.prepare_goal_plan(
        db=db,
        user_id=user_id,
        record_id=request.record_id,
        user_goal_type=request.user_goal_type,
        user_goal_description=request.user_goal_description
    )
    if not result:
        raise HTTPException(status_code=404, detail="건강 기록을 찾을 수 없습니다.")
    return result


@router.get("/{goal_id}", response_model=UserDetailResponse)
def get_goal(goal_id: int, db: Session = Depends(get_db)):
    """
    목표 조회
    
    - **goal_id**: 목표 ID
    """
    goal = UserDetailRepository.get_by_id(db, goal_id)
    if not goal:
        raise HTTPException(status_code=404, detail="목표를 찾을 수 없습니다.")
    return goal


@router.get("/user/{user_id}/active", response_model=List[UserDetailResponse])
def get_active_goals(user_id: int, db: Session = Depends(get_db)):
    """
    사용자의 활성 목표 조회
    
    - **user_id**: 사용자 ID
    """
    active_goals = UserDetailRepository.get_active_details(db, user_id)
    return active_goals


@router.get("/user/{user_id}", response_model=List[UserDetailResponse])
def get_all_goals(user_id: int, db: Session = Depends(get_db)):
    """
    사용자의 모든 목표 조회
    
    - **user_id**: 사용자 ID
    """
    all_goals = UserDetailRepository.get_all_details(db, user_id)
    return all_goals


@router.patch("/{goal_id}", response_model=UserDetailResponse)
def update_goal(
    goal_id: int,
    goal_update: UserDetailUpdate,
    db: Session = Depends(get_db)
):
    """
    목표 수정
    
    - **goal_id**: 목표 ID
    - **goal_update**: 수정할 데이터
    """
    updated_goal = UserDetailRepository.update(
        db, goal_id, **goal_update.model_dump(exclude_unset=True)
    )
    if not updated_goal:
        raise HTTPException(status_code=404, detail="목표를 찾을 수 없습니다.")
    return updated_goal


@router.delete("/{goal_id}")
def delete_goal(goal_id: int, db: Session = Depends(get_db)):
    """
    목표 삭제
    
    - **goal_id**: 목표 ID
    """
    success = UserDetailRepository.delete(db, goal_id)
    if not success:
        raise HTTPException(status_code=404, detail="목표를 찾을 수 없습니다.")
    return {"message": "목표가 삭제되었습니다."}


@router.post("/{goal_id}/complete", response_model=UserDetailResponse)
def complete_goal(goal_id: int, db: Session = Depends(get_db)):
    """
    목표 완료 처리
    
    - **goal_id**: 목표 ID
    """
    updated_goal = UserDetailRepository.update(db, goal_id, ended_at=datetime.now())
    if not updated_goal:
        raise HTTPException(status_code=404, detail="목표를 찾을 수 없습니다.")
    return updated_goal
