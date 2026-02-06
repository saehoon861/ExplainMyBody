"""
분석 라우터
/api/analysis/*
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from schemas.llm import AnalysisReportResponse, AnalysisChatRequest, AnalysisChatResponse
from services.common.health_service import HealthService
from services.llm.llm_service import LLMService
from services.llm.parse_utils import split_analysis_response
from repositories.llm.analysis_report_repository import AnalysisReportRepository
from typing import List
# Note: 현재는 Service가 None을 반환하므로 라우터에서 체크
# 향후 Service 레이어 개선 시 아래 예외들을 사용할 수 있음
# from exceptions import HealthRecordNotFoundError, AnalysisReportNotFoundError

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


def _parse_analysis_report(report) -> AnalysisReportResponse:
    """
    분석 리포트에 summary/content 파싱 추가
    기존 분석 결과 조회 시에도 파싱된 데이터를 제공하기 위한 헬퍼 함수
    """
    response = AnalysisReportResponse.model_validate(report)
    if response.llm_output:
        parsed = split_analysis_response(response.llm_output)
        response.summary = parsed["summary"]
        response.content = parsed["content"]
    return response



# record_id에 해당하는 건강 기록에 대한 분석 기록 조회
# 해당 기록이 이미 존재한다면
# DB에서 조회하여 반환
# 그렇지 않다면
# LLM을 호출하여 분석 결과를 생성하고
# DB에 저장한 후 반환 하는 방식으로 수정필요 #fixme
@router.post("/{record_id}", response_model=AnalysisReportResponse, status_code=201)
async def analyze_health_record(
    user_id: int,
    record_id: int,
    db: Session = Depends(get_db),
    health_service: HealthService = Depends(get_health_service)
):
    """
    건강 기록 분석 (LLM 사용)

    - **user_id**: 사용자 ID
    - **record_id**: 건강 기록 ID
    """
    analysis_report = await health_service.analyze_health_record(db, user_id, record_id)
    if not analysis_report:
        raise HTTPException(status_code=404, detail="건강 기록을 찾을 수 없습니다.")
    return analysis_report


@router.get("/{report_id}", response_model=AnalysisReportResponse)
def get_analysis_report(report_id: int, db: Session = Depends(get_db)):
    """
    분석 리포트 조회
    
    - **report_id**: 리포트 ID
    """
    analysis_report = AnalysisReportRepository.get_by_id(db, report_id)
    if not analysis_report:
        raise HTTPException(status_code=404, detail="분석 리포트를 찾을 수 없습니다.")
    return _parse_analysis_report(analysis_report)


@router.get("/record/{record_id}", response_model=AnalysisReportResponse)
def get_analysis_by_record(record_id: int, db: Session = Depends(get_db)):
    """
    건강 기록에 대한 분석 리포트 조회
    
    - **record_id**: 건강 기록 ID
    """
    analysis_report = AnalysisReportRepository.get_by_record_id(db, record_id)
    if not analysis_report:
        raise HTTPException(status_code=404, detail="분석 리포트를 찾을 수 없습니다.")
    return _parse_analysis_report(analysis_report)


@router.get("/user/{user_id}", response_model=List[AnalysisReportResponse])
def get_user_analysis_reports(
    user_id: int,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """
    사용자의 분석 리포트 목록 조회
    
    - **user_id**: 사용자 ID
    - **limit**: 조회할 최대 개수
    """
    analysis_reports = AnalysisReportRepository.get_by_user(db, user_id, limit=limit)
    return [_parse_analysis_report(report) for report in analysis_reports]


@router.post("/{report_id}/chat", response_model=AnalysisChatResponse)
async def chat_about_report(
    report_id: int,
    chat_request: AnalysisChatRequest,
    db: Session = Depends(get_db),
    llm_service: LLMService = Depends(get_llm_service)
):
    """
    분석 결과에 대해 AI와 대화 (휴먼 피드백)

    - **report_id**: 분석 리포트 ID
    - **message**: 사용자 질문
    """
    print(f"[DEBUG][chat_router] report_id={report_id}, request body: message='{chat_request.message[:80]}', thread_id={chat_request.thread_id!r}")

    # 폴백용: DB에서 원본 보고서 텍스트 조회 (체크포인트 소실 시 대화 맥락으로 사용)
    report = AnalysisReportRepository.get_by_id(db, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="분석 리포트를 찾을 수 없습니다.")
    print(f"[DEBUG][chat_router] DB report found, thread_id in DB report: {getattr(report, 'thread_id', 'ATTR_NOT_EXIST')!r}")

    response_text = await llm_service.chat_with_analysis(
        thread_id=chat_request.thread_id,
        user_message=chat_request.message,
        report_context=report.llm_output
    )

    return {"reply": response_text, "thread_id": chat_request.thread_id or ""}
