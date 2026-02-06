"""
InBody 데이터 Pydantic 스키마
OCR 추출 데이터 전체를 검증하는 모델
"""

from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, Dict, Any


class BasicInfo(BaseModel):
    """기본정보"""
    신장: float = Field(..., gt=50, lt=300, description="신장 (cm)")
    연령: int = Field(..., gt=0, lt=150, description="연령 (세)")
    성별: str = Field(..., pattern="^(남성|여성|남|여|male|female|Male|Female)$", description="성별")
    
    @field_validator('성별')
    @classmethod
    def normalize_gender(cls, v: str) -> str:
        """성별 정규화: 남/여/male/female → 남성/여성"""
        v_low = v.lower()
        if v == "남" or v_low == "male":
            return "남성"
        elif v == "여" or v_low == "female":
            return "여성"
        return v


class BodyComposition(BaseModel):
    """체성분"""
    체수분: Optional[float] = Field(None, gt=0, description="체수분 (L)")
    단백질: Optional[float] = Field(None, gt=0, description="단백질 (kg)")
    무기질: Optional[float] = Field(None, gt=0, description="무기질 (kg)")
    체지방: Optional[float] = Field(None, gt=0, description="체지방 (kg)")


class WeightManagement(BaseModel):
    """체중관리"""
    체중: float = Field(..., gt=10, lt=500, description="체중 (kg)")
    골격근량: float = Field(..., gt=0, lt=200, description="골격근량 (kg)")
    체지방량: Optional[float] = Field(None, gt=0, description="체지방량 (kg)")
    적정체중: Optional[float] = Field(None, gt=0, description="적정체중 (kg)")
    체중조절: Optional[float] = Field(None, description="체중조절 (kg)")
    지방조절: Optional[float] = Field(None, description="지방조절 (kg)")
    근육조절: Optional[float] = Field(None, description="근육조절 (kg)")


class ObesityAnalysis(BaseModel):
    """비만분석"""
    BMI: float = Field(..., gt=10, lt=100, description="체질량지수")
    체지방률: float = Field(..., ge=0, le=100, description="체지방률 (%)")
    복부지방률: Optional[float] = Field(None, ge=0, le=10, description="복부지방률")
    내장지방레벨: Optional[int] = Field(None, ge=1, le=20, description="내장지방레벨")
    비만도: Optional[int] = Field(None, description="비만도 (%)")


class ResearchItems(BaseModel):
    """연구항목"""
    제지방량: Optional[float] = Field(None, gt=0, description="제지방량 (kg)")
    기초대사량: Optional[int] = Field(None, gt=0, description="기초대사량 (kcal)")
    권장섭취열량: Optional[int] = Field(None, gt=0, description="권장섭취열량 (kcal)")


class SegmentalMuscleAnalysis(BaseModel):
    """부위별근육분석"""
    왼쪽팔: Optional[str] = Field(None, description="왼쪽팔 근육 평가")
    오른쪽팔: Optional[str] = Field(None, description="오른쪽팔 근육 평가")
    복부: Optional[str] = Field(None, description="복부 근육 평가")
    왼쪽하체: Optional[str] = Field(None, description="왼쪽하체 근육 평가")
    오른쪽하체: Optional[str] = Field(None, description="오른쪽하체 근육 평가")


class SegmentalFatAnalysis(BaseModel):
    """부위별체지방분석"""
    왼쪽팔: Optional[str] = Field(None, description="왼쪽팔 체지방 평가")
    오른쪽팔: Optional[str] = Field(None, description="오른쪽팔 체지방 평가")
    복부: Optional[str] = Field(None, description="복부 체지방 평가")
    왼쪽하체: Optional[str] = Field(None, description="왼쪽하체 체지방 평가")
    오른쪽하체: Optional[str] = Field(None, description="오른쪽하체 체지방 평가")


class InBodyData(BaseModel):
    """
    인바디 OCR 추출 데이터 (전체)

    사용자가 제공한 표준 JSON 구조에 맞춘 Pydantic 모델
    null 값은 사용자 검증이 필요함
    """
    기본정보: BasicInfo
    체성분: BodyComposition
    체중관리: WeightManagement
    비만분석: ObesityAnalysis
    연구항목: ResearchItems
    부위별근육분석: SegmentalMuscleAnalysis
    부위별체지방분석: SegmentalFatAnalysis
    body_type1: Optional[str] = Field(None, description="1차 체형 분류")
    body_type2: Optional[str] = Field(None, description="2차 체형 분류")
    
    @model_validator(mode='after')
    def check_null_values(self) -> 'InBodyData':
        """
        null 값이 있는 필드를 확인하고 경고
        프론트엔드에서 사용자에게 검증을 요청해야 함
        """
        null_fields = []
        
        # 각 섹션의 null 필드 확인
        for section_name in ['체성분', '체중관리', '비만분석', '연구항목', '부위별근육분석', '부위별체지방분석']:
            section = getattr(self, section_name)
            for field_name, value in section.model_dump().items():
                if value is None:
                    null_fields.append(f"{section_name}.{field_name}")
        
        if null_fields:
            print(f"⚠️  검증 필요한 null 필드: {', '.join(null_fields)}")
        
        return self
    
    def get_null_fields(self) -> Dict[str, list]:
        """
        null 값인 필드 목록 반환 (프론트엔드에서 사용)
        
        Returns:
            섹션별 null 필드 목록
        """
        null_fields_by_section = {}
        
        for section_name in ['기본정보', '체성분', '체중관리', '비만분석', '연구항목', '부위별근육분석', '부위별체지방분석']:
            section = getattr(self, section_name)
            null_fields = [field for field, value in section.model_dump().items() if value is None]
            if null_fields:
                null_fields_by_section[section_name] = null_fields
        
        return null_fields_by_section
    
    class Config:
        json_schema_extra = {
            "example": {
                "기본정보": {
                    "신장": 170,
                    "연령": 30,
                    "성별": "남성"
                },
                "체성분": {
                    "체수분": 41.7,
                    "단백질": 11.4,
                    "무기질": 3.99,
                    "체지방": 20.6
                },
                "체중관리": {
                    "체중": 77.7,
                    "골격근량": 32.5,
                    "체지방량": 20.6,
                    "적정체중": 67.2,
                    "체중조절": None,
                    "지방조절": -10.5,
                    "근육조절": 0.0
                },
                "비만분석": {
                    "BMI": 26.9,
                    "체지방률": 26.5,
                    "복부지방률": 0.93,
                    "내장지방레벨": 8,
                    "비만도": 122
                },
                "연구항목": {
                    "제지방량": 57.1,
                    "기초대사량": 1603,
                    "권장섭취열량": 2267
                },
                "부위별근육분석": {
                    "왼쪽팔": "표준",
                    "오른쪽팔": "표준",
                    "복부": "표준",
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
        }
