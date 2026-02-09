"""
prompt_generator.py의 create_inbody_analysis_prompt 함수 테스트

변경사항:
- prev_inbody_date 매개변수가 interval_days로 변경됨
- 이 변경사항이 전체 백엔드에서 타입 에러나 매개변수 에러를 발생시키지 않는지 테스트
"""

import pytest
from services.llm.prompt_generator import create_inbody_analysis_prompt
from schemas.inbody import InBodyData as InBodyMeasurements


class TestCreateInbodyAnalysisPrompt:
    """create_inbody_analysis_prompt 함수 테스트"""

    def test_basic_prompt_generation_without_prev_data(self, sample_inbody_data):
        """
        기본 테스트: 이전 데이터 없이 프롬프트 생성
        """
        measurements = InBodyMeasurements(**sample_inbody_data)
        
        system_prompt, user_prompt = create_inbody_analysis_prompt(
            measurements=measurements,
            body_type1="비만형",
            body_type2="상체발달형"
        )
        
        # 반환값 타입 검증
        assert isinstance(system_prompt, str), "system_prompt는 문자열이어야 합니다"
        assert isinstance(user_prompt, str), "user_prompt는 문자열이어야 합니다"
        
        # 프롬프트 내용 검증
        assert len(system_prompt) > 0, "system_prompt는 비어있지 않아야 합니다"
        assert len(user_prompt) > 0, "user_prompt는 비어있지 않아야 합니다"
        
        # 이전 데이터가 없을 때 "없음"이 포함되어야 함
        assert "없음" in system_prompt, "이전 인바디 데이터가 없을 때 '없음'이 포함되어야 합니다"
        
        # 사용자 데이터가 포함되어야 함
        assert "남성" in user_prompt
        assert "30세" in user_prompt
        assert "175" in user_prompt
        assert "75.0" in user_prompt

    def test_prompt_generation_with_prev_data_and_interval(self, sample_inbody_data, prev_inbody_data):
        """
        이전 데이터와 interval_days가 있을 때 프롬프트 생성
        """
        measurements = InBodyMeasurements(**sample_inbody_data)
        prev_measurements = InBodyMeasurements(**prev_inbody_data)
        
        system_prompt, user_prompt = create_inbody_analysis_prompt(
            measurements=measurements,
            body_type1="비만형",
            body_type2="상체발달형",
            prev_inbody_data=prev_measurements,
            interval_days="30"
        )
        
        # 반환값 타입 검증
        assert isinstance(system_prompt, str)
        assert isinstance(user_prompt, str)
        
        # 이전 데이터 정보가 포함되어야 함
        assert "이전 인바디 데이터와 간격" in system_prompt
        assert "30일" in system_prompt
        
        # 변화량 계산 검증 (체중 변화: 78.5 - 75.0 = 3.5kg)
        assert "변화 체중" in system_prompt

    def test_prompt_generation_with_prev_data_only(self, sample_inbody_data, prev_inbody_data):
        """
        이전 데이터만 있고 interval_days가 없을 때
        (이 경우 이전 데이터가 무시되어야 함)
        """
        measurements = InBodyMeasurements(**sample_inbody_data)
        prev_measurements = InBodyMeasurements(**prev_inbody_data)
        
        system_prompt, user_prompt = create_inbody_analysis_prompt(
            measurements=measurements,
            body_type1="비만형",
            body_type2="상체발달형",
            prev_inbody_data=prev_measurements,
            interval_days=None
        )
        
        # interval_days가 없으면 이전 데이터가 무시되어야 함
        assert "없음" in system_prompt

    def test_prompt_generation_with_interval_only(self, sample_inbody_data):
        """
        interval_days만 있고 이전 데이터가 없을 때
        (이 경우 interval_days가 무시되어야 함)
        """
        measurements = InBodyMeasurements(**sample_inbody_data)
        
        system_prompt, user_prompt = create_inbody_analysis_prompt(
            measurements=measurements,
            body_type1="비만형",
            body_type2="상체발달형",
            prev_inbody_data=None,
            interval_days="30"
        )
        
        # prev_inbody_data가 없으면 interval_days가 무시되어야 함
        assert "없음" in system_prompt

    def test_optional_parameters(self, sample_inbody_data):
        """
        선택적 매개변수 테스트 (body_type1, body_type2가 None일 때)
        """
        measurements = InBodyMeasurements(**sample_inbody_data)
        
        system_prompt, user_prompt = create_inbody_analysis_prompt(
            measurements=measurements
        )
        
        # 기본 동작 확인
        assert isinstance(system_prompt, str)
        assert isinstance(user_prompt, str)
        assert len(system_prompt) > 0
        assert len(user_prompt) > 0

    def test_parameter_types(self, sample_inbody_data, prev_inbody_data):
        """
        매개변수 타입 검증
        """
        measurements = InBodyMeasurements(**sample_inbody_data)
        prev_measurements = InBodyMeasurements(**prev_inbody_data)
        
        # 올바른 타입으로 호출
        system_prompt, user_prompt = create_inbody_analysis_prompt(
            measurements=measurements,
            body_type1="비만형",
            body_type2="상체발달형",
            prev_inbody_data=prev_measurements,
            interval_days="30"
        )
        
        assert isinstance(system_prompt, str)
        assert isinstance(user_prompt, str)

    def test_all_body_sections_included(self, sample_inbody_data):
        """
        모든 InBody 섹션이 user_prompt에 포함되는지 확인
        """
        measurements = InBodyMeasurements(**sample_inbody_data)
        
        _, user_prompt = create_inbody_analysis_prompt(
            measurements=measurements,
            body_type1="비만형",
            body_type2="상체발달형"
        )
        
        # 주요 섹션 헤더 확인
        assert "기본 정보" in user_prompt
        assert "체성분 분석" in user_prompt
        assert "비만 지표" in user_prompt
        assert "대사 정보" in user_prompt
        assert "조절 목표" in user_prompt
        assert "부위별 근육 등급" in user_prompt
        assert "규칙 기반 체형 분석" in user_prompt

    def test_interval_days_string_type(self, sample_inbody_data, prev_inbody_data):
        """
        interval_days가 문자열 타입으로 전달되는지 확인
        """
        measurements = InBodyMeasurements(**sample_inbody_data)
        prev_measurements = InBodyMeasurements(**prev_inbody_data)
        
        # 문자열로 전달
        system_prompt, _ = create_inbody_analysis_prompt(
            measurements=measurements,
            prev_inbody_data=prev_measurements,
            interval_days="45"
        )
        
        assert "45일" in system_prompt

    def test_return_tuple_structure(self, sample_inbody_data):
        """
        반환값이 정확히 2개의 문자열 튜플인지 확인
        """
        measurements = InBodyMeasurements(**sample_inbody_data)
        
        result = create_inbody_analysis_prompt(
            measurements=measurements,
            body_type1="비만형",
            body_type2="상체발달형"
        )
        
        # 튜플 타입 확인
        assert isinstance(result, tuple)
        assert len(result) == 2
        
        # 각 요소가 문자열인지 확인
        system_prompt, user_prompt = result
        assert isinstance(system_prompt, str)
        assert isinstance(user_prompt, str)
