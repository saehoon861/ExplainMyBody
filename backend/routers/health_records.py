"""
건강 기록 라우터
/api/health-records/*
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from database import get_db
from schemas.health_record import HealthRecordCreate, HealthRecordResponse
from services.health_service import HealthService
from services.ocr_service import OCRService
from repositories.health_record_repository import HealthRecordRepository
from typing import List

router = APIRouter()
health_service = HealthService()
ocr_service = OCRService()


@router.post("/", response_model=HealthRecordResponse, status_code=201)
def create_health_record(
    user_id: int,
    record_data: HealthRecordCreate,
    db: Session = Depends(get_db)
):
    """
    건강 기록 생성 (수동 입력)
    
    - **user_id**: 사용자 ID
    - **record_data**: 건강 기록 데이터
    """
    health_record = health_service.create_health_record(db, user_id, record_data)
    return health_record


@router.post("/ocr", response_model=HealthRecordResponse, status_code=201)
async def create_health_record_from_ocr(
    user_id: int,
    image: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    건강 기록 생성 (OCR을 통한 이미지 업로드)
    
    - **user_id**: 사용자 ID
    - **image**: 인바디 이미지 파일
    """
    # OCR로 데이터 추출
    ocr_data = await ocr_service.extract_inbody_data(image)
    
    # 건강 기록 생성
    record_data = HealthRecordCreate(
        measurements=ocr_data,
        source="ocr"
    )
    health_record = health_service.create_health_record(db, user_id, record_data)
    
    return health_record


@router.get("/{record_id}", response_model=HealthRecordResponse)
def get_health_record(record_id: int, db: Session = Depends(get_db)):
    """
    건강 기록 조회
    
    - **record_id**: 건강 기록 ID
    """
    health_record = HealthRecordRepository.get_by_id(db, record_id)
    if not health_record:
        raise HTTPException(status_code=404, detail="건강 기록을 찾을 수 없습니다.")
    return health_record


@router.get("/user/{user_id}", response_model=List[HealthRecordResponse])
def get_user_health_records(
    user_id: int,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """
    사용자의 건강 기록 목록 조회
    
    - **user_id**: 사용자 ID
    - **limit**: 조회할 최대 개수
    """
    health_records = HealthRecordRepository.get_by_user(db, user_id, limit=limit)
    return health_records


@router.get("/user/{user_id}/latest", response_model=HealthRecordResponse)
def get_latest_health_record(user_id: int, db: Session = Depends(get_db)):
    """
    사용자의 가장 최신 건강 기록 조회
    
    - **user_id**: 사용자 ID
    """
    health_record = HealthRecordRepository.get_latest(db, user_id)
    if not health_record:
        raise HTTPException(status_code=404, detail="건강 기록을 찾을 수 없습니다.")
    return health_record
