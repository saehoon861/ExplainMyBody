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
    from repositories.analysis_report_repository import AnalysisReportRepository
    
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
