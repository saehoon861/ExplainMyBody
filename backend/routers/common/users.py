"""
사용자 라우터
/api/users/*
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from schemas.common import UserResponse
from repositories.common.user_repository import UserRepository
from typing import List

router = APIRouter()


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    """
    사용자 정보 조회
    
    - **user_id**: 사용자 ID
    """
    user = UserRepository.get_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    return user


@router.get("/", response_model=List[UserResponse])
def get_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    사용자 목록 조회
    
    - **skip**: 건너뛸 개수
    - **limit**: 조회할 최대 개수
    """
    users = UserRepository.get_all(db, skip=skip, limit=limit)
    return users


@router.get("/{user_id}/statistics")
def get_user_statistics(user_id: int, db: Session = Depends(get_db)):
    """
    사용자 통계 조회
    
    - **user_id**: 사용자 ID
    """
    from repositories.health_record_repository import HealthRecordRepository
    from repositories.llm.analysis_report_repository import AnalysisReportRepository
    
    user = UserRepository.get_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    
    total_records = len(HealthRecordRepository.get_by_user(db, user_id, limit=1000))
    total_reports = len(AnalysisReportRepository.get_by_user(db, user_id, limit=1000))
    
    return {
        "user_id": user_id,
        "total_records": total_records,
        "total_reports": total_reports
    }

from repositories.llm.user_detail_repository import UserDetailRepository
from repositories.common.health_record_repository import HealthRecordRepository
from schemas.llm import UserDetailCreate, UserGoalUpdateRequest
import json

@router.put("/{user_id}/goal", response_model=UserResponse)
def update_user_goal(
    user_id: int, 
    goal_data: UserGoalUpdateRequest, 
    db: Session = Depends(get_db)
):
    """
    사용자 목표 및 시작 체중 수정
    """
    user = UserRepository.get_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

    # 1. Update Goal (UserDetail) -> start_weight and target_weight stored in JSON
    # Find active detail
    active_details = UserDetailRepository.get_active_details(db, user_id)
    active_detail = active_details[0] if active_details else None

    # Pack description with start_weight and target_weight
    combined_description = {
        "start_weight": goal_data.start_weight,
        "target_weight": goal_data.target_weight,
        "description": goal_data.goal_description
    }
    packed_description = json.dumps(combined_description, ensure_ascii=False)

    goal_type_str = ", ".join(goal_data.goal_type) if goal_data.goal_type else None

    if active_detail:
        # Update existing
        UserDetailRepository.update(
            db,
            active_detail.id,
            goal_type=goal_type_str,
            goal_description=packed_description
        )
    else:
        # Create new if not exists
        new_detail = UserDetailCreate(
            goal_type=goal_type_str,
            goal_description=packed_description,
            is_active=1
        )
        UserDetailRepository.create(db, user_id, new_detail)

    # Force reload of relationship to ensure active_detail property picks up the change
    db.expire(user, ['user_details'])
    db.refresh(user)
    
    return user
