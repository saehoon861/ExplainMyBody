"""
Pydantic 스키마 및 서비스 통합 테스트
"""

import sys
sys.path.append('/home/user/ExplainMyBody/backend')

from schemas.inbody import InBodyData
from schemas.body_type import BodyTypeAnalysisInput, BodyTypeAnalysisOutput
from pydantic import ValidationError

print("=" * 60)
print("Pydantic 스키마 검증 테스트")
print("=" * 60)

# 테스트 1: 정상 데이터 검증
print("\n[테스트 1] 정상 데이터 검증")
try:
    valid_data = {
        "성별": "남성",
        "연령": 25,
        "신장": 175.0,
        "체중": 70.0,
        "BMI": 23.1,
        "체지방률": 15.2,
        "골격근량": 32.5
    }
    inbody = InBodyData(**valid_data)
    print(f"✅ InBodyData 검증 성공")
    print(f"   성별: {inbody.성별}, 연령: {inbody.연령}, BMI: {inbody.BMI}")
except ValidationError as e:
    print(f"❌ 검증 실패: {e}")

# 테스트 2: 이상치 데이터 검증 (나이: 200)
print("\n[테스트 2] 이상치 데이터 검증 (연령: 200)")
try:
    invalid_data = {
        "성별": "남성",
        "연령": 200,  # 이상치
        "신장": 175.0,
        "체중": 70.0,
        "BMI": 23.1,
        "체지방률": 15.2,
        "골격근량": 32.5
    }
    inbody = InBodyData(**invalid_data)
    print(f"❌ 검증이 통과되면 안됨")
except ValidationError as e:
    print(f"✅ 예상대로 검증 실패 감지")
    print(f"   에러: {e.errors()[0]['msg']}")

# 테스트 3: 필수 필드 누락
print("\n[테스트 3] 필수 필드 누락 (체중 없음)")
try:
    incomplete_data = {
        "성별": "남성",
        "연령": 25,
        "신장": 175.0,
        # 체중 누락
        "BMI": 23.1,
        "체지방률": 15.2,
        "골격근량": 32.5
    }
    inbody = InBodyData(**incomplete_data)
    print(f"❌ 검증이 통과되면 안됨")
except ValidationError as e:
    print(f"✅ 예상대로 검증 실패 감지")
    print(f"   누락 필드: {e.errors()[0]['loc']}")

# 테스트 4: BodyTypeAnalysisInput 변환
print("\n[테스트 4] InBodyData → BodyTypeAnalysisInput 변환")
try:
    inbody = InBodyData(**valid_data)
    body_type_input = BodyTypeAnalysisInput.from_inbody_data(inbody)
    print(f"✅ 변환 성공")
    print(f"   성별: {body_type_input.성별}, BMI: {body_type_input.BMI}")
except Exception as e:
    print(f"❌ 변환 실패: {e}")

# 테스트 5: BodyTypeAnalysisOutput 생성
print("\n[테스트 5] BodyTypeAnalysisOutput 생성")
try:
    output = BodyTypeAnalysisOutput(stage2="비만형", stage3="표준형")
    print(f"✅ 출력 모델 생성 성공")
    print(f"   stage2: {output.stage2}, stage3: {output.stage3}")
except Exception as e:
    print(f"❌ 생성 실패: {e}")

print("\n" + "=" * 60)
print("테스트 완료")
print("=" * 60)
