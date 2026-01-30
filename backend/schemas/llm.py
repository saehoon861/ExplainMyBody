"""
LLM Schemas - LLM 팀원 전담
InbodyAnalysisReport, UserDetail, WeeklyPlan, LLM 입출력 (상태 분석 + 주간 계획) 관련 모든 스키마
"""

from pydantic import BaseModel
from datetime import datetime, date
from typing import Optional, Dict, Any, List


# ============================================================================
# InbodyAnalysisReport Schemas
# ============================================================================

class AnalysisReportBase(BaseModel):
    """분석 리포트 기본 스키마"""
    llm_output: str
    model_version: Optional[str] = None
    analysis_type: Optional[str] = None  # "status_analysis" 또는 "goal_plan"


class AnalysisReportCreate(AnalysisReportBase):
    """분석 리포트 생성 요청 스키마"""
    record_id: int
    embedding_1536: Optional[List[float]] = None  # OpenAI embedding (1536 차원)


class AnalysisReportResponse(AnalysisReportBase):
    """분석 리포트 응답 스키마"""
    id: int
    user_id: int
    record_id: int
    generated_at: datetime
    embedding_1536: Optional[List[float]] = None  # OpenAI embedding (1536 차원)
    
    class Config:
        from_attributes = True


# ============================================================================
# UserDetail Schemas (구 UserGoal)
# ============================================================================

class UserDetailBase(BaseModel):
    """사용자 상세정보/목표 기본 스키마"""
    goal_type: Optional[str] = None
    # target_weight: Optional[float] = None # DB 컬럼 아님, Response에만 존재
    # start_weight: Optional[float] = None # DB 컬럼 아님
    goal_description: Optional[str] = None
    preferences: Optional[str] = None
    health_specifics: Optional[str] = None
    is_active: Optional[int] = 1


class UserDetailCreate(UserDetailBase):
    """사용자 상세정보 생성 요청 스키마"""
    pass


class UserDetailUpdate(BaseModel):
    """사용자 상세정보 수정 요청 스키마"""
    goal_type: Optional[str] = None
    goal_description: Optional[str] = None
    preferences: Optional[str] = None
    health_specifics: Optional[str] = None
    is_active: Optional[int] = None
    ended_at: Optional[datetime] = None


class UserDetailResponse(UserDetailBase):
    """사용자 상세정보 응답 스키마"""
    id: int
    user_id: int
    started_at: datetime
    ended_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

    @property
    def target_weight(self) -> Optional[float]:
        """goal_description JSON에서 target_weight 추출"""
        try:
            import json
            if not self.goal_description:
                return None
            data = json.loads(self.goal_description)
            if isinstance(data, dict):
                return data.get("target_weight")
        except (json.JSONDecodeError, TypeError):
            pass
        return None

    @property
    def goal_description_text(self) -> Optional[str]:
        """goal_description JSON에서 description 텍스트만 추출 (프론트엔드 표시용)"""
        # Pydantic이 자동으로 goal_description 필드를 덮어쓰지는 않으므로, 
        # 프론트엔드가 'goal_description'을 쓸지 'goal_description_text'를 쓸지 결정 필요.
        # 여기서는 goal_description 자체를 오버라이드 하거나 새로운 필드를 제공.
        # UserDetailResponse는 Pydantic 모델이므로 @property로 getter를 만들면 json serialization 시 포함됨 (if configured).
        # 하지만 validator로 root data를 수정하는 게 더 확실함.
        return None 
    
    from pydantic import model_validator
    
    @model_validator(mode='after')
    def unpack_goal_description(self):
        try:
            import json
            if not self.goal_description:
                return self
                
            # JSON 파싱 시도
            data = json.loads(self.goal_description)
            if isinstance(data, dict):
                # JSON 형식이면 target_weight와 description 분리
                self.target_weight = data.get("target_weight")
                self.start_weight = data.get("start_weight")
                self.goal_description = data.get("description") # 원래 필드를 텍스트로 덮어씀
        except (json.JSONDecodeError, TypeError):
            # JSON 양식이 아니면 (예: 기존 데이터) 그냥 둠
            pass
        return self


# ============================================================================
# WeeklyPlan Schemas (신규)
# ============================================================================

class WeeklyPlanBase(BaseModel):
    """주간 계획 기본 스키마"""
    week_number: int
    start_date: date
    end_date: date
    plan_data: Dict[str, Any]  # JSONB 데이터
    model_version: Optional[str] = None


class WeeklyPlanCreate(WeeklyPlanBase):
    """주간 계획 생성 요청 스키마"""
    pass


class WeeklyPlanUpdate(BaseModel):
    """주간 계획 수정 요청 스키마"""
    plan_data: Optional[Dict[str, Any]] = None
    model_version: Optional[str] = None


class WeeklyPlanResponse(WeeklyPlanBase):
    """주간 계획 응답 스키마"""
    id: int
    user_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# LLM Input/Output Schemas - 상태 분석 (LLM1)
# ============================================================================

class StatusAnalysisInput(BaseModel):
    """
    LLM1: 건강 상태 분석용 Input 스키마
    - LLM 팀원이 API 연동 시 이 데이터를 사용
    """
    record_id: int
    user_id: int
    measured_at: datetime
    measurements: Dict[str, Any]  # 인바디 데이터 전부 + body_type1, 2가 포함됨
    # body_type1, body_type2 필드 삭제!

    class Config:
        from_attributes = True


class StatusAnalysisResponse(BaseModel):
    """LLM1 응답: 프론트엔드에서 LLM API 호출에 사용할 input 반환"""
    success: bool = True
    message: str = "LLM input 데이터 준비 완료. 프론트엔드에서 LLM API를 호출하세요."
    input_data: StatusAnalysisInput


# ============================================================================
# LLM Input/Output Schemas - 주간 계획 (LLM2)
# ============================================================================

class GoalPlanInput(BaseModel):
    """
    LLM2: 주간 계획서 생성용 Input 스키마
    - LLM 팀원이 API 연동 시 이 데이터를 사용
    """
    # 사용자 요구사항
    user_goal_type: Optional[str] = None
    user_goal_description: Optional[str] = None

    # 최신 건강 기록
    record_id: int
    user_id: int
    measured_at: datetime
    measurements: Dict[str, Any]  # 인바디 데이터 전부 + body_type1, 2가 포함됨
    # body_type1, body_type2 필드 삭제!

    # LLM1(status_analysis)의 분석 결과
    status_analysis_result: Optional[str] = None
    status_analysis_id: Optional[int] = None

    class Config:
        from_attributes = True


class GoalPlanResponse(BaseModel):
    """LLM2 응답: 프론트엔드에서 LLM API 호출에 사용할 input 반환"""
    success: bool = True
    message: str = "LLM input 데이터 준비 완료. 프론트엔드에서 LLM API를 호출하세요."
    input_data: GoalPlanInput


class GoalPlanRequest(BaseModel):
    """LLM2 요청: 주간 계획서 생성을 위한 사용자 입력"""
    record_id: int  # 프론트에서 선택한 건강 기록 ID
    user_goal_type: Optional[str] = None  # 목표 타입 (다이어트, 근육 증가 등)
    user_goal_description: Optional[str] = None  # 상세 목표 설명
