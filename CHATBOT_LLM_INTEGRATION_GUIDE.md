# 🤖 챗봇 백엔드 연결 가이드

## 📋 개요

ExplainMyBody의 챗봇 페이지를 백엔드 API와 연결하는 통합 가이드입니다.

**작업 일자**: 2026-01-30
**상태**: ✅ 임시 구현 완료 (키워드 기반 Mock 응답)
**향후 계획**: 백엔드 담당자가 실제 LLM/LangGraph 연결 예정

---

## 🎯 구현 목표

### Before (기존)
- 프론트엔드에서 Mock 응답 사용
- 키워드 기반 단순 응답
- 대화 이력 없음

### After (변경 후)
- 백엔드 API 호출 (현재: Mock 응답)
- Thread ID 기반 구조 준비
- 향후 실제 LLM 연결 가능 (OpenAI API 직접 연결 또는 LangGraph)

---

## 🏗️ 전체 아키텍처

```
프론트엔드 (React)
    ↓
Chatbot.jsx → sendChatbotMessage()
    ↓
/api/chatbot/chat (백엔드 API)
    ↓
chatbot_router.py → LLMService
    ↓
llm_service.py → chatbot_conversation()
    ↓
키워드 기반 Mock 응답 (현재)
또는
실제 LLM API (향후 구현 - OpenAI, Claude 등)
```

---

## 📁 수정된 파일 목록

### 백엔드 (Python/FastAPI)
1. **schemas/llm.py** - 챗봇 요청/응답 스키마 추가
2. **services/llm/llm_service.py** - 챗봇 대화 메서드 추가
3. **routers/chatbot.py** - 챗봇 라우터 신규 생성
4. **routers/__init__.py** - 챗봇 라우터 export 추가
5. **main.py** - 챗봇 라우터 등록

### 프론트엔드 (React)
1. **services/chatService.js** - sendChatbotMessage() API 함수 추가
2. **pages/Chatbot/Chatbot.jsx** - Mock 응답 → 실제 API 호출로 변경

---

## 💻 백엔드 변경 사항 (담당자에게 전달)

### 1. schemas/llm.py - 스키마 추가

**위치**: `backend/schemas/llm.py` 파일 끝에 추가

**변경 내용**:
```python
# ============================================================================
# Chatbot Schemas - 챗봇 대화
# ============================================================================

class ChatbotRequest(BaseModel):
    """챗봇 대화 요청"""
    bot_type: str  # "inbody-analyst" 또는 "workout-planner"
    message: str
    user_id: Optional[int] = None  # 옵션: 사용자별 대화 이력 관리
    thread_id: Optional[str] = None  # 옵션: 이전 대화 이어서 하기


class ChatbotResponse(BaseModel):
    """챗봇 대화 응답"""
    response: str
    thread_id: str  # 대화 이력 추적용
```

**역할**:
- 프론트엔드와 백엔드 간 데이터 형식 정의
- Pydantic을 통한 데이터 검증

---

### 2. services/llm/llm_service.py - 챗봇 메서드 추가

**위치**: `backend/services/llm/llm_service.py` 파일 끝에 추가

**변경 내용** (현재: 키워드 기반 Mock 응답):
```python
async def chatbot_conversation(
    self,
    bot_type: str,
    user_message: str,
    thread_id: Optional[str] = None,
    user_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    챗봇 대화 처리

    Args:
        bot_type: 챗봇 유형 ("inbody-analyst" 또는 "workout-planner")
        user_message: 사용자 메시지
        thread_id: 기존 대화 스레드 ID (없으면 새로 생성)
        user_id: 사용자 ID (옵션)

    Returns:
        {
            "response": str,  # AI 응답
            "thread_id": str  # 대화 스레드 ID
        }
    """
    # 스레드 ID 생성 또는 재사용
    if not thread_id:
        import uuid
        thread_id = f"chatbot_{bot_type}_{user_id or 'guest'}_{uuid.uuid4().hex[:8]}"

    # ====================================================================
    # TODO: 백엔드 담당자가 실제 LLM API 연결 필요
    # 현재는 임시 Mock 응답 사용 (키워드 매칭)
    # ====================================================================

    # 임시 Mock 응답 (실제 LLM 구현 전까지)
    MOCK_RESPONSES = {
        "inbody-analyst": {
            "keywords": {
                "체지방": "체지방 감소를 위해서는 유산소 운동과 근력 운동을 병행하는 것이 좋습니다...",
                "근육": "근육량 증가를 위해서는 충분한 단백질 섭취(체중 1kg당 1.6-2g)와...",
                "식단": "균형잡힌 영양 섭취가 중요합니다. 탄수화물:단백질:지방을 5:3:2 비율로...",
                # ... 더 많은 키워드
            },
            "default": "안녕하세요! 인바디 분석 전문가입니다. 체성분 데이터 분석, 식단, 운동..."
        },
        "workout-planner": {
            "keywords": {
                "운동": "효과적인 운동 루틴을 위해서는 목표와 현재 체력 수준을 고려해야...",
                "하체": "하체 운동의 기본은 스쿼트입니다! 월요일과 목요일에...",
                # ... 더 많은 키워드
            },
            "default": "안녕하세요! 운동 플래너 전문가입니다. 개인 맞춤형 운동 루틴..."
        }
    }

    # 봇 타입에 맞는 응답 선택
    bot_responses = MOCK_RESPONSES.get(bot_type, MOCK_RESPONSES["inbody-analyst"])

    # 키워드 매칭
    ai_response = bot_responses["default"]
    for keyword, response in bot_responses["keywords"].items():
        if keyword in user_message:
            ai_response = response
            break

    return {
        "response": ai_response,
        "thread_id": thread_id
    }
```

**현재 구현**:
- ❌ **LangGraph 사용 안함** (복잡도 제거)
- ✅ **키워드 기반 Mock 응답** (간단한 로직)
- ✅ **Thread ID 생성** (향후 대화 이력 추적용)

**향후 실제 LLM 연결 시**:
백엔드 담당자가 Mock 응답 부분을 아래 중 하나로 교체:
1. **OpenAI API 직접 호출** (간단, 추천)
2. **LangGraph + OpenAI** (복잡한 워크플로우 필요 시)
3. **다른 LLM** (Anthropic Claude, Google Gemini 등)

---

### 3. routers/chatbot.py - 신규 라우터 생성

**위치**: `backend/routers/chatbot.py` (신규 파일)

**전체 코드**:
```python
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
```

**역할**:
- `/api/chatbot/chat` 엔드포인트 제공
- 요청 데이터 검증 (bot_type, message)
- LLM 서비스 호출 및 응답 반환

---

### 4. routers/__init__.py - Export 추가

**위치**: `backend/routers/__init__.py`

**변경 전**:
```python
from .common import auth_router, users_router
from .ocr import health_records_router
from .llm import analysis_router, goals_router

__all__ = ["auth_router", "users_router", "health_records_router", "analysis_router", "goals_router"]
```

**변경 후**:
```python
from .common import auth_router, users_router
from .ocr import health_records_router
from .llm import analysis_router, goals_router, weekly_plans_router
from .chatbot import router as chatbot_router

__all__ = [
    "auth_router",
    "users_router",
    "health_records_router",
    "analysis_router",
    "goals_router",
    "weekly_plans_router",
    "chatbot_router"
]
```

---

### 5. main.py - 라우터 등록

**위치**: `backend/main.py`

**변경 내용**:

1. Import 추가:
```python
from routers import chatbot_router
```

2. 라우터 등록 추가:
```python
app.include_router(chatbot_router, prefix="/api/chatbot", tags=["챗봇"])
```

**전체 라우터 등록 부분**:
```python
# 라우터 등록
app.include_router(auth_router, prefix="/api/auth", tags=["인증"])
app.include_router(users_router, prefix="/api/users", tags=["사용자"])
app.include_router(health_records_router, prefix="/api/health-records", tags=["건강 기록"])
app.include_router(analysis_router, prefix="/api/analysis", tags=["분석"])
app.include_router(goals_router, prefix="/api/goals", tags=["목표"])
app.include_router(weekly_plans_router, prefix="/api/weekly-plans", tags=["주간 계획"])
app.include_router(chatbot_router, prefix="/api/chatbot", tags=["챗봇"])  # 신규
```

---

## 🎨 프론트엔드 변경 사항

### 1. services/chatService.js - API 함수 추가

**위치**: `frontend/src/services/chatService.js` 파일 끝에 추가

**변경 내용**:
```javascript
/**
 * 챗봇 대화 (신규)
 *
 * 📍 사용 위치: pages/Chatbot/Chatbot.jsx
 *
 * 기능:
 * - 인바디 분석 전문가 또는 운동 플래너 전문가와 대화
 * - 백엔드 API를 통한 응답 생성 (현재: Mock, 향후: 실제 LLM)
 * - 대화 이력 자동 추적 (thread_id 사용)
 *
 * @param {Object} data - 챗봇 대화 요청 데이터
 * @param {string} data.bot_type - 챗봇 유형 ("inbody-analyst" | "workout-planner")
 * @param {string} data.message - 사용자 메시지
 * @param {number} [data.user_id] - 사용자 ID (옵션)
 * @param {string} [data.thread_id] - 대화 스레드 ID (이전 대화 이어가기용, 옵션)
 *
 * @returns {Promise<Object>} 챗봇 응답
 * @returns {string} return.response - AI 응답 메시지
 * @returns {string} return.thread_id - 대화 스레드 ID (다음 요청에 사용)
 *
 * @example
 * // 첫 대화 시작
 * const result1 = await sendChatbotMessage({
 *   bot_type: "inbody-analyst",
 *   message: "체지방을 줄이려면 어떻게 해야 해?",
 *   user_id: 1
 * });
 * console.log(result1.response);
 * console.log(result1.thread_id); // "chatbot_inbody-analyst_1_abc123"
 *
 * // 이전 대화 이어서 하기
 * const result2 = await sendChatbotMessage({
 *   bot_type: "inbody-analyst",
 *   message: "유산소 운동은 얼마나 해야 해?",
 *   thread_id: result1.thread_id // 이전 대화 ID 전달
 * });
 * console.log(result2.response); // 이전 대화 맥락을 기억하여 답변
 */
export const sendChatbotMessage = async (data) => {
    return await apiRequest('/chatbot/chat', {
        method: 'POST',
        body: JSON.stringify(data),
    });
};
```

---

### 2. pages/Chatbot/Chatbot.jsx - API 연결

**주요 변경 사항**:

#### 1) Import 추가
```javascript
import { sendChatbotMessage } from '../../services/chatService';
```

#### 2) State 추가 (Thread ID 관리)
```javascript
const [threadId, setThreadId] = useState(null); // LangGraph 대화 스레드 ID
```

#### 3) handleSend 함수 변경 (Mock → 실제 API)

**변경 전** (Mock 응답):
```javascript
const handleSend = (e) => {
    e.preventDefault();
    if (!inputValue.trim()) return;

    const userMessage = {
        id: Date.now(),
        text: inputValue,
        sender: 'user'
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsTyping(true);

    // 시뮬레이션된 AI 응답
    setTimeout(() => {
        const botMessage = {
            id: Date.now() + 1,
            text: getMockResponse(inputValue),
            sender: 'bot'
        };
        setMessages(prev => [...prev, botMessage]);
        setIsTyping(false);
    }, 1500);
};
```

**변경 후** (실제 API 호출):
```javascript
const handleSend = async (e) => {
    e.preventDefault();
    if (!inputValue.trim()) return;

    const userMessage = {
        id: Date.now(),
        text: inputValue,
        sender: 'user'
    };

    setMessages(prev => [...prev, userMessage]);
    const currentInput = inputValue;
    setInputValue('');
    setIsTyping(true);

    try {
        // 백엔드 LLM API 호출
        const result = await sendChatbotMessage({
            bot_type: botType,
            message: currentInput,
            thread_id: threadId, // 이전 대화 이력 추적
            user_id: 1 // TODO: 실제 사용자 ID로 변경 (로그인 구현 후)
        });

        // Thread ID 저장 (대화 이력 유지)
        if (result.thread_id) {
            setThreadId(result.thread_id);
        }

        const botMessage = {
            id: Date.now() + 1,
            text: result.response,
            sender: 'bot'
        };
        setMessages(prev => [...prev, botMessage]);
    } catch (error) {
        console.error('챗봇 응답 오류:', error);
        // 오류 시 폴백 응답
        const errorMessage = {
            id: Date.now() + 1,
            text: "죄송합니다. 일시적인 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
            sender: 'bot'
        };
        setMessages(prev => [...prev, errorMessage]);
    } finally {
        setIsTyping(false);
    }
};
```

#### 4) BOT_CONFIG 간소화 (responses 제거)

Mock 응답 로직을 더 이상 사용하지 않으므로 BOT_CONFIG에서 `responses` 필드 제거:

```javascript
const BOT_CONFIG = {
    'inbody-analyst': {
        name: '인바디 분석 전문가',
        icon: '🧑‍⚕️',
        greeting: "안녕하세요! 인바디 분석 전문가입니다. 당신의 체성분 데이터를 분석하고 건강한 신체를 위한 조언을 드리겠습니다. 무엇이 궁금하신가요?",
        color: '#667eea',
        gradient: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
    },
    'workout-planner': {
        name: '운동 플래너 전문가',
        icon: '🏋️',
        greeting: "안녕하세요! 운동 플래너 전문가입니다. 당신의 목표에 맞는 최적의 운동 루틴을 제안하고, 올바른 자세와 동기부여를 제공하겠습니다. 어떤 운동이 필요하신가요?",
        color: '#f5576c',
        gradient: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)'
    }
};
```

---

## 🔄 API 플로우

### 1️⃣ 현재 구현 (Mock 응답)

```
사용자 입력: "체지방을 줄이려면 어떻게 해야 해?"
    ↓
Chatbot.jsx: sendChatbotMessage({
    bot_type: "inbody-analyst",
    message: "체지방을 줄이려면 어떻게 해야 해?",
    user_id: 1,
    thread_id: null  // 첫 대화이므로 null
})
    ↓
Backend /api/chatbot/chat
    ↓
LLMService.chatbot_conversation()
    - thread_id 자동 생성: "chatbot_inbody-analyst_1_abc123"
    - "체지방" 키워드 감지
    - MOCK_RESPONSES에서 매칭되는 응답 반환
    ↓
응답 반환: {
    response: "체지방 감소를 위해서는 유산소 운동과 근력 운동을 병행하는 것이 좋습니다...",
    thread_id: "chatbot_inbody-analyst_1_abc123"
}
    ↓
Chatbot.jsx
    - threadId state에 저장
    - 화면에 응답 표시
```

**현재 한계**:
- 키워드가 없으면 기본 응답만 제공
- 대화 맥락을 기억하지 못함 (thread_id는 생성되지만 활용 안 됨)

### 2️⃣ 향후 실제 LLM 연결 시

```
사용자 입력: "체지방을 줄이려면 어떻게 해야 해?"
    ↓
Chatbot.jsx: sendChatbotMessage({...})
    ↓
Backend /api/chatbot/chat
    ↓
LLMService.chatbot_conversation()
    - thread_id 자동 생성
    - OpenAI API 호출 (또는 다른 LLM)
    - 시스템 프롬프트: "당신은 인바디 분석 전문가입니다..."
    ↓
OpenAI GPT-4
    - 사용자 질문 이해
    - 전문가 페르소나로 응답 생성
    ↓
응답 반환: {
    response: "체지방 감소를 위한 맞춤형 조언...",
    thread_id: "chatbot_inbody-analyst_1_abc123"
}
```

**실제 LLM 사용 시 장점**:
- 자연스러운 대화 가능
- 다양한 질문에 유연하게 대응
- 대화 맥락 기억 (thread_id 활용)

---

## 🧪 테스트 방법

### 1. 백엔드 서버 실행
```bash
cd backend
uvicorn main:app --reload
```

### 2. API 문서 확인
```
http://localhost:8000/docs
```

**확인 사항**:
- `/api/chatbot/chat` 엔드포인트가 보이는지
- Request Body 스키마가 올바른지
- Try it out으로 테스트 가능

### 3. Swagger UI 테스트

Request Body:
```json
{
  "bot_type": "inbody-analyst",
  "message": "체지방을 줄이려면 어떻게 해야 해?",
  "user_id": 1
}
```

Expected Response:
```json
{
  "response": "체지방 감소를 위해서는 유산소 운동과...",
  "thread_id": "chatbot_inbody-analyst_1_abc123"
}
```

### 4. 프론트엔드 테스트

```bash
cd frontend
npm run dev
```

**확인 사항**:
1. `/chatbot` 페이지 접속
2. 챗봇 선택 (인바디 분석 또는 운동 플래너)
3. 메시지 전송 → AI 응답 확인
4. 연속 대화 → 맥락 유지 확인
5. 브라우저 콘솔에서 thread_id 확인

---

## 🔧 실제 LLM API 연결 방법 (백엔드 담당자용)

현재는 **키워드 기반 Mock 응답**을 사용하고 있습니다. 실제 LLM을 연결하려면 아래 방법 중 하나를 선택하세요.

---

### 방법 1: OpenAI API 직접 연결 (추천 ⭐)

**장점**:
- 간단한 구현
- 빠른 응답 속도
- LangGraph 없이도 대화 가능

**단점**:
- 대화 이력을 수동으로 관리해야 함
- 복잡한 워크플로우 구현 어려움

#### 1️⃣ 사전 준비 확인

**OpenAI 패키지**는 이미 설치되어 있습니다 (`llm_clients.py`에서 사용 중).

#### 2️⃣ .env 파일에 API 키 추가

`backend/.env` 파일에 OpenAI API 키가 있는지 확인:

```bash
OPENAI_API_KEY="sk-..."
```

없으면 추가하세요.

#### 3️⃣ llm_service.py 수정

프로젝트에는 이미 `OpenAIClient` 클래스가 있습니다 ([llm_clients.py](backend/services/llm/llm_clients.py:26-67)).
이를 활용하여 `chatbot_conversation()` 메서드의 Mock 응답 부분을 아래 코드로 교체:

```python
async def chatbot_conversation(
    self,
    bot_type: str,
    user_message: str,
    thread_id: Optional[str] = None,
    user_id: Optional[int] = None
) -> Dict[str, Any]:
    """챗봇 대화 처리 (OpenAI API 연결)"""

    # 1. Thread ID 생성 또는 재사용
    if not thread_id:
        import uuid
        thread_id = f"chatbot_{bot_type}_{user_id or 'guest'}_{uuid.uuid4().hex[:8]}"

    # 2. 봇 타입별 시스템 프롬프트 설정
    SYSTEM_PROMPTS = {
        "inbody-analyst": """당신은 친근하고 전문적인 인바디 분석 전문가입니다.
        사용자의 체성분 데이터를 분석하고, 건강한 신체를 위한 맞춤형 조언을 제공합니다.
        식단, 운동, 생활습관에 대해 구체적이고 실용적인 정보를 제공하세요.
        답변은 친근하면서도 전문적인 톤으로 작성하고, 이모지를 적절히 사용하세요.""",

        "workout-planner": """당신은 열정적이고 전문적인 운동 플래너 전문가입니다.
        사용자의 목표와 현재 체력 수준에 맞는 최적의 운동 루틴을 제안합니다.
        올바른 자세, 운동 빈도, 강도 조절에 대해 구체적인 조언을 제공하세요.
        답변은 동기부여가 되는 톤으로 작성하고, 이모지를 적절히 사용하세요."""
    }

    system_prompt = SYSTEM_PROMPTS.get(bot_type, SYSTEM_PROMPTS["inbody-analyst"])

    # 3. 기존 OpenAI 클라이언트 사용 (self.llm_client는 __init__에서 이미 생성됨)
    try:
        # OpenAIClient의 generate_chat 메서드 사용
        ai_response = self.llm_client.generate_chat(
            system_prompt=system_prompt,
            user_prompt=user_message
        )

        return {
            "response": ai_response,
            "thread_id": thread_id
        }

    except Exception as e:
        # 오류 시 폴백 응답
        return {
            "response": "죄송합니다. 일시적인 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
            "thread_id": thread_id
        }
```

**설명**:
- `self.llm_client`는 `LLMService.__init__()`에서 이미 생성되어 있습니다
- `generate_chat()` 메서드는 [llm_clients.py:33-42](backend/services/llm/llm_clients.py:33-42)에 구현되어 있습니다
- 이미 있는 클라이언트를 재사용하므로 추가 import 불필요

#### 4️⃣ 대화 이력 추가 (선택사항)

위 코드는 **단발성 대화**만 가능합니다. 이전 대화를 기억하려면:

```python
# llm_service.py의 __init__에 대화 이력 저장소 추가
def __init__(self):
    self.model_version = "gpt-4o-mini"
    self.llm_client = create_llm_client(self.model_version)
    self.analysis_agent = create_analysis_agent(self.llm_client)

    # 대화 이력 저장소 (메모리)
    self.conversation_history = {}  # {thread_id: [("user", "메시지"), ("assistant", "응답")]}

async def chatbot_conversation(self, bot_type, user_message, thread_id=None, user_id=None):
    # ... (thread_id 생성, SYSTEM_PROMPTS 코드 동일)

    # 대화 이력 불러오기
    if thread_id not in self.conversation_history:
        self.conversation_history[thread_id] = []

    # 사용자 메시지 추가 (튜플 형태: role, content)
    self.conversation_history[thread_id].append(("user", user_message))

    try:
        # OpenAIClient의 generate_chat_with_history 메서드 사용
        ai_response = self.llm_client.generate_chat_with_history(
            system_prompt=SYSTEM_PROMPTS[bot_type],
            messages=self.conversation_history[thread_id]
        )

        # AI 응답 저장
        self.conversation_history[thread_id].append(("assistant", ai_response))

        return {"response": ai_response, "thread_id": thread_id}

    except Exception as e:
        return {
            "response": "죄송합니다. 일시적인 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
            "thread_id": thread_id
        }
```

**설명**:
- `generate_chat_with_history()` 메서드는 [llm_clients.py:44-58](backend/services/llm/llm_clients.py:44-58)에 구현되어 있습니다
- 메시지는 `(role, content)` 튜플 리스트 형태로 저장합니다
- 클라이언트가 자동으로 OpenAI 형식으로 변환합니다

**주의사항**:
- 메모리 기반이므로 서버 재시작 시 대화 이력 소실
- 프로덕션에서는 Redis 또는 PostgreSQL에 저장 권장 (아래 "향후 개선 사항" 참고)

---

### 방법 2: LangGraph + OpenAI (복잡한 워크플로우용)

**장점**:
- 복잡한 대화 흐름 관리 가능
- 대화 이력 자동 관리
- 다중 에이전트 협업 가능

**단점**:
- 구현 복잡도 높음
- 추가 학습 필요

**사용 시나리오**:
- 챗봇이 여러 단계를 거쳐 응답해야 할 때
- 외부 API 호출이 필요할 때 (예: 인바디 데이터 조회)
- 여러 전문가 봇이 협업해야 할 때

(LangGraph 구현은 복잡하므로 필요 시 별도 문서 작성)

---

### 방법 3: 다른 LLM 사용 (Claude, Gemini 등)

OpenAI 대신 다른 LLM을 사용하려면:

**Anthropic Claude**:
```bash
pip install anthropic
```

```python
from anthropic import AsyncAnthropic

client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
response = await client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=500,
    system=system_prompt,
    messages=[{"role": "user", "content": user_message}]
)
ai_response = response.content[0].text
```

**Google Gemini**:
```bash
pip install google-generativeai
```

```python
import google.generativeai as genai

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel("gemini-pro")
response = model.generate_content(user_message)
ai_response = response.text
```

---

### ⚠️ 주의사항

#### 1. API 키 보안
- `.env` 파일에 저장 (절대 Git에 커밋 금지)
- `.gitignore`에 `.env` 추가 확인

#### 2. 비용 관리
- OpenAI GPT-4o-mini: 입력 $0.15/1M 토큰, 출력 $0.60/1M 토큰
- 대화 길이 제한 (max_tokens) 설정 권장
- 사용량 모니터링 (OpenAI Dashboard)

#### 3. 사용자 인증
현재 `user_id: 1` 하드코딩됨.

**TODO**:
- JWT 토큰에서 user_id 추출
- 프론트엔드에서 localStorage의 사용자 정보 활용

#### 4. Rate Limiting
- OpenAI API에는 분당 요청 제한 있음
- 프로덕션에서는 Rate Limiter 추가 권장

---

## 🎓 학습 포인트

### 1. FastAPI 라우터 구조
```
routers/
├── chatbot.py       # 신규 라우터 (챗봇 전용)
├── __init__.py      # Export 관리
└── llm/
    ├── analysis.py  # 건강 분석 라우터
    └── ...

main.py → app.include_router()로 등록
```

**핵심 개념**:
- 기능별 라우터 분리 (chatbot, analysis, goals 등)
- `__init__.py`에서 중앙 관리
- `main.py`에서 prefix로 API 경로 구성

### 2. Pydantic 스키마 (Request/Response)
```python
class ChatbotRequest(BaseModel):
    bot_type: str
    message: str
    user_id: Optional[int] = None
    thread_id: Optional[str] = None

class ChatbotResponse(BaseModel):
    response: str
    thread_id: str
```

**역할**:
- 데이터 검증 자동화 (타입, 필수값 체크)
- OpenAPI 문서 자동 생성 (`/docs`)
- 타입 안전성 보장

### 3. Thread ID 패턴
```python
# 백엔드: Thread ID 생성
thread_id = f"chatbot_{bot_type}_{user_id}_{uuid.uuid4().hex[:8]}"
# 예: "chatbot_inbody-analyst_1_a3b7c9d2"

# 프론트엔드: Thread ID 저장 및 재사용
const [threadId, setThreadId] = useState(null);
```

**동작 원리**:
- 첫 대화: `thread_id=null` → 백엔드가 생성하여 반환
- 이어서 대화: 받은 `thread_id` 재사용 → 대화 이력 유지
- 실제 LLM 연결 시 이 ID로 대화 맥락 추적

### 4. React Async 상태 관리
```javascript
const handleSend = async (e) => {
    e.preventDefault();
    setIsTyping(true); // 로딩 상태

    try {
        const result = await sendChatbotMessage({...});
        // 성공 처리
    } catch (error) {
        // 에러 처리 (폴백 메시지 표시)
    } finally {
        setIsTyping(false); // 로딩 해제
    }
};
```

**핵심 패턴**:
- `async/await`로 비동기 API 호출
- `try-catch-finally`로 에러 처리
- 로딩 상태 관리 (`isTyping`)

### 5. 키워드 기반 응답 매칭 (현재 구현)
```python
MOCK_RESPONSES = {
    "inbody-analyst": {
        "keywords": {"체지방": "...", "근육": "..."},
        "default": "기본 응답"
    }
}

# 키워드 매칭
for keyword, response in keywords.items():
    if keyword in user_message:
        return response
```

**한계**:
- 단순 문자열 포함 여부만 확인
- 대화 맥락 이해 불가
- 실제 LLM으로 교체 시 자연스러운 대화 가능

---

## 🔮 향후 개선 사항

### 1단계: Mock → 실제 LLM 연결 (우선순위 ⭐⭐⭐)
- **현재**: 키워드 기반 Mock 응답
- **목표**: OpenAI API 직접 연결
- **작업**: 위의 "방법 1: OpenAI API 직접 연결" 참고

### 2단계: 대화 이력 저장 (우선순위 ⭐⭐)
**현재 상태**:
- Thread ID는 생성되지만 대화 이력 미저장
- 메모리 기반 (서버 재시작 시 소실)

**개선 방안**:
```python
# Redis 사용 예시
import redis
import json

redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)

# 대화 저장
redis_client.setex(
    f"chat_history:{thread_id}",
    3600,  # 1시간 TTL
    json.dumps(messages)
)

# 대화 불러오기
history = redis_client.get(f"chat_history:{thread_id}")
messages = json.loads(history) if history else []
```

**또는 PostgreSQL 저장**:
```sql
CREATE TABLE chat_history (
    id SERIAL PRIMARY KEY,
    thread_id VARCHAR(100),
    role VARCHAR(20),  -- 'user' 또는 'assistant'
    content TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 3단계: 스트리밍 응답 (우선순위 ⭐)
**현재**: 전체 응답 생성 후 한 번에 반환
**목표**: 실시간 타이핑 효과

```python
# 백엔드: 스트리밍 응답
from fastapi.responses import StreamingResponse

async def chatbot_conversation_stream(...):
    async for chunk in client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        stream=True
    ):
        yield chunk.choices[0].delta.content or ""

@router.post("/chat/stream")
async def chat_stream(request: ChatbotRequest):
    return StreamingResponse(
        chatbot_conversation_stream(...),
        media_type="text/event-stream"
    )
```

```javascript
// 프론트엔드: 스트리밍 수신
const response = await fetch('/api/chatbot/chat/stream', {...});
const reader = response.body.getReader();

while (true) {
    const {done, value} = await reader.read();
    if (done) break;

    const text = new TextDecoder().decode(value);
    // 실시간으로 메시지에 추가
    setMessages(prev => [...prev.slice(0, -1), {
        ...prev[prev.length - 1],
        text: prev[prev.length - 1].text + text
    }]);
}
```

### 4단계: 인바디 데이터 연동
챗봇이 사용자의 실제 인바디 데이터를 참조하여 답변:

```python
# 사용자의 최근 인바디 데이터 조회
from models import HealthRecord

record = db.query(HealthRecord).filter_by(user_id=user_id).order_by(
    HealthRecord.measured_at.desc()
).first()

# 시스템 프롬프트에 데이터 포함
system_prompt = f"""당신은 인바디 분석 전문가입니다.
현재 사용자 정보:
- 체중: {record.body_weight}kg
- 골격근량: {record.skeletal_muscle_mass}kg
- 체지방률: {record.body_fat_percentage}%
...
이 데이터를 바탕으로 맞춤형 조언을 제공하세요."""
```

### 5단계: 멀티모달 (이미지 업로드)
운동 자세 사진을 업로드하여 피드백 받기:

```python
class ChatbotRequest(BaseModel):
    message: str
    image: Optional[str] = None  # Base64 이미지

# GPT-4o-vision 사용
response = await client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "user", "content": [
            {"type": "text", "text": "이 운동 자세가 맞나요?"},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image}"}}
        ]}
    ]
)
```

### 6단계: 음성 입력/출력
- **입력**: Web Speech API (음성 → 텍스트)
- **출력**: Text-to-Speech (AI 응답 읽어주기)

```javascript
// Web Speech API
const recognition = new webkitSpeechRecognition();
recognition.onresult = (event) => {
    const text = event.results[0][0].transcript;
    setInputValue(text);
};
```

---

## 📞 문의 사항

백엔드 담당자가 구현 중 궁금한 사항:
1. LangGraph 에이전트 설정
2. Thread ID 영구 저장 방법
3. 시스템 프롬프트 튜닝

→ 프론트엔드 개발자에게 문의

---

**작성자**: Claude Code
**작성일**: 2026-01-30
**최종 수정**: 2026-01-30
**상태**: ✅ 임시 구현 완료 (Mock 응답)
**다음 단계**: 백엔드 담당자가 OpenAI API 연결 (위 가이드 참고)
