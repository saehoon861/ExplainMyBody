"""
체형 분석 Pydantic 스키마
InBody 데이터에서 체형 분석에 필요한 필드만 추출
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict
from .inbody import InBodyData


class MuscleFatSegment(BaseModel):
    """부위별 근육/지방 데이터 (수치)"""
    왼팔: float = Field(..., gt=0, description="왼팔 근육/지방량 (kg)")
    오른팔: float = Field(..., gt=0, description="오른팔 근육/지방량 (kg)")
    몸통: float = Field(..., gt=0, description="몸통 근육/지방량 (kg)")
    왼다리: float = Field(..., gt=0, description="왼다리 근육/지방량 (kg)")
    오른다리: float = Field(..., gt=0, description="오른다리 근육/지방량 (kg)")


class BodyTypeAnalysisInput(BaseModel):
    """
    체형 분석 입력 데이터
    
    InBodyData에서 필요한 필드만 추출하여 생성
    모든 필수 필드가 없으면 Pydantic ValidationError 발생
    """
    성별: str = Field(..., pattern="^(남성|여성)$", description="성별")
    연령: int = Field(..., gt=0, lt=150, description="연령 (세)")
    신장: float = Field(..., gt=0, lt=300, description="신장 (cm)")
    체중: float = Field(..., gt=0, lt=500, description="체중 (kg)")
    BMI: float = Field(..., gt=0, lt=100, description="체질량지수")
    체지방률: float = Field(..., ge=0, le=100, description="체지방률 (%)")
    골격근량: float = Field(..., gt=0, description="골격근량 (kg)")
    
    # 선택적 필드 (부위별 수치 데이터)
    muscle_seg: Optional[MuscleFatSegment] = Field(None, description="부위별 근육량")
    fat_seg: Optional[MuscleFatSegment] = Field(None, description="부위별 지방량")
    
    @classmethod
    def from_inbody_data(
        cls, 
        inbody: InBodyData,
        muscle_seg: Optional[Dict[str, float]] = None,
        fat_seg: Optional[Dict[str, float]] = None
    ):
        """
        InBodyData에서 체형 분석 입력 생성
        
        Args:
            inbody: InBodyData Pydantic 모델 (중첩 구조)
            muscle_seg: 부위별 근육량 수치 (선택적)
            fat_seg: 부위별 지방량 수치 (선택적)
            
        Returns:
            BodyTypeAnalysisInput: 체형 분석 입력 모델
        """
        return cls(
            성별=inbody.기본정보.성별,
            연령=inbody.기본정보.연령,
            신장=inbody.기본정보.신장,
            체중=inbody.체중관리.체중,
            BMI=inbody.비만분석.BMI,
            체지방률=inbody.비만분석.체지방률,
            골격근량=inbody.체중관리.골격근량,
            muscle_seg=MuscleFatSegment(**muscle_seg) if muscle_seg else None,
            fat_seg=MuscleFatSegment(**fat_seg) if fat_seg else None
        )
    
    class Config:
        json_schema_extra = {
            "example": {
                "성별": "남성",
                "연령": 25,
                "신장": 175.0,
                "체중": 70.0,
                "BMI": 23.1,
                "체지방률": 15.2,
                "골격근량": 25.4,
                "muscle_seg": {
                    "왼팔": 2.1,
                    "오른팔": 2.2,
                    "몸통": 10.3,
                    "왼다리": 12.4,
                    "오른다리": 12.5
                },
                "fat_seg": {
                    "왼팔": 1.1,
                    "오른팔": 1.2,
                    "몸통": 4.3,
                    "왼다리": 6.4,
                    "오른다리": 6.5
                }
            }
        }


class BodyTypeAnalysisOutput(BaseModel):
    """체형 분석 결과"""
    stage2: str = Field(..., description="근육 보정 체형 (예: 비만형, 표준형, 근육형)")
    stage3: str = Field(..., description="최종 체형 (예: 표준형, 상체발달형)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "stage2": "비만형",
                "stage3": "표준형"
            }
        }
