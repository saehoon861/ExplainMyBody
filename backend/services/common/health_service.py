"""
건강 서비스 - 인바디 데이터
건강 기록 관련 비즈니스 로직
"""

from sqlalchemy.orm import Session
from repositories.common.health_record_repository import HealthRecordRepository
from repositories.llm.analysis_report_repository import AnalysisReportRepository
from schemas.common import HealthRecordCreate
from schemas.llm import (
    StatusAnalysisInput,
    GoalPlanInput,
    StatusAnalysisResponse,
    GoalPlanPrepareResponse,
    AnalysisReportResponse,
    AnalysisReportCreate
)
from services.ocr.body_type_service import BodyTypeService
from services.llm.llm_service import LLMService
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
        record_data: HealthRecordCreate
    ):
        """
        건강 기록 생성

        Note: 체형 분류는 router에서 처리합니다.

        Args:
            db: 데이터베이스 세션
            user_id: 사용자 ID
            record_data: 건강 기록 데이터
        """
        # 건강 기록 생성 (body_type1, body_type2는 router에서 설정)
        health_record = HealthRecordRepository.create(db, user_id, record_data)
        return health_record

    def prepare_status_analysis(
        self,
        db: Session,
        user_id: int,
        record_id: int
    ) -> Optional[StatusAnalysisResponse]:
        """
        LLM1: 건강 기록 분석용 input 데이터 준비 (status_analysis)

        - 프론트엔드에서 선택한 건강 기록의 데이터를 반환
        - 프론트엔드에서 이 데이터를 LLM API에 전달

        Args:
            db: 데이터베이스 세션
            user_id: 사용자 ID
            record_id: 선택된 건강 기록 ID

        Returns:
            StatusAnalysisResponse: LLM input 데이터
        """
        # 건강 기록 조회
        health_record = HealthRecordRepository.get_by_id(db, record_id)
        if not health_record or health_record.user_id != user_id:
            return None

        # LLM input 데이터 준비
        # body_type1, body_type2는 measurements JSONB 안에 저장됨
        input_data = self.llm_service.prepare_status_analysis_input(
            record_id=health_record.id,
            user_id=health_record.user_id,
            measured_at=health_record.measured_at,
            measurements=health_record.measurements,
            body_type1=health_record.measurements.get('body_type1'),
            body_type2=health_record.measurements.get('body_type2')
        )

        return StatusAnalysisResponse(
            success=True,
            message="LLM input 데이터 준비 완료. 프론트엔드에서 LLM API를 호출하세요.",
            input_data=StatusAnalysisInput(**input_data)
        )

    def prepare_goal_plan(
        self,
        db: Session,
        user_id: int,
        record_id: int,
        user_goal_type: Optional[str] = None,
        user_goal_description: Optional[str] = None
    ) -> Optional[GoalPlanPrepareResponse]:
        """
        LLM2: 주간 계획서 생성용 input 데이터 준비 (goal_plan)

        - 사용자 요구사항 + 선택된 건강 기록 + status_analysis 결과를 반환
        - 프론트엔드에서 이 데이터를 LLM API에 전달

        Args:
            db: 데이터베이스 세션
            user_id: 사용자 ID
            record_id: 선택된 건강 기록 ID
            user_goal_type: 사용자 목표 타입
            user_goal_description: 사용자 목표 상세

        Returns:
            GoalPlanPrepareResponse: LLM input 데이터
        """
        # 선택된 건강 기록 조회
        health_record = HealthRecordRepository.get_by_id(db, record_id)
        if not health_record or health_record.user_id != user_id:
            return None

        # 해당 건강 기록의 status_analysis 결과 조회
        status_analysis = AnalysisReportRepository.get_by_record_id_and_type(
            db, record_id, "status_analysis"
        )

        status_analysis_result = None
        status_analysis_id = None
        if status_analysis:
            status_analysis_result = status_analysis.llm_output
            status_analysis_id = status_analysis.id

        # LLM input 데이터 준비
        input_data = self.llm_service.prepare_goal_plan_input(
            user_goal_type=user_goal_type,
            user_goal_description=user_goal_description,
            record_id=health_record.id,
            user_id=health_record.user_id,
            measured_at=health_record.measured_at,
            measurements=health_record.measurements,
            status_analysis_result=status_analysis_result,
            status_analysis_id=status_analysis_id
        )

        return GoalPlanPrepareResponse(
            success=True,
            message="LLM input 데이터 준비 완료. 프론트엔드에서 LLM API를 호출하세요.",
            input_data=GoalPlanInput(**input_data)
        )


    async def analyze_health_record(
        self,
        db: Session,
        user_id: int,
        record_id: int
    ) -> Optional[AnalysisReportResponse]:
        """
        건강 기록 분석 및 리포트 생성
        
        Args:
            db: 데이터베이스 세션
            user_id: 사용자 ID
            record_id: 건강 기록 ID
            
        Returns:
            AnalysisReportResponse: 생성된 분석 리포트
        """
        # 1. 건강 기록 조회
        health_record = HealthRecordRepository.get_by_id(db, record_id)
        if not health_record or health_record.user_id != user_id:
            return None
            
        # 2. 이미 존재하는 분석 리포트 확인 (status_analysis 타입)
        # 같은 날짜, 같은 데이터라도 record_id가 다르면 새로 생성해야 함
        existing_report = AnalysisReportRepository.get_by_record_id_and_type(
            db, record_id, "status_analysis"
        )
        
        if existing_report:
            # 기존 리포트도 summary와 content로 분리하여 반환
            from services.llm.parse_utils import split_analysis_response
            
            response = AnalysisReportResponse.model_validate(existing_report)
            parsed = split_analysis_response(existing_report.llm_output)
            response.summary = parsed["summary"]
            response.content = parsed["content"]
            
            return response
            
        # 3. LLM 서비스 호출을 위한 입력 데이터 준비
        # body_type1, body_type2는 measurements JSONB 안에 저장됨
        input_data = self.llm_service.prepare_status_analysis_input(
            record_id=health_record.id,
            user_id=health_record.user_id,
            measured_at=health_record.measured_at,
            measurements=health_record.measurements,
            body_type1=health_record.measurements.get('body_type1'),
            body_type2=health_record.measurements.get('body_type2')
        )
        
        # 4. LLM 호출
        try:
            # dict를 Pydantic 모델로 변환하여 전달해야 함 (llm_service가 객체 속성 접근을 사용하므로)
            analysis_input = StatusAnalysisInput(**input_data)
            llm_result = await self.llm_service.call_status_analysis_llm(analysis_input)
            llm_output = llm_result["analysis_text"]
            thread_id = llm_result.get("thread_id")
            embedding_data = llm_result.get("embedding") or {}
            embedding_1536 = embedding_data.get("embedding_1536")
            embedding_1024 = embedding_data.get("embedding_1024")
        except NotImplementedError:
             # LLM 서비스가 아직 구현되지 않았을 경우 Mock 데이터 사용
            llm_output = f"""
[건강 상태 분석 결과]
측정일: {health_record.measured_at.strftime('%Y-%m-%d')}
체중: {health_record.measurements.get('weight', 'N/A')}kg
골격근량: {health_record.measurements.get('skeletal_muscle_mass', 'N/A')}kg
체지방률: {health_record.measurements.get('body_fat_percentage', 'N/A')}%

현재 건강 상태는 전반적으로 양호합니다. 
꾸준한 운동과 식단 관리를 통해 현재 상태를 유지하는 것을 권장합니다.
"""
            thread_id = None
            embedding_1536 = None
            embedding_1024 = None

        # 5. 분석 리포트 저장
        report_data = AnalysisReportCreate(
            record_id=record_id,
            llm_output=llm_output,
            model_version=self.llm_service.model_version,
            analysis_type="status_analysis",
            thread_id=thread_id,
            embedding_1536=embedding_1536,
            embedding_1024=embedding_1024
        )
        
        analysis_report = AnalysisReportRepository.create(db, user_id, report_data)
        
        # 6. Pydantic 모델로 변환하여 반환
        # DB에는 thread_id가 저장되지 않았으므로, 응답 객체에 수동으로 주입하여 프론트엔드에 전달
        response = AnalysisReportResponse.model_validate(analysis_report)
        response.thread_id = thread_id
        
        # LLM1 출력 결과를 요약과 전문으로 분리 (프론트엔드 표시용)
        # 프론트엔드에서 요약만 먼저 보여주고, 전문은 접었다가 펼칠 수 있도록 함
        from services.llm.parse_utils import split_analysis_response
        parsed = split_analysis_response(llm_output)
        response.summary = parsed["summary"]
        response.content = parsed["content"]
        
        return response

    def get_record_with_analysis(
        self,
        db: Session,
        user_id: int,
        record_id: int
    ) -> Optional[Dict[str, Any]]:
        """
        특정 건강 기록과 분석 결과 조회

        Args:
            db: 데이터베이스 세션
            user_id: 사용자 ID
            record_id: 건강 기록 ID
        """
        health_record = HealthRecordRepository.get_by_id(db, record_id)
        if not health_record or health_record.user_id != user_id:
            return None

        # status_analysis 타입의 분석 결과 조회
        status_analysis = AnalysisReportRepository.get_by_record_id_and_type(
            db, record_id, "status_analysis"
        )

        # goal_plan 타입의 분석 결과 조회
        goal_plan = AnalysisReportRepository.get_by_record_id_and_type(
            db, record_id, "goal_plan"
        )

        return {
            "health_record": health_record,
            "status_analysis": status_analysis,
            "goal_plan": goal_plan
        }
