"""
분석 라우터
/api/analysis/*
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from schemas.llm import AnalysisReportResponse
from services.common.health_service import HealthService
from repositories.llm.analysis_report_repository import AnalysisReportRepository
from typing import List

router = APIRouter()
health_service = HealthService()


@router.post("/{record_id}", response_model=AnalysisReportResponse, status_code=201)
async def analyze_health_record(
    user_id: int,
    record_id: int,
    db: Session = Depends(get_db)
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
    return analysis_report


@router.get("/record/{record_id}", response_model=AnalysisReportResponse)
def get_analysis_by_record(record_id: int, db: Session = Depends(get_db)):
    """
    건강 기록에 대한 분석 리포트 조회
    
    - **record_id**: 건강 기록 ID
    """
    analysis_report = AnalysisReportRepository.get_by_record_id(db, record_id)
    if not analysis_report:
        raise HTTPException(status_code=404, detail="분석 리포트를 찾을 수 없습니다.")
    return analysis_report


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
    return analysis_reports
