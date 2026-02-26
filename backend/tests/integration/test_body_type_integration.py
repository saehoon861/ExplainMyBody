"""
체형 분석 통합 테스트
===================
인바디 기록 생성 시 체형 분석이 정상적으로 수행되고 
measurements JSONB 컬럼에 body_type1, body_type2가 제대로 들어가는지 확인

Mock을 사용하여 DB 저장 직전에 데이터를 가로채서 검증
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from schemas.inbody import InBodyData
from schemas.body_type import BodyTypeAnalysisInput
from schemas.common import HealthRecordCreate
from services.ocr.body_type_service import BodyTypeService
from services.common.health_service import HealthService


# ============================================================================
# Sample Data Fixtures
# ============================================================================

@pytest.fixture
def complete_inbody_data():
    """완전한 인바디 데이터 (모든 필드 포함)"""
    return {
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
            "복부": "표준이하",
            "왼쪽하체": "표준이상",
            "오른쪽하체": "표준이상"
        },
        "부위별체지방분석": {
            "왼쪽팔": "표준",
            "오른쪽팔": "표준",
            "복부": "표준이상",
            "왼쪽하체": "표준",
            "오른쪽하체": "표준"
        }
    }


@pytest.fixture
def lean_muscle_inbody_data():
    """근육형 체형 데이터"""
    return {
        "기본정보": {
            "신장": 180.0,
            "연령": 28,
            "성별": "남성"
        },
        "체성분": {
            "체수분": 48.0,
            "단백질": 14.5,
            "무기질": 4.8,
            "체지방": 12.0
        },
        "체중관리": {
            "체중": 80.0,
            "골격근량": 42.0,
            "체지방량": 12.0,
            "적정체중": 75.0,
            "체중조절": -5.0,
            "지방조절": -2.0,
            "근육조절": 0.0
        },
        "비만분석": {
            "BMI": 24.7,
            "체지방률": 15.0,
            "복부지방률": 0.75,
            "내장지방레벨": 5,
            "비만도": 107
        },
        "연구항목": {
            "제지방량": 68.0,
            "기초대사량": 1850,
            "권장섭취열량": 2700
        },
        "부위별근육분석": {
            "왼쪽팔": "표준이상",
            "오른쪽팔": "표준이상",
            "복부": "표준",
            "왼쪽하체": "표준이상",
            "오른쪽하체": "표준이상"
        },
        "부위별체지방분석": {
            "왼쪽팔": "표준",
            "오른쪽팔": "표준",
            "복부": "표준",
            "왼쪽하체": "표준",
            "오른쪽하체": "표준"
        }
    }


# ============================================================================
# Integration Tests
# ============================================================================

@pytest.mark.integration
class TestBodyTypeIntegration:
    """체형 분석 통합 테스트 - Mock을 사용하여 DB 저장 직전 데이터 검증"""
    
    def test_body_type_analysis_and_save_flow(self, complete_inbody_data):
        """
        [통합 테스트] 인바디 데이터 입력 → 체형 분석 → DB 저장 흐름 검증
        
        Flow:
        1. InBodyData Pydantic 검증
        2. BodyTypeService로 체형 분석 수행
        3. measurements에 body_type1, body_type2 추가
        4. HealthService.create_health_record 호출
        5. Mock으로 Repository.create 가로채서 measurements 검증
        """
        # Step 1: Pydantic 검증
        validated_inbody = InBodyData(**complete_inbody_data)
        assert validated_inbody is not None
        print(f"\n✅ Step 1: InBodyData 검증 완료")
        
        # Step 2: 체형 분석 수행
        body_type_service = BodyTypeService()
        
        # InBodyData에서 체형 분석 입력 생성
        body_type_input = BodyTypeAnalysisInput.from_inbody_data(
            inbody=validated_inbody,
            muscle_seg=validated_inbody.부위별근육분석.model_dump(),
            fat_seg=validated_inbody.부위별체지방분석.model_dump()
        )
        
        # 체형 분석 실행
        body_type_result = body_type_service.get_full_analysis(body_type_input)
        
        assert body_type_result is not None, "체형 분석 결과가 None입니다"
        assert hasattr(body_type_result, 'stage2'), "stage2 (body_type1) 결과가 없습니다"
        assert hasattr(body_type_result, 'stage3'), "stage3 (body_type2) 결과가 없습니다"
        
        body_type1 = body_type_result.stage2
        body_type2 = body_type_result.stage3
        
        print(f"✅ Step 2: 체형 분석 완료")
        print(f"   - body_type1 (stage2): {body_type1}")
        print(f"   - body_type2 (stage3): {body_type2}")
        
        # Step 3: measurements에 체형 분석 결과 추가
        measurements_with_body_type = validated_inbody.model_dump(exclude_none=True)
        measurements_with_body_type["body_type1"] = body_type1
        measurements_with_body_type["body_type2"] = body_type2
        
        print(f"✅ Step 3: measurements에 체형 분석 결과 추가 완료")
        
        # Step 4: HealthService를 통해 DB 저장 시도 (Mock으로 가로채기)
        health_service = HealthService()
        record_data = HealthRecordCreate(
            measurements=measurements_with_body_type,
            source="ocr"
        )
        
        # Mock DB 세션
        mock_db = Mock()
        test_user_id = 123
        
        # Mock: Repository.create를 가로채서 호출 인자 검증
        with patch('services.common.health_service.HealthRecordRepository.create') as mock_create:
            # Mock이 반환할 가짜 HealthRecord 객체
            mock_health_record = Mock()
            mock_health_record.id = 1
            mock_health_record.user_id = test_user_id
            mock_health_record.measurements = measurements_with_body_type
            mock_health_record.source = "ocr"
            mock_create.return_value = mock_health_record
            
            # HealthService.create_health_record 호출
            result = health_service.create_health_record(
                db=mock_db,
                user_id=test_user_id,
                record_data=record_data
            )
            
            # Step 5: Mock 호출 검증
            assert mock_create.called, "Repository.create가 호출되지 않았습니다"
            assert mock_create.call_count == 1, "Repository.create가 여러 번 호출되었습니다"
            
            # 호출 인자 확인
            call_args = mock_create.call_args
            called_db = call_args[0][0]
            called_user_id = call_args[0][1]
            called_record_data = call_args[0][2]
            
            assert called_db == mock_db, "DB 세션이 올바르지 않습니다"
            assert called_user_id == test_user_id, "user_id가 올바르지 않습니다"
            assert isinstance(called_record_data, HealthRecordCreate), "record_data 타입이 올바르지 않습니다"
            
            # 🎯 핵심 검증: measurements에 body_type1, body_type2가 포함되어 있는지 확인
            saved_measurements = called_record_data.measurements
            
            assert "body_type1" in saved_measurements, "❌ body_type1이 measurements에 없습니다!"
            assert "body_type2" in saved_measurements, "❌ body_type2가 measurements에 없습니다!"
            
            assert saved_measurements["body_type1"] == body_type1, \
                f"❌ body_type1 값이 다릅니다: {saved_measurements['body_type1']} != {body_type1}"
            assert saved_measurements["body_type2"] == body_type2, \
                f"❌ body_type2 값이 다릅니다: {saved_measurements['body_type2']} != {body_type2}"
            
            # 인바디 데이터도 제대로 포함되어 있는지 확인
            assert "기본정보" in saved_measurements, "기본정보가 measurements에 없습니다"
            assert "비만분석" in saved_measurements, "비만분석이 measurements에 없습니다"
            assert saved_measurements["기본정보"]["신장"] == 175.0, "신장 데이터가 올바르지 않습니다"
            assert saved_measurements["비만분석"]["BMI"] == 24.5, "BMI 데이터가 올바르지 않습니다"
            
            print(f"\n✅ Step 4: Repository.create 호출 검증 완료")
            print(f"   - DB에 저장될 measurements에 body_type1: {saved_measurements['body_type1']}")
            print(f"   - DB에 저장될 measurements에 body_type2: {saved_measurements['body_type2']}")
            print(f"   - source: {called_record_data.source}")
            print(f"\n🎉 통합 테스트 성공: 체형 분석 결과가 measurements에 제대로 포함되어 DB에 저장됩니다!")
    
    
    def test_lean_muscle_body_type_flow(self, lean_muscle_inbody_data):
        """
        [통합 테스트] 근육형 체형 데이터로 전체 흐름 테스트
        """
        # Pydantic 검증
        validated_inbody = InBodyData(**lean_muscle_inbody_data)
        
        # 체형 분석
        body_type_service = BodyTypeService()
        body_type_input = BodyTypeAnalysisInput.from_inbody_data(
            inbody=validated_inbody,
            muscle_seg=validated_inbody.부위별근육분석.model_dump(),
            fat_seg=validated_inbody.부위별체지방분석.model_dump()
        )
        
        body_type_result = body_type_service.get_full_analysis(body_type_input)
        
        assert body_type_result is not None
        body_type1 = body_type_result.stage2
        body_type2 = body_type_result.stage3
        
        print(f"\n🏋️ 근육형 체형 분석 결과:")
        print(f"   - body_type1: {body_type1}")
        print(f"   - body_type2: {body_type2}")
        
        # measurements에 추가
        measurements_with_body_type = validated_inbody.model_dump(exclude_none=True)
        measurements_with_body_type["body_type1"] = body_type1
        measurements_with_body_type["body_type2"] = body_type2
        
        # HealthService를 통해 저장 시도
        health_service = HealthService()
        record_data = HealthRecordCreate(
            measurements=measurements_with_body_type,
            source="ocr"
        )
        
        mock_db = Mock()
        test_user_id = 456
        
        # Mock으로 검증
        with patch('services.common.health_service.HealthRecordRepository.create') as mock_create:
            mock_health_record = Mock()
            mock_health_record.id = 2
            mock_health_record.measurements = measurements_with_body_type
            mock_create.return_value = mock_health_record
            
            result = health_service.create_health_record(
                db=mock_db,
                user_id=test_user_id,
                record_data=record_data
            )
            
            # 검증
            call_args = mock_create.call_args
            saved_measurements = call_args[0][2].measurements
            
            assert saved_measurements["body_type1"] == body_type1
            assert saved_measurements["body_type2"] == body_type2
            
            print(f"✅ 근육형 체형 테스트 성공")
            print(f"   - measurements에 body_type1: {saved_measurements['body_type1']}")
            print(f"   - measurements에 body_type2: {saved_measurements['body_type2']}")
    
    
    def test_body_type_service_only(self):
        """
        [단위 테스트] BodyTypeService만 독립적으로 테스트
        
        DB 없이 체형 분석 로직만 검증
        """
        body_type_service = BodyTypeService()
        
        # 테스트 데이터
        test_input = BodyTypeAnalysisInput(
            성별="남성",
            연령=30,
            신장=175.0,
            체중=75.0,
            BMI=24.5,
            체지방률=24.7,
            골격근량=35.0,
            muscle_seg={
                "왼팔": "표준",
                "오른팔": "표준",
                "몸통": "표준이하",
                "왼다리": "표준이상",
                "오른다리": "표준이상"
            },
            fat_seg={
                "왼팔": "표준",
                "오른팔": "표준",
                "몸통": "표준이상",
                "왼다리": "표준",
                "오른다리": "표준"
            }
        )
        
        result = body_type_service.get_full_analysis(test_input)
        
        assert result is not None, "체형 분석 결과가 None입니다"
        assert result.stage2 is not None, "stage2 결과가 None입니다"
        assert result.stage3 is not None, "stage3 결과가 None입니다"
        
        print(f"\n🔍 BodyTypeService 단독 테스트:")
        print(f"   - stage2 (body_type1): {result.stage2}")
        print(f"   - stage3 (body_type2): {result.stage3}")
        
        # 결과가 문자열인지 확인
        assert isinstance(result.stage2, str), "stage2는 문자열이어야 합니다"
        assert isinstance(result.stage3, str), "stage3는 문자열이어야 합니다"
        
        # 결과가 비어있지 않은지 확인
        assert len(result.stage2) > 0, "stage2 결과가 비어있습니다"
        assert len(result.stage3) > 0, "stage3 결과가 비어있습니다"
        
        print(f"✅ BodyTypeService 단독 테스트 성공")


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
