"""
LLM Schemas - LLM 팀원 전담
InbodyAnalysisReport, UserDetail, WeeklyPlan, LLM 입출력 (상태 분석 + 주간 계획) 관련 모든 스키마
"""

from pydantic import BaseModel, model_validator
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
    thread_id: Optional[str] = None      # LangGraph 대화 스레드 ID


class AnalysisReportCreate(AnalysisReportBase):
    """분석 리포트 생성 요청 스키마"""
    record_id: int
    embedding_1536: Optional[List[float]] = None  # OpenAI embedding (1536 차원)
    embedding_1024: Optional[List[float]] = None  # Ollama bge-m3 embedding (1024 차원)


class AnalysisReportResponse(AnalysisReportBase):
    """분석 리포트 응답 스키마"""
    id: int
    user_id: int
    record_id: int
    generated_at: datetime
    thread_id: Optional[str] = None
    embedding_1536: Optional[List[float]] = None  # OpenAI embedding (1536 차원)
    embedding_1024: Optional[List[float]] = None  # Ollama bge-m3 embedding (1024 차원)
    
    # LLM1 출력 결과를 요약과 전문으로 분리 (프론트엔드 표시용)
    summary: Optional[str] = None  # 종합 체형 평가 등 요약 섹션
    content: Optional[str] = None  # 전체 내용
    
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
    goal_description: Optional[str] = None  # JSON 형식으로 저장(재활, 시작체중, 목표체중)
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


class UserGoalUpdateRequest(BaseModel):
    """목표 수정 요청 스키마 (UserDetail의 goal_description 팩킹용)"""
    start_weight: Optional[float] = None
    target_weight: Optional[float] = None
    goal_type: Optional[str] = None
    goal_description: Optional[str] = None


class UserDetailResponse(UserDetailBase):
    """사용자 상세정보 응답 스키마"""
    id: int
    user_id: int
    started_at: datetime
    ended_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

    # JSON 파싱 결과를 담을 필드 추가
    target_weight: Optional[float] = None
    start_weight: Optional[float] = None
    
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
# LLM Input Schemas
# ============================================================================

class StatusAnalysisInput(BaseModel):
    """LLM1: 건강 상태 분석 입력 스키마"""
    record_id: int
    user_id: int
    measured_at: datetime
    measurements: Dict[str, Any]
    body_type1: Optional[str] = None
    body_type2: Optional[str] = None
    previous_analysis_result: Optional[str] = None


class GoalPlanInput(BaseModel):
    """LLM2: 주간 계획 생성 입력 스키마"""
    user_goal_type: Optional[str] = None
    user_goal_description: Optional[str] = None
    preferences: Optional[str] = None
    health_specifics: Optional[str] = None
    record_id: int
    user_id: int
    measured_at: datetime
    measurements: Dict[str, Any]
    status_analysis_result: Optional[str] = None
    status_analysis_id: Optional[int] = None
    body_type1: Optional[str] = None
    body_type2: Optional[str] = None


class GoalPlanRequest(BaseModel):
    """LLM2: 주간 계획 생성 요청 (프론트엔드 -> 백엔드 API)"""
    record_id: int
    user_goal_type: Optional[str] = None
    user_goal_description: Optional[str] = None
    preferences: Optional[str] = None
    health_specifics: Optional[str] = None


class GoalPlanPrepareResponse(BaseModel):
    """LLM2: 주간 계획 생성용 input 데이터 준비 응답"""
    success: bool
    message: str
    input_data: 'GoalPlanInput'


class StatusAnalysisResponse(BaseModel):
    """LLM1: 상태 분석 결과 응답"""
    report_id: int
    content: str
    summary: Optional[str] = None


class GoalPlanResponse(BaseModel):
    """LLM2: 주간 계획 생성 결과 응답 (실제 계획 생성 후)"""
    plan_id: int
    report_id: int
    weekly_plan: Dict[str, Any]
    message: Optional[str] = None



# ============================================================================
# WeeklyPlan Schemas
# ============================================================================

class WeeklyPlanBase(BaseModel):
    """주간 계획 기본 스키마"""
    week_number: int = 1
    start_date: date
    # end_date: date    daily_plans: Dict[str, Any]  # 요일별 운동/식단 JSON
    # weekly_goal: Optional[str] = None
    plan_data: Optional[Dict[str, Any]] = None  # LLM 생성 결과를 저장
    model_version: Optional[str] = None


class WeeklyPlanCreate(BaseModel):
    """주간 계획 생성 요청"""
    week_number: int = 1
    start_date: date
    end_date: date
    plan_data: Dict[str, Any]  # LLM 생성 결과 (content, raw_response 등)
    model_version: Optional[str] = None


class WeeklyPlanUpdate(BaseModel):
    """주간 계획 수정 요청"""
    # daily_plans: Optional[Dict[str, Any]] = None
    # weekly_goal: Optional[str] = None
    plan_data: Optional[Dict[str, Any]] = None
    is_completed: Optional[bool] = None


class WeeklyPlanResponse(BaseModel):
    """주간 계획 응답"""
    id: int
    user_id: int
    week_number: int
    start_date: date
    end_date: date
    plan_data: Optional[Dict[str, Any]] = None
    model_version: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# Chat / Human Feedback Schemas
# ============================================================================

class AnalysisChatRequest(BaseModel):
    """분석/계획에 대한 대화 요청 (Human Feedback)"""
    report_id: int
    message: str
    thread_id: Optional[str] = None  # LangGraph 스레드 ID (대화 맥락 유지)


class AnalysisChatResponse(BaseModel):
    """대화 응답"""
    reply: str
    thread_id: str
    updated_plan: Optional[Dict[str, Any]] = None  # 대화로 인해 계획이 변경된 경우 갱신된 데이터 반환


# ============================================================================
# Weekly Plan Chat Schemas
# ============================================================================

class WeeklyPlanChatRequest(BaseModel):
    """주간 계획 채팅 요청 스키마"""
    thread_id: str
    message: str


class WeeklyPlanChatResponse(BaseModel):
    """주간 계획 채팅 응답 스키마"""
    response: str


# ============================================================================
# LLM Interaction Schemas
# ============================================================================

class LLMInteractionBase(BaseModel):
    llm_stage: str
    source_type: Optional[str] = None
    source_id: Optional[int] = None
    category_type: Optional[str] = None
    output_text: str
    model_version: Optional[str] = None

class LLMInteractionCreate(LLMInteractionBase):
    pass

class LLMInteractionResponse(LLMInteractionBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True

# ============================================================================
# Human Feedback Schemas
# ============================================================================

class HumanFeedbackBase(BaseModel):
    llm_interaction_id: int
    feedback_category: Optional[str] = None
    feedback_text: str

class HumanFeedbackCreate(HumanFeedbackBase):
    pass

class HumanFeedbackResponse(HumanFeedbackBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True