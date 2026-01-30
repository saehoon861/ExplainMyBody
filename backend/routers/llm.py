from fastapi import APIRouter, Depends, HTTPException
from services.llm.llm_service import LLMService
from schemas.llm import StatusAnalysisInput, GoalPlanInput, ChatRequest, LLMResponse

router = APIRouter(prefix="/api/llm", tags=["LLM"])

def get_llm_service():
    """Dependency Injection을 위한 팩토리 함수"""
    return LLMService()

@router.post("/analysis")
async def analyze_health_status(
    input_data: StatusAnalysisInput,
    service: LLMService = Depends(get_llm_service)
):
    """LLM을 통한 건강 상태 분석 요청"""
    try:
        # 1. LLM 서비스 호출 (분석 및 임베딩 생성)
        result = await service.call_status_analysis_llm(input_data)
        
        # 2. TODO: Repository를 호출하여 result(분석글, 임베딩)를 DB에 저장하는 로직 필요
        # 예: await analysis_repo.save_analysis(result)
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analysis/{thread_id}/chat")
async def chat_about_analysis(
    thread_id: str,
    chat_req: ChatRequest,
    service: LLMService = Depends(get_llm_service)
):
    """건강 분석 결과에 대한 추가 Q&A"""
    response = await service.chat_with_analysis(thread_id, chat_req.message)
    return {"response": response}

@router.post("/plan")
async def create_weekly_plan(
    input_data: GoalPlanInput,
    service: LLMService = Depends(get_llm_service)
):
    """주간 운동/식단 계획 생성 요청"""
    try:
        # Service 메서드가 dict를 인자로 받으므로 변환
        result = await service.call_goal_plan_llm(input_data.model_dump())
        
        # TODO: Repository를 호출하여 result(계획서)를 DB에 저장하는 로직 필요
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/plan/{thread_id}/chat", response_model=LLMResponse)
async def chat_about_plan(
    thread_id: str,
    chat_req: ChatRequest,
    service: LLMService = Depends(get_llm_service)
):
    """주간 계획에 대한 추가 Q&A"""
    response = await service.chat_with_weekly_plan(thread_id, chat_req.message)
    return {"response": response}