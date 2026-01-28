"""
AnalysisReport Repository
분석 리포트 데이터 접근 계층
"""

from sqlalchemy.orm import Session
from sqlalchemy import desc
from models.analysis_report import AnalysisReport
from schemas.analysis_report import AnalysisReportCreate
from typing import Optional, List


class AnalysisReportRepository:
    """분석 리포트 데이터 접근 계층"""
    
    @staticmethod
    def create(db: Session, user_id: int, report_data: AnalysisReportCreate) -> AnalysisReport:
        """분석 리포트 생성"""
        db_report = AnalysisReport(
            user_id=user_id,
            record_id=report_data.record_id,
            llm_output=report_data.llm_output,
            model_version=report_data.model_version,
            analysis_type=report_data.analysis_type
        )
        db.add(db_report)
        db.commit()
        db.refresh(db_report)
        return db_report
    
    @staticmethod
    def get_by_id(db: Session, report_id: int) -> Optional[AnalysisReport]:
        """ID로 리포트 조회"""
        return db.query(AnalysisReport).filter(AnalysisReport.id == report_id).first()
    
    @staticmethod
    def get_by_record_id(db: Session, record_id: int) -> Optional[AnalysisReport]:
        """건강 기록 ID로 리포트 조회 (가장 최신)"""
        return db.query(AnalysisReport)\
            .filter(AnalysisReport.record_id == record_id)\
            .order_by(desc(AnalysisReport.generated_at))\
            .first()
    
    @staticmethod
    def get_by_user(db: Session, user_id: int, limit: int = 10) -> List[AnalysisReport]:
        """사용자의 리포트 목록 조회"""
        return db.query(AnalysisReport)\
            .filter(AnalysisReport.user_id == user_id)\
            .order_by(desc(AnalysisReport.generated_at))\
            .limit(limit)\
            .all()
    
    @staticmethod
    def delete(db: Session, report_id: int) -> bool:
        """리포트 삭제"""
        db_report = db.query(AnalysisReport).filter(AnalysisReport.id == report_id).first()
        if db_report:
            db.delete(db_report)
            db.commit()
            return True
        return False
