"""
LLM 서비스
AI 분석 및 계획 생성
=========================
현재: 팀원이 LLM API 연동을 작성할 예정이므로, input 데이터만 반환
추후: LLM API 호출 구현 예정
=========================
"""

from typing import Dict, Any, Optional
import os
from dotenv import load_dotenv

load_dotenv()


class LLMService:
    """LLM API 호출 서비스 (현재는 input 데이터 반환용)"""

    def __init__(self):
        """LLM 클라이언트 초기화"""
        # TODO: LLM API 키 설정
        self.api_key = os.getenv("LLM_API_KEY", "")
        self.model_version = "pending"  # 팀원이 LLM 연동 시 설정

    def prepare_status_analysis_input(
        self,
        record_id: int,
        user_id: int,
        measured_at: Any,
        measurements: Dict[str, Any],
        body_type1: Optional[str] = None,
        body_type2: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        LLM1: 건강 상태 분석용 input 데이터 준비

        Args:
            record_id: 건강 기록 ID
            user_id: 사용자 ID
            measured_at: 측정 일시
            measurements: 인바디 측정 데이터
            body_type1: stage2 체형 분류
            body_type2: stage3 체형 분류

        Returns:
            LLM에 전달할 input 데이터 (프론트엔드에서 LLM API 호출 시 사용)
        """
        return {
            "record_id": record_id,
            "user_id": user_id,
            "measured_at": measured_at,
            "measurements": measurements,
            "body_type1": body_type1,
            "body_type2": body_type2
        }

    def prepare_goal_plan_input(
        self,
        # 사용자 요구사항
        user_goal_type: Optional[str],
        user_goal_description: Optional[str],
        # 선택된 건강 기록
        record_id: int,
        user_id: int,
        measured_at: Any,
        measurements: Dict[str, Any],
        body_type1: Optional[str] = None,
        body_type2: Optional[str] = None,
        # LLM1 분석 결과
        status_analysis_result: Optional[str] = None,
        status_analysis_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        LLM2: 주간 계획서 생성용 input 데이터 준비

        Args:
            user_goal_type: 사용자 목표 타입
            user_goal_description: 사용자 목표 상세
            record_id: 선택된 건강 기록 ID
            user_id: 사용자 ID
            measured_at: 측정 일시
            measurements: 인바디 측정 데이터
            body_type1: stage2 체형 분류
            body_type2: stage3 체형 분류
            status_analysis_result: LLM1의 분석 결과 텍스트
            status_analysis_id: LLM1 분석 결과 ID

        Returns:
            LLM에 전달할 input 데이터 (프론트엔드에서 LLM API 호출 시 사용)
        """
        return {
            "user_goal_type": user_goal_type,
            "user_goal_description": user_goal_description,
            "record_id": record_id,
            "user_id": user_id,
            "measured_at": measured_at,
            "measurements": measurements,
            "body_type1": body_type1,
            "body_type2": body_type2,
            "status_analysis_result": status_analysis_result,
            "status_analysis_id": status_analysis_id
        }

    # =====================================================
    # 아래는 팀원이 LLM API 연동 시 구현할 메서드들
    # =====================================================

    async def call_status_analysis_llm(
        self,
        input_data: Dict[str, Any]
    ) -> str:
        """
        TODO: 팀원이 구현 예정
        LLM1: 건강 상태 분석 API 호출

        Args:
            input_data: prepare_status_analysis_input()의 반환값

        Returns:
            LLM이 생성한 분석 결과 텍스트
        """
        # 임시 Mock 구현
        return self._create_status_analysis_prompt(input_data)
        # raise NotImplementedError("LLM API 연동 미구현 - 팀원이 구현 예정")

    async def call_goal_plan_llm(
        self,
        input_data: Dict[str, Any]
    ) -> str:
        """
        TODO: 팀원이 구현 예정
        LLM2: 주간 계획서 생성 API 호출

        Args:
            input_data: prepare_goal_plan_input()의 반환값

        Returns:
            LLM이 생성한 주간 계획서 텍스트
        """
        raise NotImplementedError("LLM API 연동 미구현 - 팀원이 구현 예정")

    def _create_status_analysis_prompt(
        self,
        input_data: Dict[str, Any]
    ) -> str:
        """
        TODO: 팀원이 구현 예정
        상태 분석용 프롬프트 생성
        """
        return f"""
당신은 전문 건강 컨설턴트입니다.
다음 인바디 데이터와 체형 정보를 분석하여 사용자의 현재 건강 상태를 평가해주세요.

인바디 데이터:
{input_data.get('measurements', {})}

체형 분류: {input_data.get('body_type1', '미분류')}

분석 내용:
1. 현재 건강 상태 평가
2. 강점과 개선이 필요한 부분
3. 건강 관리 권장사항
"""

    def _create_goal_plan_prompt(
        self,
        input_data: Dict[str, Any]
    ) -> str:
        """
        TODO: 팀원이 구현 예정
        주간 계획 생성용 프롬프트 생성
        """
        return f"""
당신은 전문 피트니스 트레이너입니다.
다음 정보를 바탕으로 사용자의 목표 달성을 위한 주간 계획을 작성해주세요.

인바디 데이터: {input_data.get('measurements', {})}
체형: {input_data.get('body_type1', '미분류')}
건강 분석 결과: {input_data.get('status_analysis_result', '분석 결과 없음')}
사용자 목표: {input_data.get('user_goal_description') or input_data.get('user_goal_type') or '건강 개선'}

주간 계획 포함 사항:
1. 요일별 운동 계획
2. 식단 권장사항
3. 주의사항 및 팁
"""
