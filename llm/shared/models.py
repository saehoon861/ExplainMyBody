"""
Pydantic 데이터 모델
"""

from typing import Optional, Dict, List
from pydantic import BaseModel, Field
from datetime import datetime


# ==================== InBody 관련 ====================

class InBodyMeasurements(BaseModel):
    """InBody 측정 데이터"""

    # 기본 정보
    성별: str
    나이: int = Field(ge=1, le=120)
    신장: float = Field(ge=100, le=250)
    체중: float = Field(ge=20, le=300)

    # 체성분
    무기질: Optional[float] = None
    체수분: Optional[float] = None
    단백질: Optional[float] = None
    체지방: Optional[float] = None
    골격근량: float

    # 비만 지표
    BMI: float
    체지방률: float
    복부지방률: Optional[float] = None
    내장지방레벨: Optional[int] = None
    비만도: Optional[float] = None

    # 대사
    기초대사량: Optional[int] = None
    적정체중: Optional[float] = None
    권장섭취열량: Optional[int] = None

    # 조절
    체중조절: Optional[float] = None
    지방조절: Optional[float] = None
    근육조절: Optional[float] = None

    # 부위별
    근육_부위별등급: Dict[str, str]
    체지방_부위별등급: Optional[Dict[str, str]] = None

    # Stage 분석 (규칙 기반)
    stage2_근육보정체형: Optional[str] = None
    stage3_상하체밸런스: Optional[str] = None


class InBodyAnalysisResult(BaseModel):
    """인바디 분석 결과"""

    user_id: int
    record_id: int
    analysis_text: str
    embedding: Optional[List[float]] = None
    model_version: str
    generated_at: datetime = Field(default_factory=datetime.now)


# ==================== 사용자 목표 및 선호도 ====================

class UserGoal(BaseModel):
    """사용자 목표"""

    goal_type: str = Field(
        ...,
        description="목표 유형: 체중감량, 근육증가, 체력향상, 건강유지 등"
    )
    target_weight: Optional[float] = Field(None, description="목표 체중 (kg)")
    target_body_fat: Optional[float] = Field(None, description="목표 체지방률 (%)")
    target_muscle: Optional[float] = Field(None, description="목표 골격근량 (kg)")
    deadline: Optional[str] = Field(None, description="목표 달성 기한 (예: 3개월)")
    priority: str = Field(default="medium", description="우선순위: high, medium, low")


class UserPreferences(BaseModel):
    """사용자 운동 및 식단 선호도"""

    # 운동 선호도
    preferred_exercise_types: List[str] = Field(
        default_factory=list,
        description="선호하는 운동 유형: 웨이트, 유산소, 필라테스, 요가 등"
    )
    exercise_frequency: Optional[int] = Field(None, ge=1, le=7, description="주간 운동 횟수")
    exercise_duration: Optional[int] = Field(None, description="1회 운동 시간 (분)")
    exercise_intensity: str = Field(default="medium", description="운동 강도: low, medium, high")

    # 식단 선호도
    dietary_restrictions: List[str] = Field(
        default_factory=list,
        description="식단 제한사항: 채식, 할랄, 유당불내증, 견과류 알레르기 등"
    )
    preferred_cuisine: List[str] = Field(
        default_factory=list,
        description="선호 음식: 한식, 양식, 일식 등"
    )
    disliked_foods: List[str] = Field(
        default_factory=list,
        description="비선호 음식"
    )
    meal_frequency: Optional[int] = Field(None, ge=2, le=6, description="하루 식사 횟수")

    # 건강 특이사항
    health_conditions: List[str] = Field(
        default_factory=list,
        description="건강 특이사항: 당뇨, 고혈압, 관절염 등"
    )
    injuries: List[str] = Field(
        default_factory=list,
        description="부상 이력: 허리 디스크, 무릎 연골 등"
    )
    medications: List[str] = Field(
        default_factory=list,
        description="복용 중인 약물"
    )


class UserProfile(BaseModel):
    """사용자 종합 프로필"""

    user_id: int
    username: str
    email: str

    # 목표
    goals: List[UserGoal]

    # 선호도
    preferences: UserPreferences

    # 최신 인바디 분석
    latest_inbody_analysis: Optional[InBodyAnalysisResult] = None


# ==================== 주간 계획 ====================

class Exercise(BaseModel):
    """운동 항목"""

    name: str = Field(..., description="운동 이름")
    category: str = Field(..., description="운동 카테고리: 웨이트, 유산소, 스트레칭 등")
    target_muscle: Optional[str] = Field(None, description="목표 근육: 가슴, 등, 다리 등")
    sets: Optional[int] = Field(None, description="세트 수")
    reps: Optional[str] = Field(None, description="반복 횟수 또는 시간")
    rest_seconds: Optional[int] = Field(None, description="세트 간 휴식 시간")
    notes: Optional[str] = Field(None, description="추가 설명")


class Meal(BaseModel):
    """식사 항목"""

    meal_type: str = Field(..., description="식사 유형: 아침, 점심, 저녁, 간식")
    foods: List[str] = Field(..., description="음식 목록")
    calories: Optional[int] = Field(None, description="칼로리 (kcal)")
    protein_g: Optional[float] = Field(None, description="단백질 (g)")
    carbs_g: Optional[float] = Field(None, description="탄수화물 (g)")
    fat_g: Optional[float] = Field(None, description="지방 (g)")
    notes: Optional[str] = Field(None, description="추가 설명")


class DayPlan(BaseModel):
    """하루 계획"""

    day_of_week: str = Field(..., description="요일: 월요일, 화요일 등")
    exercises: List[Exercise] = Field(default_factory=list)
    meals: List[Meal] = Field(default_factory=list)
    total_calories: Optional[int] = Field(None, description="하루 총 칼로리")
    notes: Optional[str] = Field(None, description="하루 전체 노트")


class WeeklyPlan(BaseModel):
    """주간 계획"""

    user_id: int
    week_number: int = Field(..., description="주차")
    start_date: str = Field(..., description="시작 날짜")
    end_date: str = Field(..., description="종료 날짜")

    daily_plans: List[DayPlan] = Field(..., description="요일별 계획")

    weekly_summary: Optional[str] = Field(None, description="주간 요약")
    weekly_goal: Optional[str] = Field(None, description="주간 목표")
    tips: Optional[List[str]] = Field(None, description="주간 팁")

    model_version: str
    generated_at: datetime = Field(default_factory=datetime.now)


# ==================== API 요청/응답 ====================

class InBodyAnalysisRequest(BaseModel):
    """인바디 분석 요청"""

    user_id: int
    measurements: InBodyMeasurements
    source: str = Field(default="manual", description="데이터 소스: manual, inbody_ocr 등")


class InBodyAnalysisResponse(BaseModel):
    """인바디 분석 응답"""

    success: bool
    record_id: Optional[int] = None
    analysis_id: Optional[int] = None
    analysis_text: Optional[str] = None
    error: Optional[str] = None


class WeeklyPlanRequest(BaseModel):
    """주간 계획 생성 요청"""

    user_id: int
    goals: List[UserGoal]
    preferences: UserPreferences
    week_number: int = Field(default=1, description="주차")
    start_date: Optional[str] = Field(None, description="시작 날짜 (YYYY-MM-DD)")


class WeeklyPlanResponse(BaseModel):
    """주간 계획 생성 응답"""

    success: bool
    plan_id: Optional[int] = None
    weekly_plan: Optional[WeeklyPlan] = None
    error: Optional[str] = None
