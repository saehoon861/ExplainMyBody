# rule_based_prompts → LangGraph 통합 설계문서

작성일: 2026-02-05
대상 그래프: `backend/services/llm/llm_rag/weekly_plan_graph_rag.py`
통합할 프롬프트: `src/llm/llm_prompt_test_sk/rule_based_prompts.py`

---

## 1. 기존 LangGraph 구조

### 1.1 파일 구성

```
backend/services/llm/
├── llm_clients.py                  # OpenAI 클라이언트 (현재 sync only)
├── agent_graph.py                  # LLM1 그래프 (비RAG)
├── weekly_plan_graph.py            # LLM2 그래프 (비RAG)
├── llm_service.py                  # 서비스 레이어 (비RAG)
├── human_feedback.py               # HumanFeedback ORM
├── llm_interaction.py              # LLMInteraction ORM
└── llm_rag/                        # ← 현재 사용중 (RAG 버전)
    ├── agent_graph_rag.py          # LLM1 그래프
    ├── weekly_plan_graph_rag.py    # LLM2 그래프  ← 통합 대상
    ├── llm_service_rag.py          # 서비스 레이어
    ├── rag_retriever.py            # pgvector 검색
    ├── prompt_generator_rag.py     # 기존 프롬프트 생성
    └── weekly_plan_service_rag.py  # 주간 계획 서비스
```

### 1.2 공통 그래프 패턴

두 그래프(LLM1, LLM2) 모두 동일한 구조:

```
[START]
  ↓
[initial_*]  ──→ interrupt_after ──→ 프론트에서 결과 표시
  ↓                                        ↓ 사용자 입력
  ↓  ←──────────────────────── invoke(messages: [user_msg]) ←──
  ↓
route_qa()  (사용자 입력 첫 숫자로 카테고리 판단)
  ↓
[qa_*]      ──→ interrupt_after ──→ 프론트에서 결과 표시
  ↓                                        ↓ (루프)
  ↓  ←──────────────────────────────────────
  ↓
[finalize_*] ──→ [END]
```

구성 요소:
- **State**: `TypedDict` + `messages: Annotated[list, add_messages]` (리듀서로 대화 기록 자동 누적)
- **Checkpointer**: `MemorySaver()` — `thread_id`로 세션 단위 상태 저장
- **interrupt_after**: 지정된 노드 실행 후 자동 중단 → 외부에서 `invoke()` 재호출로 재개
- **route_qa**: conditional edge 라우팅 함수

### 1.3 LLM1 그래프 (agent_graph_rag.py)

```
State: AnalysisStateRAG
  ├─ analysis_input: StatusAnalysisInput
  ├─ messages: Annotated[list, add_messages]
  ├─ embedding: Optional[Dict]        ← 분석 결과의 임베딩 벡터
  └─ rag_context: Optional[str]

Nodes:
  initial_analysis       RAG 검색 + LLM 1회 + 임베딩 생성
  qa_strength_weakness   강점/약점 분석 Q&A
  qa_health_status       건강 상태 Q&A
  qa_impact              일상/운동 영향 Q&A
  qa_priority            개선 우선순위 Q&A
  qa_general             기타 Q&A
  finalize_analysis  →   END
```

### 1.4 LLM2 그래프 (weekly_plan_graph_rag.py) — 통합 대상

```
State: PlanStateRAG
  ├─ plan_input: GoalPlanInput
  ├─ messages: Annotated[list, add_messages]
  └─ rag_context: Optional[str]

Nodes:
  initial_plan           RAG 검색 + LLM 1회 (단일 프롬프트로 전체 계획 생성)
  qa_exercise_guide      운동 방법 가이드 Q&A
  qa_plan_adjustment     운동 플랜 조정 Q&A
  qa_diet_adjustment     식단 조정 Q&A
  qa_intensity_adjustment 강도 조정 Q&A
  qa_general             기타 Q&A
  finalize_plan      →   END
```

현재 `initial_plan`의 내부 흐름 (weekly_plan_graph_rag.py:52~96):
```
1. InBodyMeasurements 모델 변환
2. RAG 검색 (_generate_rag_query_from_goal → pgvector)
3. create_weekly_plan_prompt_with_rag() → (system, user)
4. llm_client.generate_chat(system, user)    ← 단일 sync 호출
5. return {messages, rag_context}
```

### 1.5 Human Feedback 루프 — 세부 흐름

```
① llm_service_rag.py: call_goal_plan_llm(plan_input)
     ↓
② thread_id 생성 ("plan_rag_{user_id}_{record_id}_{ts}")
     ↓
③ weekly_plan_agent.invoke(
       {plan_input, messages: [], rag_context: None},
       config={thread_id}
   )
     ↓
④ initial_plan 실행 → interrupt_after에 의해 중단
     ↓ 반환값
⑤ 프론트엔드에 plan_text 표시, thread_id 저장
     ↓ 사용자가 질문/수정 요청
⑥ llm_service_rag.py: chat_with_plan(thread_id, user_message)
     ↓
⑦ weekly_plan_agent.invoke(
       {messages: [("human", user_message)]},
       config={thread_id}            ← 동일 thread로 상태 복원
   )
     ↓
⑧ route_qa() → Q&A 노드 실행 → interrupt (루프 → ⑤)
     ↓ "5" 입력 시
⑨ finalize_plan → END
```

**핵심**: `invoke()` 재호출 시 `thread_id`를 통해 이전 상태(messages 전체)가 복원됨.
Q&A 노드는 `state["messages"]` 전체를 히스토리로 LLM에 전달하므로,
`initial_plan`에서 생성된 계획 텍스트를 자동으로 컨텍스트로 가집니다.

---

## 2. 현재 initial_plan의 문제점

| 문제 | 원인 |
|------|------|
| 단일 실패점 | LLM 1회 호출로 운동·식단·생활습관 전부 생성 — 하나라도 부적합하면 전체 재생성 |
| 응답 불균형 | 단일 프롬프트에서 여러 섹션을 생성하면 일부 섹션이 짧거나 얕아짐 |
| 룰 미적용 | `rule_based_prompts`에 이미 구현된 Health forbid/require, BodyType 룰, EXERCISE_TYPE_RULES 등이 현재 그래프에서는 사용되지 않음 |
| 속도 | 단일 장문 응답 생성(max_tokens 높음)이 분리된 단문 응답보다 느림 |

---

## 3. rule_based_prompts의 4호출 구조

`src/llm/llm_prompt_test_sk/rule_based_prompts.py`의 현재 구조:

| # | 함수 | 역할 | 프롬프트 핵심 내용 |
|---|------|------|--------------------|
| 1 | `create_summary_prompt` | 주간 목표 요약 | 전체 룰 종합 → 핵심 전략 3가지 |
| 2 | `create_workout_prompt` | 요일별 운동 계획 | Health forbid + WORKOUT RULES + EXERCISE_TYPE_RULES 확장 |
| 3 | `create_diet_prompt` | 식단 계획 | DIET RULES + 기초대사량/권장열량 |
| 4 | `create_lifestyle_prompt` | 생활 습관 팁 | COACH TONE + 동기부여 |

공통 인터페이스:
```python
def create_*_prompt(
    goal_input: GoalPlanInput,
    measurements: InBodyMeasurements,
    rag_context: str = "",
    user_profile: Optional[Dict[str, Any]] = None,
) -> Tuple[str, str]:  # (system_prompt, user_prompt)
```

4개 프롬프트는 **완전히 독립** — 서로 참조하지 않음. 이것이 병렬 호출의 근거입니다.

`user_profile`에 필요한 키:
```python
{
    "body_type1": str,          # BODY_TYPE1_RULES 키
    "body_type2": str,          # BODY_TYPE2_RULES 키
    "goal_type": str,           # comma-separated (다중선택): "감량, 재활"
    "health_specifics": str,    # comma-separated (다중선택): "허리 디스크, 고혈압"
    "preferences": str,         # "활동레벨: 보통, 유산소, 웨이트, ..."
}
```

---

## 4. 통합 가능성 분석

| 조건 | 현재 상태 | 통합 가능? |
|------|-----------|-----------|
| 4개 프롬프트의 독립성 | 서로 참조 없음 | ✅ 병렬 호출 적합 |
| LangGraph async node | `async def` node 지원, `ainvoke()` 제공 | ✅ |
| OpenAI async 클라이언트 | 현재 `OpenAI` (sync) only | ⚠️ `AsyncOpenAI` 추가 필요 |
| Q&A 컨텍스트 유지 | messages에 종합 응답을 저장하면 Q&A 자동 참조 | ✅ 변경 불필요 |
| user_profile 공급 | `GoalPlanInput`에 `health_specifics`, `preferences` 없음 | ⚠️ 서비스에서 DB 조회 후 State에 추가 필요 |
| 기존 Q&A 노드 | messages 히스토리 기반 — node 내부 변경 없음 | ✅ |

**결론: 통합 가능. `initial_plan` node를 async 4호출 node로 교체하면 됨.**
Q&A 노드, 라우팅, interrupt 구조는 모두 유지.

---

## 5. 통합 설계 — 변경 내용

### 5.1 변경 파일 목록

| 파일 | 변경 내용 |
|------|-----------|
| `llm_clients.py` | `AsyncOpenAIClient` 클래스 추가 |
| `weekly_plan_graph_rag.py` | State 확장, `initial_plan` → `generate_rule_based_plan` (async) 교체, node 등록명 변경 |
| `llm_service_rag.py` | `user_profile` DB 조회 후 State 전달, `invoke` → `ainvoke` |
| `rule_based_prompts.py` | 변경 없음 (import 경로만 백엔드 측에서 맞추기) |
| `rules.py` | 변경 없음 |

### 5.2 State 확장

```python
# weekly_plan_graph_rag.py

class PlanStateRAG(TypedDict):
    plan_input:   GoalPlanInput
    messages:     Annotated[list, add_messages]
    rag_context:  Optional[str]
    # --- 추가 ---
    user_profile: Optional[Dict[str, Any]]   # DB에서 조회한 건강/선호 정보
    plan_results: Optional[Dict[str, str]]   # {summary, workout, diet, lifestyle} 개별 응답 저장
```

### 5.3 AsyncOpenAIClient 추가

```python
# llm_clients.py
from openai import AsyncOpenAI

class AsyncOpenAIClient:
    """asyncio.gather용 async OpenAI 클라이언트"""
    def __init__(self, model: str = "gpt-4o-mini"):
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = model

    async def generate_chat(self, system_prompt: str, user_prompt: str) -> str:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,
        )
        return response.choices[0].message.content
```

### 5.4 async Node — 핵심 변경

기존 `generate_initial_plan` (sync, 단일 호출)을 아래로 교체:

```python
# weekly_plan_graph_rag.py
import asyncio
from services.llm.llm_clients import AsyncOpenAIClient
# rule_based_prompts는 shared 경로로 이동 후 import (§7 참조)
from <shared_path>.rule_based_prompts import (
    create_summary_prompt,
    create_workout_prompt,
    create_diet_prompt,
    create_lifestyle_prompt,
)

async_llm = AsyncOpenAIClient()

# ── node 정의 (create_weekly_plan_agent_with_rag 내부) ──
async def generate_rule_based_plan(state: PlanStateRAG) -> dict:
    """Node 1: RAG 검색 + rule_based 4호출 (async 병렬)"""
    plan_input  = state["plan_input"]
    user_profile = state.get("user_profile") or {}
    measurements = InBodyMeasurements(**plan_input.measurements)

    # ── 1. RAG 검색 (기존 동일) ──
    rag_context = ""
    if use_rag and rag_retriever:
        try:
            query   = _generate_rag_query_from_goal(plan_input, measurements)
            papers  = rag_retriever.retrieve_relevant_papers(query=query, top_k=5, lang="ko")
            if papers:
                rag_context = rag_retriever.format_papers_for_prompt(papers)
        except Exception as e:
            print(f"RAG 검색 실패: {e}")

    # ── 2. 4개 프롬프트 생성 (sync, 계산 부분은 빠름) ──
    prompt_fns = {
        "summary":   create_summary_prompt,
        "workout":   create_workout_prompt,
        "diet":      create_diet_prompt,
        "lifestyle": create_lifestyle_prompt,
    }
    prompts = {
        key: fn(
            goal_input=plan_input,
            measurements=measurements,
            rag_context=rag_context,
            user_profile=user_profile,
        )
        for key, fn in prompt_fns.items()
    }

    # ── 3. async 4호출 (병렬) ──
    async def _call(key: str, system_prompt: str, user_prompt: str) -> tuple[str, str]:
        text = await async_llm.generate_chat(system_prompt, user_prompt)
        return key, text

    results = dict(await asyncio.gather(
        _call("summary",   *prompts["summary"]),
        _call("workout",   *prompts["workout"]),
        _call("diet",      *prompts["diet"]),
        _call("lifestyle", *prompts["lifestyle"]),
        return_exceptions=True,          # 일부 실패해도 나머지 반환
    ))

    # ── 4. 실패 항목 처리 ──
    for key, val in results.items():
        if isinstance(val, Exception):
            results[key] = f"[{key} 생성 실패: {val}]"

    # ── 5. messages로 종합 (Q&A 컨텍스트용) ──
    combined = (
        f"---\n🎯 주간 목표 요약\n{results['summary']}\n\n"
        f"---\n🏋️ 운동 계획\n{results['workout']}\n\n"
        f"---\n🍽 식단 계획\n{results['diet']}\n\n"
        f"---\n💡 생활 습관\n{results['lifestyle']}"
    )

    return {
        "messages":    [("human", "주간 계획 생성 요청"), ("ai", combined)],
        "rag_context": rag_context,
        "plan_results": results,
    }

# ── 그래프 구성 ──
workflow.add_node("initial_plan", generate_rule_based_plan)  # 등록명 유지 → interrupt_after 등 변경 불필요
```

> `return_exceptions=True`를 사용하면 4개 중 일부가 타임아웃/실패해도 나머지 결과를 반환합니다.
> `asyncio.gather`의 반환값은 순서대로 튜플이므로, `isinstance(val, Exception)` 체크로 실패 항목을 구분합니다.

### 5.5 서비스 레이어 — user_profile 공급 및 ainvoke

```python
# llm_service_rag.py

async def call_goal_plan_llm(self, plan_input: GoalPlanInput, db: Session) -> Dict[str, Any]:
    thread_id = f"plan_rag_{plan_input.user_id}_{plan_input.record_id}_{datetime.now().timestamp()}"
    config = {"configurable": {"thread_id": thread_id}}

    # ── user_profile: UserDetail에서 조회 ──
    active_detail = UserDetailRepository.get_active_detail(db, plan_input.user_id)
    user_profile = {
        "body_type1":      plan_input.body_type1 or "",
        "body_type2":      plan_input.body_type2 or "",
        "goal_type":       active_detail.goal_type       if active_detail else "",
        "health_specifics": active_detail.health_specifics if active_detail else "",
        "preferences":     active_detail.preferences     if active_detail else "",
    }

    # ── ainvoke (async node이므로 반드시 ainvoke 사용) ──
    initial_state = await self.weekly_plan_agent.ainvoke(
        {
            "plan_input":    plan_input,
            "messages":      [],
            "rag_context":   None,
            "user_profile":  user_profile,
            "plan_results":  None,
        },
        config=config,
    )

    return {
        "plan_text":    initial_state["messages"][-1].content,
        "plan_results": initial_state.get("plan_results"),
        "thread_id":    thread_id,
        "rag_context":  initial_state.get("rag_context", ""),
    }
```

### 5.6 Q&A 노드 — 변경 불필요

기존 Q&A 노드들은 `state["messages"]` 전체를 대화 히스토리로 사용합니다.
`generate_rule_based_plan`이 4개 결과를 종합하여 단일 AI message로 저장하면
Q&A에서 자동으로 전체 계획을 컨텍스트로 가집니다.

라우팅(`route_qa`), interrupt 목록, `finalize_plan` 모두 기존과 동일.

---

## 6. 그래프 다이어그램 (변경 전·후)

### 변경 전

```
[START]
  ↓
[initial_plan]                sync, LLM 1회 호출 (단일 프롬프트 → 전체 계획)
  ├── interrupt
  ↓
route_qa → [qa_*] ──→ interrupt (루프)
  ↓
[finalize_plan] → [END]
```

### 변경 후

```
[START]
  ↓
[initial_plan]                async, LLM 4회 병렬 호출
  │  ┌─ summary   ─┐
  │  ├─ workout   ─┤  asyncio.gather (동시 실행)
  │  ├─ diet      ─┤
  │  └─ lifestyle ─┘
  │  → 4개 결과를 종합하여 messages에 저장
  ├── interrupt              프론트에 종합 결과 표시
  ↓
route_qa → [qa_*] ──→ interrupt (루프)   ← 종합 결과 전체를 컨텍스트로 가짐
  ↓
[finalize_plan] → [END]
```

---

## 7. 주의사항 및 결정이 필요한 포인트

### 7.1 rule_based_prompts import 경로

현재 `rule_based_prompts.py`와 `rules.py`는 `src/llm/llm_prompt_test_sk/` 안에 있습니다.
백엔드(`backend/services/llm/`)에서 직접 import하려면 아래 중 하나를 선택해야 합니다:

- **옵션 A**: `src/llm/shared/` 등 공통 경로로 이동 후 양측에서 import
- **옵션 B**: `backend/services/llm/` 내부에 복사본 유지 (빠르지만 동기화 부담)
- **옵션 C**: `rules.py`는 향후 DB로 교체될 것이므로, `rule_based_prompts.py`만 이동하고 `rules.py`는 DB 조회로 대체하는 시점에 정리

### 7.2 ainvoke vs invoke

LangGraph node가 `async def`이면 반드시 `graph.ainvoke()`를 사용해야 합니다.
`invoke()`로 호출하면 async node의 내부 `await`가 실행되지 않습니다.

`chat_with_plan()` (Q&A 재개)도 동일하게 `ainvoke`로 변경해야 합니다.
Q&A 노드 자체는 sync이지만, async node와 같은 그래프 내에서 `ainvoke`로 실행하면 sync 노드도 정상 동작합니다.

### 7.3 temperature 통일

| 위치 | 현재 temperature |
|------|-----------------|
| `test_llm_call.py` (테스트) | 1.0 |
| `OpenAIClient` (백엔드) | 0.7 |

계획성 응답이므로 **0.7 권장**. `AsyncOpenAIClient`에도 0.7로 설정합니다.

### 7.4 MemorySaver의 async 지원

현재 `MemorySaver()`는 인메모리 체크포인터로 async 호환됩니다.
프로덕션으로 넘어간다면 `PostgresSaver`로 교체하면 `ainvoke` + 영속 저장 모두 지원됩니다.

### 7.5 GoalPlanInput 확장 가능성

현재 설계에서는 `user_profile`을 별도 State 키로 전달합니다.
다른 접근으로, `GoalPlanInput` 스키마에 `health_specifics`, `preferences`를 직접 추가하면
`user_profile` State 키가 불필요하여 단순화됩니다.
다만 이는 백엔드 스키마 변경을 수반하므로, 현재 단계에서는 State 키 방식이 안전합니다.

### 7.6 프론트엔드 응답 구조

현재 `call_goal_plan_llm`의 반환값은 `plan_text: str` (단일 문자열)입니다.
4개 결과를 개별적으로 프론트에 표시하려면 `plan_results: Dict[str, str]`도 반환에 포함시키면 됩니다.
종합 문자열(`plan_text`)은 하위 호환성을 위해 유지합니다.
