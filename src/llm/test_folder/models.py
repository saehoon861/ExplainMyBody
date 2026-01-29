"""
Pydantic Models for ExplainMyBody
"""

from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Any, Optional, Union
from enum import Enum


# ============================================================
# 1. Enum - Body Type Constants
# ============================================================

class Sex(str, Enum):
    MALE = "남자"
    FEMALE = "여자"


class BMICategory(str, Enum):
    UNDERWEIGHT = "저체중"
    NORMAL = "정상"
    OVERWEIGHT = "과체중"
    OBESE_1 = "비만1단계"
    OBESE_2 = "비만2단계"
    MORBID_OBESE = "고도비만"


class FatCategory(str, Enum):
    BELOW_STANDARD = "표준미만"
    STANDARD = "표준"
    OVERWEIGHT = "과체중"
    OBESE = "비만"


class MuscleLevel(str, Enum):
    VERY_HIGH = "근육 매우 많음"
    HIGH = "근육 많음"
    SUFFICIENT = "근육 충분"
    NORMAL = "근육 보통"
    LOW = "근육 적음"


class PartLevel(str, Enum):
    ABOVE_STANDARD = "표준이상"
    STANDARD = "표준"
    BELOW_STANDARD = "표준미만"


# ============================================================
# 2. Input Models - InBody Profile
# ============================================================

class InBodyProfile(BaseModel):
    """InBody measurement profile"""
    id: Optional[int] = None
    name: str = Field(..., min_length=1, max_length=50)
    sex: str
    age: int = Field(..., ge=1, le=120)
    height_cm: float = Field(..., ge=100, le=250)
    weight_kg: float = Field(..., ge=20, le=300)
    bmi: float = Field(..., ge=10, le=60)
    fat_rate: float = Field(..., ge=0, le=70)
    smm: float = Field(..., ge=5, le=100, description="Skeletal Muscle Mass (kg)")
    muscle_seg: dict[str, float]
    fat_seg: Optional[dict[str, float]] = None
    description: Optional[str] = None

    @field_validator("bmi")
    @classmethod
    def validate_bmi(cls, v):
        return round(v, 1)


# ============================================================
# 3. Analysis Result Models
# ============================================================

class BasicInfo(BaseModel):
    """Basic body info"""
    sex: str
    age: int
    weight_kg: float


class Stage12Result(BaseModel):
    """Stage 1-2 analysis result"""
    bmi: float
    bmi_category: str
    fat_category: str
    smm_ratio: float
    muscle_level: str
    stage1_type: str
    stage2_type: str


class BodyAnalysisResult(BaseModel):
    """Full body analysis result"""
    basic_info: BasicInfo
    stage1_2: Stage12Result
    muscle_seg: dict[str, str]
    fat_seg: Optional[dict[str, str]] = None
    stage3: str


# ============================================================
# 4. LLM Output Models (Flexible for LLM quirks)
# ============================================================

class BodyAnalysisSummary(BaseModel):
    """Body analysis summary"""
    body_type: str
    strengths: list[str]
    improvement_areas: list[str]


class Exercise(BaseModel):
    """
    Exercise info - handles both rep-based and time-based exercises

    LLM이 "30초", "1분" 같은 시간 기반 값을 반환할 수 있으므로
    reps, sets 필드를 Union[int, str]로 유연하게 처리
    """
    name: str
    sets: Union[int, str] = Field(default=3, description="세트 수 또는 시간")
    reps: Union[int, str] = Field(default=12, description="횟수(12) 또는 시간(30초)")
    rest_seconds: Union[int, str] = Field(default=60, description="휴식 시간")
    note: Optional[str] = None
    
    @field_validator("reps", mode="before")
    @classmethod
    def parse_reps(cls, v):
        """시간 기반 값은 문자열로 유지, 숫자는 int로 변환"""
        if isinstance(v, int):
            return v
        if isinstance(v, str):
            # 순수 숫자 문자열이면 int로 변환
            if v.isdigit():
                return int(v)
            # "30초", "1분" 등은 문자열 유지
            return v
        return v
    
    @field_validator("rest_seconds", mode="before")
    @classmethod
    def parse_rest(cls, v):
        """휴식 시간도 유연하게 처리"""
        if isinstance(v, int):
            return v
        if isinstance(v, str):
            if v.isdigit():
                return int(v)
            return v
        return v


class Cardio(BaseModel):
    """Cardio exercise info"""
    type: str
    duration_minutes: Union[int, str] = Field(default=20)
    intensity: Optional[str] = "중강도"
    
    @field_validator("duration_minutes", mode="before")
    @classmethod
    def parse_duration(cls, v):
        if isinstance(v, int):
            return v
        if isinstance(v, str):
            if v.isdigit():
                return int(v)
            # "20~30" 같은 범위도 문자열로 유지
            return v
        return v


class DaySchedule(BaseModel):
    """Daily exercise schedule"""
    day: str
    focus: str
    duration_minutes: Union[int, str] = Field(default=60)
    exercises: list[Exercise]
    cardio: Optional[Cardio] = None
    
    @field_validator("duration_minutes", mode="before")
    @classmethod
    def parse_duration(cls, v):
        if isinstance(v, int):
            return v
        if isinstance(v, str):
            if v.isdigit():
                return int(v)
            return v
        return v


class ExercisePlan(BaseModel):
    """Weekly exercise plan"""
    weekly_goal: str
    recommended_frequency: str
    weekly_schedule: list[DaySchedule]


class Macros(BaseModel):
    """Macro nutrients"""
    protein_g: Union[int, float] = Field(..., ge=0)
    carbs_g: Union[int, float] = Field(..., ge=0)
    fat_g: Union[int, float] = Field(..., ge=0)


class Meal(BaseModel):
    """Meal info"""
    meal: str
    time: Optional[str] = None
    menu: list[str]
    calories: Union[int, str] = Field(default=0)
    
    @field_validator("calories", mode="before")
    @classmethod
    def parse_calories(cls, v):
        if isinstance(v, int):
            return v
        if isinstance(v, str):
            if v.isdigit():
                return int(v)
            return v
        return v


class DietPlan(BaseModel):
    """Diet plan"""
    daily_calorie_target: Union[int, str] = Field(...)
    macros: Macros
    meal_plan: list[Meal]
    guidelines: list[str]
    foods_to_avoid: Optional[list[str]] = None
    recommended_foods: Optional[list[str]] = None
    
    @field_validator("daily_calorie_target", mode="before")
    @classmethod
    def parse_calories(cls, v):
        if isinstance(v, int):
            return v
        if isinstance(v, str):
            # "1800~2000" 같은 범위도 허용
            cleaned = v.replace(",", "")
            if cleaned.isdigit():
                return int(cleaned)
            return v
        return v


class LLMRecommendation(BaseModel):
    """LLM generated recommendation"""
    body_analysis_summary: BodyAnalysisSummary
    exercise_plan: ExercisePlan
    diet_plan: DietPlan
    weekly_tips: list[str]


# ============================================================
# 5. Pipeline Result Model
# ============================================================

class ProfileSummary(BaseModel):
    """Profile summary"""
    name: Optional[str]
    sex: str
    age: int
    height_cm: Optional[float]
    weight_kg: float


class PipelineResult(BaseModel):
    """Full pipeline result"""
    profile: ProfileSummary
    analysis: BodyAnalysisResult
    recommendations: Optional[Any] = None
    generated_at: str
