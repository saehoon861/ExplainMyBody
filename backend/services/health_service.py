"""
건강 서비스 - 인바디 데이터
건강 기록 관련 비즈니스 로직
"""

from sqlalchemy.orm import Session
from repositories.health_record_repository import HealthRecordRepository
from repositories.analysis_report_repository import AnalysisReportRepository
from schemas.health_record import HealthRecordCreate
from services.body_type_service import BodyTypeService
from services.llm_service import LLMService
from typing import Optional, Dict, Any


class HealthService:
    """건강 기록 관련 비즈니스 로직"""
    
    def __init__(self):
        self.body_type_service = BodyTypeService()
        self.llm_service = LLMService()
    
    def create_health_record(
        self,
        db: Session,
        user_id: int,
        record_data: HealthRecordCreate,
        auto_classify: bool = True
    ):
        """
        건강 기록 생성 및 자동 체형 분류
        
        Args:
            db: 데이터베이스 세션
            user_id: 사용자 ID
            record_data: 건강 기록 데이터
            auto_classify: 자동 체형 분류 여부
        """
        # 건강 기록 생성
        health_record = HealthRecordRepository.create(db, user_id, record_data)
        
        # 자동 체형 분류 # input, output의 형태에 대한 확인 필요 #fixme
        if auto_classify:
            body_type = self.body_type_service.classify_body_type(record_data.measurements)
            if body_type:
                health_record = HealthRecordRepository.update(
                    db, health_record.id, body_type=body_type
                )
        
        return health_record
    
    async def analyze_health_record(
        self,
        db: Session,
        user_id: int,
        record_id: int
    ):
        """
        건강 기록 분석 (LLM 사용)
        
        Args:
            db: 데이터베이스 세션
            user_id: 사용자 ID
            record_id: 건강 기록 ID
        """
        # 건강 기록 조회
        health_record = HealthRecordRepository.get_by_id(db, record_id)
        if not health_record or health_record.user_id != user_id:
            return None
        
        # LLM 분석 실행
        # 추후 LLM1의 개발이 완료되면 그에 맞춰서 수정필요 #fixme
        analysis_text = await self.llm_service.analyze_health_status(
            health_record.measurements,
            health_record.body_type
        )
        
        # 분석 결과 저장
        from schemas.analysis_report import AnalysisReportCreate
        report_data = AnalysisReportCreate(
            record_id=record_id,
            llm_output=analysis_text,
            model_version=self.llm_service.model_version,
            analysis_type="status_analysis"
        )
        
        analysis_report = AnalysisReportRepository.create(db, user_id, report_data)
        return analysis_report
    
    def get_latest_record_with_analysis(self, db: Session, user_id: int):
        """
        가장 최신 건강 기록과 분석 결과 조회
        """
        latest_record = HealthRecordRepository.get_latest(db, user_id)
        if not latest_record:
            return None
        
        analysis_report = AnalysisReportRepository.get_by_record_id(db, latest_record.id)
        
        return {
            "health_record": latest_record,
            "analysis_report": analysis_report
        }
