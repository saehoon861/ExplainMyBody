"""
분석 라우터 (RAG 버전)
/api/analysis-rag/*

RAG 기능이 추가된 분석 엔드포인트
- 논문 DB 기반 과학적 근거 제공
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from schemas.llm import AnalysisReportResponse, AnalysisChatRequest, AnalysisChatResponse
from services.common.health_service_rag import HealthServiceRAG
from services.llm.llm_rag.llm_service_rag import LLMServiceRAG
from services.llm.parse_utils import split_analysis_response
from repositories.llm.analysis_report_repository import AnalysisReportRepository
from typing import List

router = APIRouter()
health_service_rag = HealthServiceRAG()
llm_service_rag = LLMServiceRAG(model_version="gpt-4o-mini", use_rag=True)


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


@router.post("/{record_id}", response_model=AnalysisReportResponse, status_code=201)
async def analyze_health_record_with_rag(
    user_id: int,
    record_id: int,
    db: Session = Depends(get_db)
):
    """
    건강 기록 분석 (RAG 포함)

    - **user_id**: 사용자 ID
    - **record_id**: 건강 기록 ID
    - **RAG**: 논문 DB에서 관련 연구 자동 검색 및 분석에 포함
    """
    analysis_report = await health_service_rag.analyze_health_record(db, user_id, record_id)
    if not analysis_report:
        raise HTTPException(status_code=404, detail="건강 기록을 찾을 수 없습니다.")
    return analysis_report


@router.get("/{report_id}", response_model=AnalysisReportResponse)
def get_analysis_report(report_id: int, db: Session = Depends(get_db)):
    """
    RAG 분석 리포트 조회

    - **report_id**: 리포트 ID
    """
    analysis_report = AnalysisReportRepository.get_by_id(db, report_id)
    if not analysis_report:
        raise HTTPException(status_code=404, detail="분석 리포트를 찾을 수 없습니다.")
    return _parse_analysis_report(analysis_report)


@router.get("/record/{record_id}", response_model=AnalysisReportResponse)
def get_analysis_by_record(record_id: int, db: Session = Depends(get_db)):
    """
    건강 기록에 대한 RAG 분석 리포트 조회

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
    사용자의 RAG 분석 리포트 목록 조회

    - **user_id**: 사용자 ID
    - **limit**: 조회할 최대 개수
    """
    analysis_reports = AnalysisReportRepository.get_by_user(db, user_id, limit=limit)
    return [_parse_analysis_report(report) for report in analysis_reports]


@router.post("/{report_id}/chat", response_model=AnalysisChatResponse)
async def chat_about_report_with_rag(
    report_id: int,
    chat_request: AnalysisChatRequest,
    db: Session = Depends(get_db)
):
    """
    RAG 분석 결과에 대해 AI와 대화 (휴먼 피드백)

    - **report_id**: 분석 리포트 ID
    - **message**: 사용자 질문
    """
    # DB에서 thread_id를 조회하지 않고, 클라이언트가 보낸 thread_id를 사용합니다.
    # (팀원이 DB 설계를 완료할 때까지 임시로 메모리 기반 대화 유지)

    # LLM 서비스 호출 (대화 진행)
    response_text = await llm_service_rag.chat_with_analysis(chat_request.message, chat_request.thread_id)

    return {"response": response_text}
