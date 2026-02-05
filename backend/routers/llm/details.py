"""
User Detail Router (Details)
/api/details/*
"""

from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from database import get_db
from schemas.llm import UserDetailCreate, UserDetailResponse, UserDetailUpdate, GoalPlanRequest, GoalPlanPrepareResponse
from repositories.llm.user_detail_repository import UserDetailRepository
from services.llm.llm_service import LLMService
from services.common.health_service import HealthService
from typing import List, Optional
from datetime import datetime

router = APIRouter()
# health_service = HealthService()
llm_service = LLMService()
health_service = HealthService(llm_service=llm_service)

# ============================================================================
# Core / Create
# ============================================================================

@router.post("/", response_model=UserDetailResponse, status_code=201)
def create_detail(
    user_id: int,
    detail_data: UserDetailCreate,
    db: Session = Depends(get_db)
):
    """
    사용자 상세정보(목표 포함) 생성
    
    - **user_id**: 사용자 ID
    - **detail_data**: 생성할 데이터
    """
    new_detail = UserDetailRepository.create(db, user_id, detail_data)
    return new_detail

@router.post("/plan/prepare", response_model=GoalPlanPrepareResponse)
def prepare_goal_plan(
    user_id: int,
    request: GoalPlanRequest,
    db: Session = Depends(get_db)
):
    """
    LLM2: 주간 계획서 생성용 input 데이터 준비
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

# ============================================================================
# Full Access (Details + Goal)
# ============================================================================

@router.get("/user/{user_id}/active", response_model=List[UserDetailResponse])
def get_active_details(user_id: int, db: Session = Depends(get_db)):
    """
    사용자의 활성 상세정보 전체 조회
    """
    return UserDetailRepository.get_active_details(db, user_id)

@router.get("/user/{user_id}", response_model=List[UserDetailResponse])
def get_all_details(user_id: int, db: Session = Depends(get_db)):
    """
    사용자의 모든 상세정보 조회 (히스토리 포함)
    """
    return UserDetailRepository.get_all_details(db, user_id)

@router.get("/{detail_id}", response_model=UserDetailResponse)
def get_detail(detail_id: int, db: Session = Depends(get_db)):
    """
    특정 상세정보 조회 (전체 필드)
    """
    detail = UserDetailRepository.get_by_id(db, detail_id)
    if not detail:
        raise HTTPException(status_code=404, detail="상세정보를 찾을 수 없습니다.")
    return detail

@router.patch("/{detail_id}", response_model=UserDetailResponse)
def update_detail(
    detail_id: int,
    detail_update: UserDetailUpdate,
    db: Session = Depends(get_db)
):
    """
    상세정보 전체 수정 (모든 필드 허용)
    """
    updated_detail = UserDetailRepository.update(
        db, detail_id, **detail_update.model_dump(exclude_unset=True)
    )
    if not updated_detail:
        raise HTTPException(status_code=404, detail="상세정보를 찾을 수 없습니다.")
    return updated_detail

@router.delete("/{detail_id}")
def delete_detail(detail_id: int, db: Session = Depends(get_db)):
    """
    상세정보 삭제 (Goal 포함 전체 삭제)
    """
    success = UserDetailRepository.delete(db, detail_id)
    if not success:
        raise HTTPException(status_code=404, detail="상세정보를 찾을 수 없습니다.")
    return {"message": "상세정보가 삭제되었습니다."}

@router.post("/{detail_id}/complete", response_model=UserDetailResponse)
def complete_detail(detail_id: int, db: Session = Depends(get_db)):
    """
    상세정보(목표) 완료 처리
    """
    updated_detail = UserDetailRepository.update(db, detail_id, ended_at=datetime.now())
    if not updated_detail:
        raise HTTPException(status_code=404, detail="상세정보를 찾을 수 없습니다.")
    return updated_detail

# ============================================================================
# Goal Only Access
# ============================================================================

@router.get("/{detail_id}/goal", response_model=UserDetailResponse)
def get_detail_goal_only(detail_id: int, db: Session = Depends(get_db)):
    """
    목표 정보만 조회 (응답은 전체 모델이지만, 프론트엔드에서 목표 필드만 사용)
    """
    detail = UserDetailRepository.get_by_id(db, detail_id)
    if not detail:
        raise HTTPException(status_code=404, detail="상세정보를 찾을 수 없습니다.")
    return detail

@router.patch("/{detail_id}/goal", response_model=UserDetailResponse)
def update_detail_goal_only(
    detail_id: int,
    detail_update: UserDetailUpdate,
    db: Session = Depends(get_db)
):
    """
    목표 정보만 수정
    
    **Validation**:
    - `preferences`, `health_specifics` 등 Info 관련 필드가 포함되면 400 에러를 발생시킵니다.
    - `goal_type`, `goal_description` 만 허용됩니다.
    """
    update_data = detail_update.model_dump(exclude_unset=True)
    
    # 검증: Info 관련 필드 존재 여부 확인
    forbidden_fields = ['preferences', 'health_specifics']
    for field in forbidden_fields:
        if field in update_data and update_data[field] is not None:
             raise HTTPException(
                status_code=400, 
                detail=f"Goal 수정 엔드포인트에서는 '{field}' 필드를 수정할 수 없습니다. /info 엔드포인트를 사용하세요."
            )

    updated_detail = UserDetailRepository.update(db, detail_id, **update_data)
    if not updated_detail:
        raise HTTPException(status_code=404, detail="상세정보를 찾을 수 없습니다.")
    return updated_detail

@router.delete("/{detail_id}/goal")
def delete_detail_goal(detail_id: int, db: Session = Depends(get_db)):
    """
    목표 삭제 (데이터 구조상 전체 상세정보 삭제와 동일)
    """
    return delete_detail(detail_id, db)

# ============================================================================
# Info Only Access (Preferences, Health Specifics)
# ============================================================================

@router.get("/{detail_id}/info", response_model=UserDetailResponse)
def get_detail_info_only(detail_id: int, db: Session = Depends(get_db)):
    """
    상세 정보(선호도/특이사항)만 조회
    """
    detail = UserDetailRepository.get_by_id(db, detail_id)
    if not detail:
        raise HTTPException(status_code=404, detail="상세정보를 찾을 수 없습니다.")
    return detail

@router.patch("/{detail_id}/info", response_model=UserDetailResponse)
def update_detail_info_only(
    detail_id: int,
    detail_update: UserDetailUpdate,
    db: Session = Depends(get_db)
):
    """
    상세 정보(선호도/특이사항)만 수정
    
    **Validation**:
    - `goal_type`, `goal_description` 등 Goal 관련 필드가 포함되면 400 에러를 발생시킵니다.
    - `preferences`, `health_specifics` 만 허용됩니다.
    """
    update_data = detail_update.model_dump(exclude_unset=True)
    
    # 검증: Goal 관련 필드 존재 여부 확인
    forbidden_fields = ['goal_type', 'goal_description']
    for field in forbidden_fields:
        if field in update_data and update_data[field] is not None:
            raise HTTPException(
                status_code=400, 
                detail=f"Info 수정 엔드포인트에서는 '{field}' 필드를 수정할 수 없습니다. /goal 엔드포인트를 사용하세요."
            )
            
    updated_detail = UserDetailRepository.update(db, detail_id, **update_data)
    if not updated_detail:
        raise HTTPException(status_code=404, detail="상세정보를 찾을 수 없습니다.")
    return updated_detail
