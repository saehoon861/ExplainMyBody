"""
목표 라우터
/api/goals/*
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from schemas.user_goal import UserGoalCreate, UserGoalResponse, UserGoalUpdate
from repositories.user_goal_repository import UserGoalRepository
from services.llm_service import LLMService
from repositories.health_record_repository import HealthRecordRepository
from repositories.analysis_report_repository import AnalysisReportRepository
from typing import List
from datetime import datetime

router = APIRouter()
llm_service = LLMService()


@router.post("/", response_model=UserGoalResponse, status_code=201)
def create_goal(
    user_id: int,
    goal_data: UserGoalCreate,
    db: Session = Depends(get_db)
):
    """
    사용자 목표 생성
    
    - **user_id**: 사용자 ID
    - **goal_data**: 목표 데이터
    """
    new_goal = UserGoalRepository.create(db, user_id, goal_data)
    return new_goal


@router.post("/{goal_id}/generate-plan", response_model=UserGoalResponse)
async def generate_weekly_plan(
    user_id: int,
    goal_id: int,
    db: Session = Depends(get_db)
):
    """
    주간 계획서 생성 (LLM 사용)
    
    - **user_id**: 사용자 ID
    - **goal_id**: 목표 ID
    """
    # 목표 조회
    goal = UserGoalRepository.get_by_id(db, goal_id)
    if not goal or goal.user_id != user_id:
        raise HTTPException(status_code=404, detail="목표를 찾을 수 없습니다.")
    
    # 최신 건강 기록 조회
    latest_record = HealthRecordRepository.get_latest(db, user_id)
    if not latest_record:
        raise HTTPException(status_code=404, detail="건강 기록이 없습니다.")
    
    # 분석 결과 조회
    analysis_report = AnalysisReportRepository.get_by_record_id(db, latest_record.id)
    analysis_text = analysis_report.llm_output if analysis_report else "분석 결과 없음"
    
    # LLM으로 주간 계획 생성
    weekly_plan = await llm_service.generate_weekly_plan(
        latest_record.measurements,
        latest_record.body_type,
        analysis_text,
        goal.goal_description or goal.goal_type or "건강 개선"
    )
    
    # 목표에 주간 계획 저장
    updated_goal = UserGoalRepository.update(db, goal_id, weekly_plan=weekly_plan)
    return updated_goal


@router.get("/{goal_id}", response_model=UserGoalResponse)
def get_goal(goal_id: int, db: Session = Depends(get_db)):
    """
    목표 조회
    
    - **goal_id**: 목표 ID
    """
    goal = UserGoalRepository.get_by_id(db, goal_id)
    if not goal:
        raise HTTPException(status_code=404, detail="목표를 찾을 수 없습니다.")
    return goal


@router.get("/user/{user_id}/active", response_model=List[UserGoalResponse])
def get_active_goals(user_id: int, db: Session = Depends(get_db)):
    """
    사용자의 활성 목표 조회
    
    - **user_id**: 사용자 ID
    """
    active_goals = UserGoalRepository.get_active_goals(db, user_id)
    return active_goals


@router.get("/user/{user_id}", response_model=List[UserGoalResponse])
def get_all_goals(user_id: int, db: Session = Depends(get_db)):
    """
    사용자의 모든 목표 조회
    
    - **user_id**: 사용자 ID
    """
    all_goals = UserGoalRepository.get_all_goals(db, user_id)
    return all_goals


@router.patch("/{goal_id}", response_model=UserGoalResponse)
def update_goal(
    goal_id: int,
    goal_update: UserGoalUpdate,
    db: Session = Depends(get_db)
):
    """
    목표 수정
    
    - **goal_id**: 목표 ID
    - **goal_update**: 수정할 데이터
    """
    updated_goal = UserGoalRepository.update(
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
    success = UserGoalRepository.delete(db, goal_id)
    if not success:
        raise HTTPException(status_code=404, detail="목표를 찾을 수 없습니다.")
    return {"message": "목표가 삭제되었습니다."}


@router.post("/{goal_id}/complete", response_model=UserGoalResponse)
def complete_goal(goal_id: int, db: Session = Depends(get_db)):
    """
    목표 완료 처리
    
    - **goal_id**: 목표 ID
    """
    updated_goal = UserGoalRepository.update(db, goal_id, ended_at=datetime.now())
    if not updated_goal:
        raise HTTPException(status_code=404, detail="목표를 찾을 수 없습니다.")
    return updated_goal
