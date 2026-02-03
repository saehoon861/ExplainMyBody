# 챗봇 OpenAI API 연결 및 대화 이력 구현 가이드

## 📅 구현 일자
**2026-01-30**

---

## 🎯 구현 목표
1. ✅ 챗봇의 Mock 응답을 실제 OpenAI API로 교체
2. ✅ 대화 이력 기능 추가 (이전 대화 기억)

---

## 📚 목차
1. [1단계: Mock 응답 → OpenAI API 연결](#1단계-mock-응답--openai-api-연결)
2. [2단계: 대화 이력 기능 추가](#2단계-대화-이력-기능-추가)
3. [테스트 방법](#테스트-방법)
4. [완성된 전체 코드](#완성된-전체-코드)

---

## 1단계: Mock 응답 → OpenAI API 연결

### ✅ 변경 전 (Mock 응답)

**파일**: `backend/services/llm/llm_service.py`
**메서드**: `chatbot_conversation()`

```python
# 임시 Mock 응답 (키워드 매칭)
MOCK_RESPONSES = {
    "inbody-analyst": {
        "keywords": {
            "체지방": "체지방 감소를 위해서는...",
            "근육": "근육량 증가를 위해서는...",
            # ... 더 많은 키워드
        },
        "default": "안녕하세요! 인바디 분석 전문가입니다..."
    },
    # ... workout-planner도 비슷한 구조
}

# 키워드 매칭 로직
bot_responses = MOCK_RESPONSES.get(bot_type, MOCK_RESPONSES["inbody-analyst"])
ai_response = bot_responses["default"]
for keyword, response in bot_responses["keywords"].items():
    if keyword in user_message:
        ai_response = response
        break

return {"response": ai_response, "thread_id": thread_id}
```

**문제점**:
- ❌ 키워드가 없으면 기본 응답만 제공
- ❌ 대화 맥락 이해 불가
- ❌ 자연스러운 대화 불가능

---

### ✅ 변경 후 (OpenAI API 연결)

**같은 파일, 같은 메서드를 아래처럼 수정**:

```python
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

# 3. OpenAI API 호출 (self.llm_client는 __init__에서 이미 생성됨)
try:
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

**개선 사항**:
- ✅ 실제 OpenAI GPT-4o-mini 모델 사용
- ✅ 자연스러운 대화 가능
- ✅ 다양한 질문에 유연하게 대응
- ✅ 시스템 프롬프트로 페르소나 설정
- ✅ 에러 핸들링 추가

**하지만 아직**:
- ❌ 이전 대화를 기억하지 못함 (단발성 대화만 가능)

---

## 2단계: 대화 이력 기능 추가

### 📌 단계 2-1: `__init__` 메서드에 대화 이력 저장소 추가

**파일**: `backend/services/llm/llm_service.py`
**클래스**: `LLMService`
**메서드**: `__init__()`

#### 변경 전:
```python
def __init__(self):
    """LLM 에이전트 및 클라이언트 초기화"""
    self.model_version = "gpt-4o-mini"
    self.llm_client = create_llm_client(self.model_version)
    self.analysis_agent = create_analysis_agent(self.llm_client)
```

#### 변경 후:
```python
def __init__(self):
    """LLM 에이전트 및 클라이언트 초기화"""
    self.model_version = "gpt-4o-mini"
    self.llm_client = create_llm_client(self.model_version)
    self.analysis_agent = create_analysis_agent(self.llm_client)

    # 챗봇 대화 이력 저장소 (메모리 기반)
    # {thread_id: [("user", "메시지"), ("assistant", "응답"), ...]}
    self.conversation_history = {}
```

**설명**:
- `conversation_history`: Thread ID별로 대화 이력 저장
- 형식: `{thread_id: [("role", "content"), ...]}`
- 메모리 기반이므로 서버 재시작 시 소실 (프로덕션에서는 Redis/PostgreSQL 사용 권장)

---

### 📌 단계 2-2: `chatbot_conversation()` 메서드를 대화 이력 지원으로 수정

**같은 파일, `chatbot_conversation()` 메서드 전체를 아래처럼 교체**:

```python
async def chatbot_conversation(
    self,
    bot_type: str,
    user_message: str,
    thread_id: Optional[str] = None,
    user_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    챗봇 대화 처리 (대화 이력 포함)

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

    # 3. 대화 이력 불러오기 또는 새로 생성
    if thread_id not in self.conversation_history:
        self.conversation_history[thread_id] = []

    # 4. 사용자 메시지 추가 (튜플 형태: role, content)
    self.conversation_history[thread_id].append(("user", user_message))

    # 5. OpenAI API 호출 (대화 이력 포함)
    try:
        ai_response = self.llm_client.generate_chat_with_history(
            system_prompt=system_prompt,
            messages=self.conversation_history[thread_id]
        )

        # 6. AI 응답을 대화 이력에 저장
        self.conversation_history[thread_id].append(("assistant", ai_response))

        return {
            "response": ai_response,
            "thread_id": thread_id
        }

    except Exception as e:
        # 오류 시 폴백 응답 (대화 이력에서 마지막 사용자 메시지 제거)
        self.conversation_history[thread_id].pop()
        return {
            "response": "죄송합니다. 일시적인 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
            "thread_id": thread_id
        }
```

**주요 변경 사항**:
1. **3단계**: `conversation_history`에서 thread_id별 대화 이력 불러오기
2. **4단계**: 사용자 메시지를 대화 이력에 추가 `("user", user_message)`
3. **5단계**: `generate_chat()` 대신 `generate_chat_with_history()` 사용
4. **6단계**: AI 응답을 대화 이력에 저장 `("assistant", ai_response)`
5. **에러 처리**: 실패 시 마지막 사용자 메시지를 이력에서 제거

---

## 테스트 방법

### 1️⃣ 환경 변수 확인
```bash
# backend/.env 파일에 API 키가 있는지 확인
cat backend/.env | grep OPENAI_API_KEY
```

**없으면 추가**:
```bash
echo 'OPENAI_API_KEY="sk-..."' >> backend/.env
```

---

### 2️⃣ 백엔드 서버 실행
```bash
cd backend
uvicorn main:app --reload
```

---

### 3️⃣ 프론트엔드 실행
```bash
cd frontend
npm run dev
```

---

### 4️⃣ 브라우저 테스트 (대화 이력 확인)

1. **챗봇 접속**: `http://localhost:5173/chatbot` → 인바디 분석 선택
2. **첫 메시지**: "체지방을 줄이고 싶어"
   - 응답: "체지방 감소를 위해서는 유산소 운동과..."
3. **두 번째 메시지**: "유산소는 얼마나 해야 해?"
   - ✅ **AI가 이전 대화를 기억하고 답변** (예: "앞서 말씀드린 체지방 감소를 위해서는...")
4. **세 번째 메시지**: "식단도 중요한가?"
   - ✅ **계속해서 대화 맥락 유지**

**이전 (대화 이력 없음)**:
```
사용자: "체지방을 줄이고 싶어"
AI: "유산소 운동을 추천드립니다..."

사용자: "유산소는 얼마나 해야 해?"
AI: "유산소 운동은 주 3-4회..." [맥락 없음] ❌
```

**현재 (대화 이력 있음)**:
```
사용자: "체지방을 줄이고 싶어"
AI: "유산소 운동을 추천드립니다..."

사용자: "유산소는 얼마나 해야 해?"
AI: "앞서 말씀드린 체지방 감소를 위해서는..." [맥락 유지] ✅
```

---

### 5️⃣ API 직접 테스트 (Swagger UI)

**URL**: `http://localhost:8000/docs`

**첫 대화**:
```json
POST /api/chatbot/chat
{
  "bot_type": "inbody-analyst",
  "message": "체지방을 줄이고 싶어",
  "user_id": 1
}

Response:
{
  "response": "체지방 감소를 위해서는 유산소 운동과 근력 운동을 병행하는 것이 좋습니다...",
  "thread_id": "chatbot_inbody-analyst_1_a3b7c9d2"
}
```

**이어서 대화** (같은 thread_id 사용):
```json
POST /api/chatbot/chat
{
  "bot_type": "inbody-analyst",
  "message": "유산소는 얼마나 해야 해?",
  "user_id": 1,
  "thread_id": "chatbot_inbody-analyst_1_a3b7c9d2"  // 이전 응답의 thread_id
}

Response:
{
  "response": "앞서 말씀드린 체지방 감소를 위해 주 3-4회, 30-45분 정도의 유산소 운동을 추천드립니다...",
  "thread_id": "chatbot_inbody-analyst_1_a3b7c9d2"
}
```

✅ **AI가 이전 대화를 기억하고 답변합니다!**

---

## 완성된 전체 코드

### 📄 backend/services/llm/llm_service.py (수정된 부분만)

```python
class LLMService:
    """LLM API 호출 서비스"""

    def __init__(self):
        """LLM 에이전트 및 클라이언트 초기화"""
        self.model_version = "gpt-4o-mini"
        self.llm_client = create_llm_client(self.model_version)
        self.analysis_agent = create_analysis_agent(self.llm_client)

        # 챗봇 대화 이력 저장소 (메모리 기반)
        self.conversation_history = {}

    async def chatbot_conversation(
        self,
        bot_type: str,
        user_message: str,
        thread_id: Optional[str] = None,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """챗봇 대화 처리 (대화 이력 포함)"""

        # 1. Thread ID 생성
        if not thread_id:
            import uuid
            thread_id = f"chatbot_{bot_type}_{user_id or 'guest'}_{uuid.uuid4().hex[:8]}"

        # 2. 시스템 프롬프트 설정
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

        # 3. 대화 이력 불러오기
        if thread_id not in self.conversation_history:
            self.conversation_history[thread_id] = []

        # 4. 사용자 메시지 추가
        self.conversation_history[thread_id].append(("user", user_message))

        # 5. OpenAI API 호출 (대화 이력 포함)
        try:
            ai_response = self.llm_client.generate_chat_with_history(
                system_prompt=system_prompt,
                messages=self.conversation_history[thread_id]
            )

            # 6. AI 응답 저장
            self.conversation_history[thread_id].append(("assistant", ai_response))

            return {"response": ai_response, "thread_id": thread_id}

        except Exception as e:
            # 오류 시 대화 이력에서 마지막 메시지 제거
            self.conversation_history[thread_id].pop()
            return {
                "response": "죄송합니다. 일시적인 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
                "thread_id": thread_id
            }
```

---

## 🔧 기술적 세부사항

### 사용한 클라이언트
**OpenAIClient** ([llm_clients.py:26-67](backend/services/llm/llm_clients.py:26-67))

### 사용한 메서드
**generate_chat_with_history()** ([llm_clients.py:44-58](backend/services/llm/llm_clients.py:44-58))

```python
def generate_chat_with_history(self, system_prompt: str, messages: List[Tuple[str, str]]) -> str:
    # 튜플 리스트를 OpenAI 포맷으로 변환
    formatted_messages = [{"role": "system", "content": system_prompt}]

    for role, content in messages:
        openai_role = "user" if role in ["human", "user"] else "assistant"
        formatted_messages.append({"role": openai_role, "content": content})

    response = self.client.chat.completions.create(
        model=self.model,  # "gpt-4o-mini"
        messages=formatted_messages,
        temperature=0.7,
    )
    return response.choices[0].message.content
```

### API 설정
- **모델**: `gpt-4o-mini`
- **Temperature**: 0.7
- **환경변수**: `OPENAI_API_KEY`

---

## 📊 구현 결과 비교

| 항목 | Mock 응답 | OpenAI (단발) | OpenAI (대화 이력) |
|------|-----------|---------------|-------------------|
| 자연스러운 대화 | ❌ | ✅ | ✅ |
| 다양한 질문 대응 | ❌ | ✅ | ✅ |
| 이전 대화 기억 | ❌ | ❌ | ✅ |
| 응답 품질 | 낮음 | 높음 | 매우 높음 |
| 구현 복잡도 | 낮음 | 낮음 | 중간 |

---

## ⚠️ 주의사항

### 1. 메모리 기반 저장소
**현재 구현**:
- `self.conversation_history = {}` (메모리)
- 서버 재시작 시 대화 이력 소실

**프로덕션 권장**:
- Redis 또는 PostgreSQL에 저장
- TTL 설정 (예: 1시간)

### 2. 비용 관리
**예상 비용** (GPT-4o-mini):
- 입력: $0.15 / 1M 토큰
- 출력: $0.60 / 1M 토큰
- 대화 3턴 (6개 메시지): 약 $0.001

### 3. 대화 길이 제한
- 너무 긴 대화는 토큰 제한 초과 가능
- 최근 N개 메시지만 유지 권장 (예: 최근 10턴)

---

## 🔮 향후 개선 사항

### 1. Redis 영구 저장
```python
import redis
import json

redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)

# 저장
redis_client.setex(
    f"chat_history:{thread_id}",
    3600,  # 1시간 TTL
    json.dumps(self.conversation_history[thread_id])
)

# 불러오기
history = redis_client.get(f"chat_history:{thread_id}")
messages = json.loads(history) if history else []
```

### 2. 대화 길이 제한
```python
# 최근 10턴(20개 메시지)만 유지
if len(self.conversation_history[thread_id]) > 20:
    self.conversation_history[thread_id] = self.conversation_history[thread_id][-20:]
```

### 3. 스트리밍 응답
실시간 타이핑 효과로 UX 개선

---

## ✨ 구현 완료 체크리스트

- [x] Mock 응답 제거
- [x] OpenAI API 연결
- [x] 시스템 프롬프트 설정 (2가지 봇 타입)
- [x] 에러 핸들링 추가
- [x] Thread ID 생성 로직
- [x] 기존 OpenAIClient 재사용
- [x] **대화 이력 저장 (메모리 기반) ← NEW!**
- [x] **generate_chat_with_history() 사용 ← NEW!**
- [ ] Redis 영구 저장 (추후 구현)
- [ ] 스트리밍 응답 (추후 구현)

---

**작성자**: Claude Code
**작성일**: 2026-01-30
**최종 수정**: 2026-01-30
**구현 소요 시간**: 약 10분
**구현 방식**: Mock 응답 → OpenAI API (단발) → OpenAI API (대화 이력)
