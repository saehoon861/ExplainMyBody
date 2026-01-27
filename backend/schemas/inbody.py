"""
InBody 데이터 Pydantic 스키마
OCR 추출 데이터 전체를 검증하는 모델
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional


class InBodyData(BaseModel):
    """
    인바디 OCR 추출 데이터 (전체)
    
    extract_and_match의 반환값을 Pydantic 모델로 변환
    사용자 검증 단계에서 사용
    """
    # 기본 정보 (필수)
    성별: str = Field(..., pattern="^(남성|여성|남|여)$", description="성별")
    연령: int = Field(..., gt=0, lt=150, description="연령 (세)")
    신장: float = Field(..., gt=50, lt=300, description="신장 (cm)")
    
    # 체성분 분석 (필수)
    체중: float = Field(..., gt=10, lt=500, description="체중 (kg)")
    BMI: float = Field(..., gt=10, lt=100, description="체질량지수")
    체지방률: float = Field(..., ge=0, le=100, description="체지방률 (%)")
    골격근량: float = Field(..., gt=0, lt=200, description="골격근량 (kg)")
    
    # 체성분 상세 (선택적)
    체수분: Optional[float] = Field(None, gt=0, description="체수분 (L)")
    단백질: Optional[float] = Field(None, gt=0, description="단백질 (kg)")
    무기질: Optional[float] = Field(None, gt=0, description="무기질 (kg)")
    체지방: Optional[float] = Field(None, gt=0, description="체지방 (kg)")
    체지방량: Optional[float] = Field(None, gt=0, description="체지방량 (kg)")
    제지방량: Optional[float] = Field(None, gt=0, description="제지방량 (kg)")
    
    # 체중 조절 (선택적)
    적정체중: Optional[float] = Field(None, gt=0, description="적정체중 (kg)")
    체중조절: Optional[float] = Field(None, description="체중조절 (kg)")
    지방조절: Optional[float] = Field(None, description="지방조절 (kg)")
    근육조절: Optional[float] = Field(None, description="근육조절 (kg)")
    
    # 복부 및 내장지방 (선택적)
    복부지방률: Optional[float] = Field(None, ge=0, le=10, description="복부지방률")
    내장지방레벨: Optional[int] = Field(None, ge=1, le=20, description="내장지방레벨")
    
    # 기타 (선택적)
    기초대사량: Optional[int] = Field(None, gt=0, description="기초대사량 (kcal)")
    비만도: Optional[int] = Field(None, description="비만도 (%)")
    권장섭취열량: Optional[int] = Field(None, gt=0, description="권장섭취열량 (kcal)")
    
    # 부위별 평가 (선택적 - 문자열: "표준", "표준이상", "표준이하")
    왼쪽팔_근육: Optional[str] = Field(None, description="왼쪽팔 근육 평가")
    오른쪽팔_근육: Optional[str] = Field(None, description="오른쪽팔 근육 평가")
    왼쪽팔_체지방: Optional[str] = Field(None, description="왼쪽팔 체지방 평가")
    오른쪽팔_체지방: Optional[str] = Field(None, description="오른쪽팔 체지방 평가")
    복부_근육: Optional[str] = Field(None, description="복부 근육 평가")
    복부_체지방: Optional[str] = Field(None, description="복부 체지방 평가")
    왼쪽하체_근육: Optional[str] = Field(None, description="왼쪽하체 근육 평가")
    오른쪽하체_근육: Optional[str] = Field(None, description="오른쪽하체 근육 평가")
    왼쪽하체_체지방: Optional[str] = Field(None, description="왼쪽하체 체지방 평가")
    오른쪽하체_체지방: Optional[str] = Field(None, description="오른쪽하체 체지방 평가")
    
    @field_validator('성별')
    @classmethod
    def normalize_gender(cls, v: str) -> str:
        """성별 정규화: 남/여 → 남성/여성"""
        if v == "남":
            return "남성"
        elif v == "여":
            return "여성"
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "성별": "남성",
                "연령": 25,
                "신장": 175.0,
                "체중": 70.0,
                "BMI": 23.1,
                "체지방률": 15.2,
                "골격근량": 32.5,
                "체수분": 42.3,
                "단백질": 11.2,
                "무기질": 3.5,
                "체지방": 10.6
            }
        }
