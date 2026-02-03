"""
건강 서비스 (RAG 버전)
RAG 기능이 추가된 건강 기록 관련 비즈니스 로직
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
from services.llm.llm_rag.llm_service_rag import LLMServiceRAG
from typing import Optional, Dict, Any


class HealthServiceRAG:
    """RAG 기능이 추가된 건강 기록 관련 비즈니스 로직"""

    def __init__(self):
        self.body_type_service = BodyTypeService()
        self.llm_service_rag = LLMServiceRAG(model_version="gpt-4o-mini", use_rag=True)

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
        LLM1 (RAG): 건강 기록 분석용 input 데이터 준비 (status_analysis_rag)

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
        measurements = health_record.measurements
        input_data = {
            "record_id": health_record.id,
            "user_id": health_record.user_id,
            "measured_at": health_record.measured_at,
            "measurements": measurements,
            "body_type1": measurements.get('body_type1'),
            "body_type2": measurements.get('body_type2')
        }

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
        LLM2 (RAG): 주간 계획서 생성용 input 데이터 준비 (goal_plan_rag)

        - 사용자 요구사항 + 선택된 건강 기록 + status_analysis_rag 결과를 반환
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

        # 해당 건강 기록의 status_analysis_rag 결과 조회
        status_analysis = AnalysisReportRepository.get_by_record_id_and_type(
            db, record_id, "status_analysis_rag"
        )

        status_analysis_result = None
        status_analysis_id = None
        if status_analysis:
            status_analysis_result = status_analysis.llm_output
            status_analysis_id = status_analysis.id

        # LLM input 데이터 준비
        measurements = health_record.measurements
        input_data = {
            "user_goal_type": user_goal_type,
            "user_goal_description": user_goal_description,
            "record_id": health_record.id,
            "user_id": health_record.user_id,
            "measured_at": health_record.measured_at,
            "measurements": measurements,
            "status_analysis_result": status_analysis_result,
            "status_analysis_id": status_analysis_id,
            "main_goal": user_goal_type or "건강 유지",
            "target_weight": None,
            "target_date": None,
            "preferred_exercise_types": [],
            "available_days_per_week": None,
            "available_time_per_session": None,
            "restrictions": []
        }

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
        건강 기록 분석 및 리포트 생성 (RAG 포함)

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

        # 2. 이미 존재하는 분석 리포트 확인 (status_analysis_rag 타입)
        existing_report = AnalysisReportRepository.get_by_record_id_and_type(
            db, record_id, "status_analysis_rag"
        )

        if existing_report:
            response = AnalysisReportResponse.model_validate(existing_report)
            # 파싱 추가
            from services.llm.parse_utils import split_analysis_response
            parsed = split_analysis_response(existing_report.llm_output)
            response.summary = parsed["summary"]
            response.content = parsed["content"]
            return response

        # 3. LLM 서비스 호출을 위한 입력 데이터 준비
        measurements = health_record.measurements
        analysis_input = StatusAnalysisInput(
            record_id=health_record.id,
            user_id=health_record.user_id,
            measured_at=health_record.measured_at,
            measurements=measurements,
            body_type1=measurements.get('body_type1', ''),
            body_type2=measurements.get('body_type2', '')
        )

        # 4. LLM RAG 호출
        thread_id = f"analysis_rag_{record_id}"

        try:
            result = await self.llm_service_rag.call_status_analysis_llm(
                analysis_input=analysis_input,
                thread_id=thread_id
            )

            llm_output = result["analysis_text"]
            embedding = result["embedding"]
            rag_context = result.get("rag_context", "")

        except NotImplementedError:
            # LLM 서비스가 아직 구현되지 않았을 경우 Mock 데이터 사용
            llm_output = f"""
[건강 상태 분석 결과 (RAG)]
측정일: {health_record.measured_at.strftime('%Y-%m-%d')}
체중: {measurements.get('weight', 'N/A')}kg
골격근량: {measurements.get('skeletal_muscle_mass', 'N/A')}kg
체지방률: {measurements.get('body_fat_percentage', 'N/A')}%

현재 건강 상태는 전반적으로 양호합니다.
꾸준한 운동과 식단 관리를 통해 현재 상태를 유지하는 것을 권장합니다.
"""
            embedding = None
            rag_context = ""

        # 5. 분석 리포트 저장
        report_data = AnalysisReportCreate(
            record_id=record_id,
            llm_output=llm_output,
            model_version="gpt-4o-mini-rag",
            analysis_type="status_analysis_rag"
        )

        analysis_report = AnalysisReportRepository.create(db, user_id, report_data)

        # 6. 임베딩 저장 (있는 경우)
        if embedding and embedding.get("embedding_1536"):
            AnalysisReportRepository.update_embedding(
                db,
                analysis_report.id,
                embedding["embedding_1536"]
            )

        db.commit()
        db.refresh(analysis_report)

        # 7. Pydantic 모델로 변환하여 반환
        response = AnalysisReportResponse.model_validate(analysis_report)
        response.thread_id = thread_id

        # LLM 출력 결과를 요약과 전문으로 분리
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
        특정 건강 기록과 분석 결과 조회 (RAG 버전)

        Args:
            db: 데이터베이스 세션
            user_id: 사용자 ID
            record_id: 건강 기록 ID
        """
        health_record = HealthRecordRepository.get_by_id(db, record_id)
        if not health_record or health_record.user_id != user_id:
            return None

        # status_analysis_rag 타입의 분석 결과 조회
        status_analysis = AnalysisReportRepository.get_by_record_id_and_type(
            db, record_id, "status_analysis_rag"
        )

        # goal_plan_rag 타입의 분석 결과 조회
        goal_plan = AnalysisReportRepository.get_by_record_id_and_type(
            db, record_id, "goal_plan_rag"
        )

        return {
            "health_record": health_record,
            "status_analysis": status_analysis,
            "goal_plan": goal_plan
        }
