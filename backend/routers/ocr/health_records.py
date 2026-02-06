"""
건강 기록 라우터
/api/health-records/*
======================
OCR과 검증을 거쳐서 인바디 데이터를 DB에 저장하고 체형 분석을 수행하는 엔드포인트
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from database import get_db
from schemas.common import HealthRecordCreate, HealthRecordResponse
from schemas.llm import StatusAnalysisResponse
from schemas.inbody import InBodyData
from schemas.body_type import BodyTypeAnalysisInput
from services.common.health_service import HealthService
from services.llm.llm_service import LLMService
from services.ocr.ocr_service import OCRService
from services.ocr.body_type_service import BodyTypeService
from repositories.common.health_record_repository import HealthRecordRepository
from typing import List
from pydantic import ValidationError
from exceptions import (
    OCREngineNotInitializedError,
    OCRExtractionFailedError,
    OCRProcessingError
)

router = APIRouter()

# ⚠️ LLMService를 여기서 생성하지 않음 - AppState에서 전역 인스턴스 사용 (MemorySaver 공유)
def get_llm_service():
    """Dependency to get shared LLM service from app state"""
    from app_state import AppState
    if AppState.llm_service is None:
        raise HTTPException(status_code=503, detail="LLM 서비스가 초기화되지 않았습니다.")
    return AppState.llm_service

def get_health_service(llm_service: LLMService = Depends(get_llm_service)):
    """Dependency to get health service with shared LLM service"""
    return HealthService(llm_service=llm_service)

body_type_service = BodyTypeService()


def get_ocr_service():
    """
    Dependency to get OCR service from app state
    
    OCR 엔진은 서버 시작 시 백그라운드에서 로딩됩니다.
    아직 로딩 중이면 503 에러를 반환합니다.
    """
    from app_state import AppState
    
    if AppState.ocr_service is None:
        raise HTTPException(
            status_code=503,
            detail="OCR 엔진이 아직 로딩 중입니다. 잠시 후 다시 시도해주세요."
        )
    return AppState.ocr_service


@router.post("/ocr/extract", status_code=200)
async def extract_inbody_from_image(
    image: UploadFile = File(...),
    ocr_service: OCRService = Depends(get_ocr_service)
):
    """
    Step 1: 인바디 이미지에서 데이터 추출 (OCR만 수행, 검증 없음)
    
    - OCR로 추출한 원시 데이터를 반환
    - Pydantic 검증 없음 (빈 값, 이상치 값 포함 가능)
    - 프론트엔드에서 사용자가 데이터를 확인하고 수정
    
    Flow:
    1. OCR 수행 → dict 반환
    2. 프론트엔드에서 사용자에게 보여줌
    3. 사용자가 빈 칸 채우고 이상한 값 수정
    4. 모든 필드가 올바르게 입력되면 "저장" 버튼 활성화
    5. /ocr/validate로 전송
    
    Returns:
        {
            "data": dict,  # OCR 원시 데이터 (검증 없음)
            "message": str
        }
        
    Raises:
        HTTPException 503: OCR 엔진이 아직 로딩 중
    """
    try:
        # ⚠️ 중요: image.file (BinaryIO)와 image.filename을 서비스에 전달
        raw_data = await ocr_service.extract_inbody_data(image.file, image.filename)
    
        return {
            "data": raw_data,
            "message": "OCR 추출 완료. 데이터를 확인하고 수정해주세요."
        }
    
    except OCREngineNotInitializedError as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    except OCRExtractionFailedError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    except OCRProcessingError as e:
        raise HTTPException(status_code=500, detail=str(e))



@router.post("/ocr/validate", response_model=HealthRecordResponse, status_code=201)
async def validate_and_save_inbody(
    user_id: int,
    inbody_data: dict,  # 프론트엔드에서 사용자가 검증/수정한 데이터 (dict로 받음)
    db: Session = Depends(get_db),
    health_service: HealthService = Depends(get_health_service)
):
    """
    Step 2: 사용자 검증 완료 후 Pydantic 검증 → DB 저장 및 체형 분석
    
    ⚠️ 프론트엔드 검증 필수:
    - 미입력 값이 있으면 저장 버튼 비활성화
    - 이상치 값 (예: 신장 500cm)은 프론트에서 차단
    - 백엔드는 Pydantic으로 최종 검증
    
    ⚠️ 검증 실패 시:
    - 422 에러 반환
    - 어떤 필드가 문제인지 상세 에러 메시지 포함
    - 프론트엔드는 사용자에게 다시 수정하도록 안내
    
    Flow:
    1. 프론트에서 받은 dict를 InBodyData Pydantic 모델로 검증
       - 검증 실패 시 422 에러 + 상세 에러 반환 (프론트가 다시 수정)
       - 검증 성공 시 다음 단계 진행
    2. 체형 분석 수행 (일부 필드만 사용)
    3. 인바디 데이터 + 체형 분석 결과를 measurements JSONB에 통합 저장
    4. body_type1, body_type2 별도 컬럼에도 저장 (조회 편의용)
    
    Args:
        user_id: 사용자 ID
        inbody_data: 프론트엔드에서 사용자가 검증/수정한 인바디 데이터 (dict)
        
    Returns:
        HealthRecordResponse: 저장된 건강 기록 (체형 분석 결과 포함)
        
    Raises:
        HTTPException 422: Pydantic 검증 실패 (필드 누락, 타입 오류, 이상치 등)
    """
    # Step 1: Pydantic 검증 (타입, 범위 체크)
    try:
        validated_inbody_data = InBodyData(**inbody_data)
    except ValidationError as e:
        # 검증 실패 → 프론트엔드에 상세 에러 반환
        raise HTTPException(
            status_code=422,
            detail={
                "message": "데이터 검증 실패. 입력값을 다시 확인해주세요.",
                "errors": e.errors()  # 어떤 필드가 문제인지 상세 정보
            }
        )
    
    # Step 1.5: null 값 체크 (OCR 사용 시 모든 필드 필수)
    null_fields = validated_inbody_data.get_null_fields()
    if null_fields:
        # 빈 필드가 있으면 저장 불가
        raise HTTPException(
            status_code=422,
            detail={
                "message": "OCR로 추출한 데이터는 모든 필드를 입력해야 합니다.",
                "null_fields": null_fields
            }
        )

    
    # Step 2: 체형 분석 수행 (저장 전에 먼저 분석)
    body_type1 = None
    body_type2 = None
    
    try:
        # InBodyData에서 체형 분석에 필요한 필드만 추출하여 입력 생성
        body_type_input = BodyTypeAnalysisInput.from_inbody_data(
            inbody=validated_inbody_data,
            muscle_seg=validated_inbody_data.부위별근육분석.model_dump(),
            fat_seg=validated_inbody_data.부위별체지방분석.model_dump()
        )
        
        # 체형 분석 실행 (stage2, stage3 결과 반환)
        body_type_result = body_type_service.get_full_analysis(body_type_input)
        
        if body_type_result:
            body_type1 = body_type_result.stage2  # 1차 체형 분류
            body_type2 = body_type_result.stage3  # 2차 체형 분류
            print(f"✅ 체형 분석 완료: {body_type1}, {body_type2}")
    
    except ValidationError as e:
        # 체형 분석 필수 필드 누락 → 체형 분석 없이 진행
        print(f"⚠️ 체형 분석 필수 필드 누락, 인바디 데이터만 저장: {e}")
    
    except Exception as e:
        # 체형 분석 실패 → 체형 분석 없이 진행
        print(f"⚠️ 체형 분석 실패, 인바디 데이터만 저장: {e}")
    
    # Step 3: measurements JSONB에 체형 분석 결과 포함
    measurements_with_body_type = validated_inbody_data.model_dump(exclude_none=True)
    
    # 체형 분석 결과를 measurements JSONB 끝에 추가
    if body_type1 is not None:
        measurements_with_body_type["body_type1"] = body_type1
    if body_type2 is not None:
        measurements_with_body_type["body_type2"] = body_type2
    
    # Step 4: DB 저장
    record_data = HealthRecordCreate(
        measurements=measurements_with_body_type,
        source="ocr"
    )
    health_record = health_service.create_health_record(db, user_id, record_data)
    
    # Step 5: body_type 별도 컬럼에도 저장 (조회 편의용)
    if body_type1 is not None or body_type2 is not None:
        health_record.body_type1 = body_type1
        health_record.body_type2 = body_type2
        db.commit()
        db.refresh(health_record)
    
    return health_record



@router.post("/", response_model=HealthRecordResponse, status_code=201)
def create_health_record(
    user_id: int,
    record_data: HealthRecordCreate,
    db: Session = Depends(get_db),
    health_service: HealthService = Depends(get_health_service)
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


@router.get("/{record_id}/analysis/prepare", response_model=StatusAnalysisResponse)
def prepare_status_analysis(
    user_id: int,
    record_id: int,
    db: Session = Depends(get_db),
    health_service: HealthService = Depends(get_health_service)
):
    """
    LLM1: 건강 기록 분석용 input 데이터 준비 (status_analysis)
    - 프론트엔드에서 선택한 건강 기록의 모든 데이터를 반환
    - 프론트엔드에서 이 데이터를 LLM API에 전달하여 분석 요청

    Args:
        user_id: 사용자 ID
        record_id: 선택된 건강 기록 ID

    Returns:
        StatusAnalysisResponse: LLM에 전달할 input 데이터
    """
    result = health_service.prepare_status_analysis(db, user_id, record_id)
    if not result:
        raise HTTPException(status_code=404, detail="건강 기록을 찾을 수 없습니다.")
    return result
