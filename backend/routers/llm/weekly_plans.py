"""
주간 계획 라우터
/api/weekly-plans/*
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from schemas.llm import WeeklyPlanCreate, WeeklyPlanResponse, WeeklyPlanUpdate
from repositories.llm.weekly_plan_repository import WeeklyPlanRepository
from typing import List
from datetime import date

router = APIRouter()


@router.post("/", response_model=WeeklyPlanResponse, status_code=201)
def create_weekly_plan(
    user_id: int,
    plan_data: WeeklyPlanCreate,
    db: Session = Depends(get_db)
):
    """
    주간 계획 생성
    
    - **user_id**: 사용자 ID
    - **plan_data**: 주간 계획 데이터
    """
    new_plan = WeeklyPlanRepository.create(db, user_id, plan_data)
    return new_plan


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
