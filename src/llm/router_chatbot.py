"""
챗봇 라우터
/api/chatbot/*
"""

from fastapi import APIRouter, HTTPException
from schemas.llm import ChatbotRequest, ChatbotResponse
from services.llm.llm_service import LLMService

router = APIRouter()
llm_service = LLMService()


@router.post("/chat", response_model=ChatbotResponse)
async def chat_with_bot(request: ChatbotRequest):
    """
    챗봇과 대화

    - **bot_type**: 챗봇 유형 ("inbody-analyst" 또는 "workout-planner")
    - **message**: 사용자 메시지
    - **user_id**: 사용자 ID (옵션)
    - **thread_id**: 기존 대화 이어가기 (옵션)
    """
    # 지원되는 챗봇 유형 확인
    SUPPORTED_BOT_TYPES = ["inbody-analyst", "workout-planner"]
    if request.bot_type not in SUPPORTED_BOT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"지원되지 않는 챗봇 유형입니다. {SUPPORTED_BOT_TYPES} 중 하나를 선택하세요."
        )

    try:
        # LLM 서비스 호출
        result = await llm_service.chatbot_conversation(
            bot_type=request.bot_type,
            user_message=request.message,
            thread_id=request.thread_id,
            user_id=request.user_id
        )

        return ChatbotResponse(
            response=result["response"],
            thread_id=result["thread_id"]
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"챗봇 응답 생성 중 오류 발생: {str(e)}")
