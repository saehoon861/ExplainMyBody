"""
건강 기록 라우터
/api/health-records/*
======================
OCR과 검증을 거쳐서 인바디 데이터를 DB에 저장하고 체형 분석을 수행하는 엔드포인트
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from database import get_db
from schemas.health_record import HealthRecordCreate, HealthRecordResponse
from schemas.inbody import InBodyData
from schemas.body_type import BodyTypeAnalysisInput
from services.health_service import HealthService
from services.ocr_service import OCRService
from services.body_type_service import BodyTypeService
from repositories.health_record_repository import HealthRecordRepository
from typing import List
from pydantic import ValidationError

router = APIRouter()
health_service = HealthService()
ocr_service = OCRService()
body_type_service = BodyTypeService()


@router.post("/ocr/extract", response_model=InBodyData, status_code=200)
async def extract_inbody_from_image(
    image: UploadFile = File(...)
):
    """
    Step 1: 인바디 이미지에서 데이터 추출 (OCR만 수행)
    
    - 사용자에게 추출된 데이터를 보여주기 위한 엔드포인트
    - DB 저장 없음
    - 사용자가 데이터를 확인하고 수정할 수 있도록 반환
    
    Returns:
        InBodyData: OCR로 추출된 인바디 데이터 (Pydantic 검증 완료)
    """
    inbody_data = await ocr_service.extract_inbody_data(image)
    return inbody_data


@router.post("/ocr/validate", response_model=HealthRecordResponse, status_code=201)
async def validate_and_save_inbody(
    user_id: int,
    inbody_data: InBodyData,  # 사용자가 검증/수정한 데이터
    db: Session = Depends(get_db)
):
    """
    Step 2: 사용자 검증 완료 후 DB 저장 및 체형 분석
    
    Flow:
    1. 사용자가 수정한 InBodyData를 받음 (Pydantic이 이상치 검증)
    2. 인바디 데이터를 DB에 먼저 저장 (body_type=None)
    3. 체형 분석 시도
    4. 성공 시 body_type 필드 업데이트
    5. 실패해도 인바디 데이터는 보존됨
    
    Args:
        user_id: 사용자 ID
        inbody_data: 사용자가 검증/수정한 인바디 데이터
        
    Returns:
        HealthRecordResponse: 저장된 건강 기록 (체형 분석 결과 포함)
    """
    # 1. 인바디 데이터를 DB에 저장 (body_type은 None)
    record_data = HealthRecordCreate(
        measurements=inbody_data.model_dump(exclude_none=True),
        source="ocr"
    )
    health_record = health_service.create_health_record(db, user_id, record_data)
    
    # 2. 체형 분석 시도 (필수 필드가 있는 경우만)
    try:
        # InBodyData에서 체형 분석 입력 생성
        body_type_input = BodyTypeAnalysisInput.from_inbody_data(inbody_data)
        
        # 체형 분석 실행
        body_type_result = body_type_service.get_full_analysis(body_type_input)
        
        if body_type_result:
            # 3. 체형 분석 성공 → DB 업데이트
            health_record.body_type = body_type_result.stage2
            db.commit()
            db.refresh(health_record)
    
    except ValidationError as e:
        # 체형 분석 필수 필드 누락 → 건너뛰기
        print(f"⚠️  체형 분석 필수 필드 누락, 인바디 데이터만 저장: {e}")
    
    except Exception as e:
        # 체형 분석 실패 → 건너뛰기
        print(f"⚠️  체형 분석 실패, 인바디 데이터만 저장: {e}")
    
    return health_record


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
