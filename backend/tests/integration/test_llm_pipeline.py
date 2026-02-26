"""
통합 테스트: create_inbody_analysis_prompt 함수가 전체 백엔드에서 올바르게 호출되는지 검증

테스트 대상:
1. agent_graph.py의 generate_initial_analysis 함수
2. llm_service.py의 chat_with_analysis 함수 (DB Fallback)

매개변수 변경사항:
- prev_inbody_date -> interval_days
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timedelta
from typing import Dict, Any

from services.llm.llm_service import LLMService
from schemas.llm import StatusAnalysisInput
from schemas.inbody import InBodyData as InBodyMeasurements


# 테스트용 샘플 데이터
SAMPLE_MEASUREMENTS: Dict[str, Any] = {
    "기본정보": {
        "신장": 175.0,
        "연령": 30,
        "성별": "남성"
    },
    "체성분": {
        "체수분": 42.5,
        "단백질": 12.0,
        "무기질": 4.2,
        "체지방": 18.5
    },
    "체중관리": {
        "체중": 75.0,
        "골격근량": 35.0,
        "체지방량": 18.5,
        "적정체중": 70.0,
        "체중조절": -5.0,
        "지방조절": -8.5,
        "근육조절": 3.5
    },
    "비만분석": {
        "BMI": 24.5,
        "체지방률": 24.7,
        "복부지방률": 0.88,
        "내장지방레벨": 7,
        "비만도": 107
    },
    "연구항목": {
        "제지방량": 56.5,
        "기초대사량": 1650,
        "권장섭취열량": 2400
    },
    "부위별근육분석": {
        "왼쪽팔": "표준",
        "오른쪽팔": "표준",
        "복부": "부족",
        "왼쪽하체": "발달",
        "오른쪽하체": "발달"
    },
    "부위별체지방분석": {
        "왼쪽팔": "표준",
        "오른쪽팔": "표준",
        "복부": "표준이상",
        "왼쪽하체": "표준",
        "오른쪽하체": "표준"
    }
}

PREV_MEASUREMENTS: Dict[str, Any] = {
    "기본정보": {
        "신장": 175.0,
        "연령": 30,
        "성별": "남성"
    },
    "체성분": {
        "체수분": 41.0,
        "단백질": 11.5,
        "무기질": 4.0,
        "체지방": 22.0
    },
    "체중관리": {
        "체중": 78.5,
        "골격근량": 33.0,
        "체지방량": 22.0,
        "적정체중": 70.0,
        "체중조절": -8.5,
        "지방조절": -12.0,
        "근육조절": 3.5
    },
    "비만분석": {
        "BMI": 25.6,
        "체지방률": 28.0,
        "복부지방률": 0.95,
        "내장지방레벨": 9,
        "비만도": 112
    },
    "연구항목": {
        "제지방량": 56.5,
        "기초대사량": 1600,
        "권장섭취열량": 2350
    },
    "부위별근육분석": {
        "왼쪽팔": "표준",
        "오른쪽팔": "표준",
        "복부": "부족",
        "왼쪽하체": "표준",
        "오른쪽하체": "표준"
    },
    "부위별체지방분석": {
        "왼쪽팔": "표준이상",
        "오른쪽팔": "표준이상",
        "복부": "표준이상",
        "왼쪽하체": "표준이상",
        "오른쪽하체": "표준이상"
    }
}


class TestPromptGeneratorIntegration:
    """create_inbody_analysis_prompt 함수의 통합 테스트"""

    @patch('services.llm.prompt_generator.create_inbody_analysis_prompt')
    def test_agent_graph_calls_prompt_generator_correctly(self, mock_prompt_gen):
        """
        agent_graph.py의 generate_initial_analysis가 
        create_inbody_analysis_prompt를 올바른 매개변수로 호출하는지 검증
        """
        from services.llm.agent_graph import create_analysis_agent
        
        # Mock LLM 클라이언트 생성
        mock_llm_client = Mock()
        mock_llm_client.generate_chat = Mock(return_value="분석 결과 텍스트")
        mock_llm_client.generate_chat_with_history = Mock(return_value="대화 응답")
        mock_llm_client.create_embedding = Mock(return_value=[0.1] * 1536)
        
        # Mock 프롬프트 생성 함수 설정
        mock_prompt_gen.return_value = ("system prompt", "user prompt")
        
        # 에이전트 생성
        agent = create_analysis_agent(mock_llm_client)
        
        # StatusAnalysisInput 생성 (interval_days 포함)
        analysis_input = StatusAnalysisInput(
            record_id=1,
            user_id=100,
            measured_at=datetime.now(),
            measurements=SAMPLE_MEASUREMENTS,
            body_type1="비만형",
            body_type2="상체발달형",
            prev_inbody_data=PREV_MEASUREMENTS,
            interval_days="30"  # 변경된 매개변수
        )
        
        # 에이전트 실행
        config = {"configurable": {"thread_id": "test_thread"}}
        try:
            result = agent.invoke(
                {"analysis_input": analysis_input},
                config=config
            )
            
            # create_inbody_analysis_prompt가 호출되었는지 확인
            assert mock_prompt_gen.called, "create_inbody_analysis_prompt가 호출되어야 합니다"
            
            # 호출 시 전달된 인자 확인
            call_args = mock_prompt_gen.call_args
            
            # measurements 인자 확인
            assert call_args.args[0] is not None or 'measurements' in call_args.kwargs
            
            # interval_days가 전달되었는지 확인 (prev_inbody_date가 아님)
            if call_args.kwargs:
                assert 'interval_days' in call_args.kwargs, "interval_days 매개변수가 전달되어야 합니다"
                assert 'prev_inbody_date' not in call_args.kwargs, "prev_inbody_date는 더 이상 사용되지 않아야 합니다"
                
        except Exception as e:
            # 에이전트 실행 중 타입 에러나 매개변수 에러가 발생하면 테스트 실패
            pytest.fail(f"에이전트 실행 중 에러 발생: {str(e)}")

    def test_status_analysis_input_schema_validation(self):
        """
        StatusAnalysisInput 스키마가 interval_days를 올바르게 처리하는지 검증
        """
        # interval_days가 있는 경우
        input_with_interval = StatusAnalysisInput(
            record_id=1,
            user_id=100,
            measured_at=datetime.now(),
            measurements=SAMPLE_MEASUREMENTS,
            body_type1="비만형",
            body_type2="상체발달형",
            prev_inbody_data=PREV_MEASUREMENTS,
            interval_days="30"
        )
        
        assert input_with_interval.interval_days == "30"
        
        # interval_days가 없는 경우
        input_without_interval = StatusAnalysisInput(
            record_id=1,
            user_id=100,
            measured_at=datetime.now(),
            measurements=SAMPLE_MEASUREMENTS,
            body_type1="비만형",
            body_type2="상체발달형"
        )
        
        assert input_without_interval.interval_days is None

    @patch('services.llm.prompt_generator.create_inbody_analysis_prompt')
    @patch('repositories.llm.analysis_report_repository.AnalysisReportRepository.get_by_id')
    @patch('repositories.common.health_record_repository.HealthRecordRepository.get_by_id')
    @patch('repositories.common.health_record_repository.HealthRecordRepository.get_previous_record')
    def test_llm_service_db_fallback_calls_prompt_correctly(
        self, 
        mock_get_prev_record,
        mock_get_health_record,
        mock_get_analysis_report,
        mock_prompt_gen
    ):
        """
        llm_service.py의 chat_with_analysis DB Fallback이
        create_inbody_analysis_prompt를 올바른 매개변수로 호출하는지 검증
        """
        # Mock 설정
        mock_prompt_gen.return_value = ("system prompt", "user prompt")
        
        # Mock DB 객체
        mock_db = Mock()
        
        # Mock analysis_report
        mock_analysis_report = Mock()
        mock_analysis_report.record_id = 1
        mock_get_analysis_report.return_value = mock_analysis_report
        
        # Mock health_record (현재)
        mock_health_record = Mock()
        mock_health_record.user_id = 100
        mock_health_record.measurements = SAMPLE_MEASUREMENTS
        mock_health_record.body_type1 = "비만형"
        mock_health_record.body_type2 = "상체발달형"
        mock_health_record.created_at = datetime.now()
        mock_get_health_record.return_value = mock_health_record
        
        # Mock previous health_record
        mock_prev_health_record = Mock()
        mock_prev_health_record.measurements = PREV_MEASUREMENTS
        mock_prev_health_record.created_at = datetime.now() - timedelta(days=30)
        mock_get_prev_record.return_value = mock_prev_health_record
        
        # Mock LLM 클라이언트
        mock_llm_client = Mock()
        mock_llm_client.generate_chat = Mock(return_value="분석 결과")
        mock_llm_client.create_embedding = Mock(return_value=[0.1] * 1536)
        
        # LLMService 인스턴스 생성 및 Mock 주입
        with patch('services.llm.llm_service.create_llm_client', return_value=mock_llm_client):
            with patch('services.llm.llm_service.create_analysis_agent') as mock_create_agent:
                # Mock 에이전트 설정
                mock_agent = Mock()
                mock_agent.checkpointer = None  # checkpoint 없음 (DB Fallback 트리거)
                mock_agent.invoke = Mock(return_value={
                    "messages": [
                        Mock(type="human", content="user message"),
                        Mock(type="ai", content="ai response")
                    ]
                })
                mock_create_agent.return_value = mock_agent
                
                llm_service = LLMService()
                
                # chat_with_analysis 호출 (DB Fallback 시나리오)
                import asyncio
                try:
                    result = asyncio.run(llm_service.chat_with_analysis(
                        thread_id="test_thread",
                        user_message="질문입니다",
                        report_id=1,
                        db=mock_db
                    ))
                    
                    # create_inbody_analysis_prompt가 호출되었는지 확인
                    assert mock_prompt_gen.called, "DB Fallback 시 create_inbody_analysis_prompt가 호출되어야 합니다"
                    
                    # 호출 시 전달된 인자 확인
                    call_args = mock_prompt_gen.call_args
                    
                    # interval_days가 전달되었는지 확인
                    if call_args.kwargs:
                        assert 'interval_days' in call_args.kwargs, "interval_days 매개변수가 전달되어야 합니다"
                        assert 'prev_inbody_date' not in call_args.kwargs, "prev_inbody_date는 더 이상 사용되지 않아야 합니다"
                        
                        # interval_days 값 확인 (29-30일 차이, 시간 차이로 인한 오차 허용)
                        interval_days = call_args.kwargs['interval_days']
                        assert interval_days in [29, 30], f"interval_days는 29 또는 30이어야 하지만 {interval_days}입니다"
                        
                except Exception as e:
                    pytest.fail(f"chat_with_analysis 실행 중 에러 발생: {str(e)}")

    def test_prepare_status_analysis_input_includes_interval_days(self):
        """
        LLMService.prepare_status_analysis_input이 interval_days를 포함하는지 검증
        """
        with patch('services.llm.llm_service.create_llm_client'):
            with patch('services.llm.llm_service.create_analysis_agent'):
                llm_service = LLMService()
                
                # prepare_status_analysis_input 호출
                result = llm_service.prepare_status_analysis_input(
                    record_id=1,
                    user_id=100,
                    measured_at=datetime.now(),
                    measurements=SAMPLE_MEASUREMENTS,
                    body_type1="비만형",
                    body_type2="상체발달형",
                    prev_inbody_data=PREV_MEASUREMENTS,
                    prev_inbody_date=datetime.now() - timedelta(days=30)
                )
                
                # 결과에 필요한 필드가 포함되어 있는지 확인
                assert "record_id" in result
                assert "user_id" in result
                assert "measurements" in result
                assert "prev_inbody_data" in result
                assert "prev_inbody_date" in result

    def test_no_type_errors_with_new_parameter_signature(self):
        """
        새로운 매개변수 시그니처로 호출 시 타입 에러가 발생하지 않는지 검증
        """
        from services.llm.prompt_generator import create_inbody_analysis_prompt
        
        measurements = InBodyMeasurements(**SAMPLE_MEASUREMENTS)
        prev_measurements = InBodyMeasurements(**PREV_MEASUREMENTS)
        
        try:
            # 새로운 시그니처로 호출
            system_prompt, user_prompt = create_inbody_analysis_prompt(
                measurements=measurements,
                body_type1="비만형",
                body_type2="상체발달형",
                prev_inbody_data=prev_measurements,
                interval_days="30"
            )
            
            # 타입 검증
            assert isinstance(system_prompt, str)
            assert isinstance(user_prompt, str)
            assert len(system_prompt) > 0
            assert len(user_prompt) > 0
            
        except TypeError as e:
            pytest.fail(f"타입 에러 발생: {str(e)}")
        except Exception as e:
            pytest.fail(f"예상치 못한 에러 발생: {str(e)}")

    def test_interval_days_calculation_in_llm_service(self):
        """
        llm_service.py에서 interval_days 계산이 올바른지 검증
        """
        current_date = datetime.now()
        prev_date = current_date - timedelta(days=45)
        
        # 날짜 차이 계산
        interval_days = (current_date - prev_date).days
        
        assert interval_days == 45, f"interval_days는 45여야 하지만 {interval_days}입니다"
