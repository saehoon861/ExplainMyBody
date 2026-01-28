from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict

class BasicInfo(BaseModel):
    신장: Optional[str] = None
    연령: Optional[str] = None
    성별: Optional[str] = None

class BodyComposition(BaseModel):
    체수분: Optional[str] = None
    단백질: Optional[str] = None
    무기질: Optional[str] = None
    체지방: Optional[str] = None

class WeightControl(BaseModel):
    체중: Optional[str] = None
    골격근량: Optional[str] = None
    체지방량: Optional[str] = None
    적정체중: Optional[str] = None
    체중조절: Optional[str] = None
    지방조절: Optional[str] = None
    근육조절: Optional[str] = None

class ObesityAnalysis(BaseModel):
    BMI: Optional[str] = None
    체지방률: Optional[str] = None
    복부지방률: Optional[str] = None
    내장지방레벨: Optional[str] = None
    비만도: Optional[str] = None

class ResearchItems(BaseModel):
    제지방량: Optional[str] = None
    기초대사량: Optional[str] = None
    권장섭취열량: Optional[str] = None

class MuscleEvaluation(BaseModel):
    왼쪽팔: Optional[str] = None
    오른쪽팔: Optional[str] = None
    복부: Optional[str] = None
    왼쪽하체: Optional[str] = None
    오른쪽하체: Optional[str] = None

class FatEvaluation(BaseModel):
    왼쪽팔: Optional[str] = None
    오른쪽팔: Optional[str] = None
    복부: Optional[str] = None
    왼쪽하체: Optional[str] = None
    오른쪽하체: Optional[str] = None

class InBodyResult(BaseModel):
    기본정보: BasicInfo
    체성분: BodyComposition
    체중관리: WeightControl
    비만분석: ObesityAnalysis
    연구항목: ResearchItems
    부위별근육분석: MuscleEvaluation
    부위별체지방분석: FatEvaluation

    @classmethod
    def from_dict(cls, data: Dict):
        """딕셔너리 데이터를 받아 모델 인스턴스 생성"""
        return cls(**data)
