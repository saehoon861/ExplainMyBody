# LangGraph 2단계 파이프라인 가이드

## 개요

LangGraph를 사용하여 LLM을 2번 호출하는 파이프라인:
1. **Step 1**: 자연어로 추천 생성
2. **Step 2**: 자연어를 JSON 형식으로 변환

## LangGraph란?

LangGraph는 **상태 그래프(State Graph)** 기반으로 LLM 워크플로우를 구축하는 라이브러리입니다.

### 핵심 개념

#### 1. State (상태)
- 그래프를 통해 전달되는 **데이터 구조**
- 각 노드는 상태를 받아서 업데이트하고 다음 노드로 전달
- TypedDict로 정의하여 타입 안정성 확보

```python
class PipelineState(TypedDict):
    analysis_result: dict          # 입력: 체형 분석 결과
    natural_language_response: str # Step 1 출력
    json_response: dict            # Step 2 출력
    error: str | None              # 에러 추적
```

#### 2. Nodes (노드)
- 각 **처리 단계**를 나타내는 함수
- `state`를 입력으로 받아 **업데이트된 state**를 반환
- 순수 함수처럼 동작 (side effect 최소화)

```python
def generate_natural_language(state: PipelineState, client) -> PipelineState:
    # 1. 상태에서 데이터 읽기
    analysis = state["analysis_result"]

    # 2. LLM 호출
    natural_response = client.generate_chat(system_prompt, user_prompt)

    # 3. 상태 업데이트
    state["natural_language_response"] = natural_response

    # 4. 업데이트된 상태 반환
    return state
```

#### 3. Edges (엣지)
- 노드 간의 **연결**을 정의
- 두 가지 타입:
  - **일반 Edge**: 항상 다음 노드로 이동
  - **Conditional Edge**: 조건에 따라 다른 노드로 분기

```python
# 일반 Edge
workflow.add_edge("convert_to_json", END)

# Conditional Edge
workflow.add_conditional_edges(
    "generate_natural_language",  # 현재 노드
    should_continue,               # 조건 함수
    {
        "convert_to_json": "convert_to_json",  # 성공 시
        "end": END                              # 실패 시
    }
)
```

## 파이프라인 구조

```
┌─────────────────────────────────────────────────────────┐
│                      START                              │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│  Node 1: generate_natural_language                      │
│  ────────────────────────────────────                   │
│  Input:  analysis_result                                │
│  Process: LLM 호출 (자연어 생성)                         │
│  Output: natural_language_response                      │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
              ┌──────┴──────┐
              │should_continue│ (조건 확인)
              └──────┬──────┘
                     │
        ┌────────────┼────────────┐
        │                         │
   error?                      success?
        │                         │
        ▼                         ▼
   ┌────────┐         ┌─────────────────────────────────┐
   │  END   │         │ Node 2: convert_to_json         │
   └────────┘         │ ───────────────────────────     │
                      │ Input:  natural_language_resp.  │
                      │ Process: LLM 호출 (JSON 변환)   │
                      │ Output: json_response           │
                      └────────────┬────────────────────┘
                                   │
                                   ▼
                              ┌────────┐
                              │  END   │
                              └────────┘
```

## 동작 원리

### 1. 초기화
```python
# 1) StateGraph 생성
workflow = StateGraph(PipelineState)

# 2) 노드 추가
workflow.add_node("generate_natural_language", node_function_1)
workflow.add_node("convert_to_json", node_function_2)

# 3) 엔트리 포인트 설정
workflow.set_entry_point("generate_natural_language")

# 4) 엣지 연결
workflow.add_conditional_edges(...)
workflow.add_edge(...)

# 5) 컴파일
app = workflow.compile()
```

### 2. 실행
```python
# 초기 상태 설정
initial_state = {
    "analysis_result": {...},
    "natural_language_response": None,
    "json_response": None,
    "error": None
}

# 그래프 실행
final_state = app.invoke(initial_state)
```

### 3. 상태 전달 과정

```
초기 상태
{
  "analysis_result": {...},
  "natural_language_response": None,
  "json_response": None,
  "error": None
}
        │
        ▼ [Node 1 실행]
{
  "analysis_result": {...},
  "natural_language_response": "자연어 텍스트...",  ← 업데이트
  "json_response": None,
  "error": None
}
        │
        ▼ [should_continue 조건 확인]
        │
        ▼ [Node 2 실행]
{
  "analysis_result": {...},
  "natural_language_response": "자연어 텍스트...",
  "json_response": {...},  ← 업데이트
  "error": None
}
        │
        ▼ [END]
최종 상태 반환
```

## 왜 2단계로 나누는가?

### 장점

1. **더 나은 품질**
   - Step 1: 창의적이고 자연스러운 추천 생성에 집중
   - Step 2: 구조화에만 집중 (부담 감소)
   - 각 단계가 단일 책임 원칙 준수

2. **오류 복구 가능**
   - Step 1 실패 → 즉시 종료
   - Step 2 실패 → Step 1 결과는 여전히 사용 가능 (텍스트로 저장)

3. **디버깅 용이**
   - 각 단계의 출력을 개별적으로 확인 가능
   - 어느 단계에서 문제가 생겼는지 명확히 파악

4. **유연성**
   - Step 1의 프롬프트를 창의성 중심으로 작성
   - Step 2의 프롬프트를 정확성 중심으로 작성
   - 각각 다른 모델 사용 가능 (예: GPT-4o-mini → GPT-4o)

### 비교: 1단계 vs 2단계

| 구분 | 1단계 (직접 JSON 생성) | 2단계 (자연어 → JSON) |
|------|----------------------|---------------------|
| **생성 품질** | JSON 구조 제약으로 품질 저하 가능 | 자연어 생성으로 품질 향상 |
| **JSON 정확도** | 한 번에 실패하면 전체 실패 | 2차 검증으로 정확도 향상 |
| **비용** | 1회 호출 (저렴) | 2회 호출 (비싸지만 품질 우선) |
| **복구 가능성** | 실패 시 재시도만 가능 | 자연어는 살릴 수 있음 |

## 사용 방법

### 1. 의존성 설치

```bash
pip install langgraph langchain-core
```

requirements.txt에 추가:
```
langgraph>=0.2.0
langchain-core>=0.3.0
```

### 2. 실행

```bash
# Claude 사용
python langgraph_pipeline.py --model claude-3-5-sonnet-20241022

# OpenAI 사용
python langgraph_pipeline.py --model gpt-4o-mini
```

### 3. 출력 결과

- `langgraph_output.json`: 구조화된 JSON 추천
- `langgraph_output_natural.txt`: 자연어 추천

## 확장 가능성

### 3단계 이상으로 확장

```python
# Step 3 추가: JSON 검증 및 보완
workflow.add_node("validate_and_refine", validate_function)

# Edge 연결
workflow.add_edge("convert_to_json", "validate_and_refine")
workflow.add_edge("validate_and_refine", END)
```

### 병렬 처리

```python
# 운동 추천과 식단 추천을 병렬로 생성
workflow.add_node("generate_exercise", exercise_function)
workflow.add_node("generate_diet", diet_function)

# 둘 다 실행 후 병합
workflow.add_node("merge_results", merge_function)
```

### 재시도 로직

```python
def should_retry(state: PipelineState) -> str:
    if state.get("error") and state.get("retry_count", 0) < 3:
        return "retry"
    return "end"

workflow.add_conditional_edges(
    "convert_to_json",
    should_retry,
    {
        "retry": "convert_to_json",  # 다시 시도
        "end": END
    }
)
```

## LangGraph vs 일반 함수 호출

### 일반 함수 방식
```python
# 순차 실행
natural = generate_natural(analysis)
json_result = convert_json(natural)
```

**단점:**
- 상태 관리가 암묵적
- 조건부 분기가 복잡해짐
- 재시도/병렬 처리 구현이 어려움
- 시각화 불가능

### LangGraph 방식
```python
# 그래프로 정의
app = create_pipeline()
result = app.invoke(initial_state)
```

**장점:**
- 명시적 상태 관리
- 선언적 워크플로우 정의
- 복잡한 로직도 깔끔하게 표현
- 그래프 시각화 가능 (`app.get_graph().draw_mermaid()`)

## 참고 자료

- [LangGraph 공식 문서](https://langchain-ai.github.io/langgraph/)
- [LangGraph GitHub](https://github.com/langchain-ai/langgraph)
- [State Graph 개념](https://langchain-ai.github.io/langgraph/concepts/low_level/)
