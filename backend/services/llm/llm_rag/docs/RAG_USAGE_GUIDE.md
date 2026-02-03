# RAG 통합 가이드

## 개요

`backend/services/llm/` 에 RAG(Retrieval-Augmented Generation) 기능이 추가되었습니다.
기존 LLM 서비스와 동일한 인터페이스를 제공하며, 논문 DB에서 관련 연구를 검색하여 과학적 근거 기반 분석을 제공합니다.

## 생성된 파일

### 1. `rag_retriever.py`
- **역할**: Simple Embedding-based RAG Retriever
- **기능**:
  - OpenAI text-embedding-3-small (1536D) 사용
  - PostgreSQL pgvector를 사용한 Vector 유사도 검색
  - Graph RAG 없음, Neo4j 없음 (순수 embedding 기반)
- **주요 메서드**:
  - `retrieve_relevant_papers(query, top_k, lang)`: 쿼리 기반 논문 검색
  - `format_papers_for_prompt(papers)`: 논문을 프롬프트 형식으로 포맷팅

### 2. `prompt_generator_rag.py`
- **역할**: RAG 컨텍스트가 포함된 프롬프트 생성
- **기능**:
  - 기존 `prompt_generator.py`의 프롬프트 스타일 유지
  - RAG 검색 결과(논문 정보)를 자연스럽게 프롬프트에 통합
- **주요 함수**:
  - `create_inbody_analysis_prompt_with_rag()`: InBody 분석용 프롬프트 (RAG 포함)
  - `create_weekly_plan_prompt_with_rag()`: 주간 계획용 프롬프트 (RAG 포함)

### 3. `agent_graph_rag.py`
- **역할**: RAG가 추가된 건강 상태 분석 LangGraph 에이전트
- **기능**:
  - `agent_graph.py` 기반, 동일한 구조 유지
  - 최초 분석 생성 시 RAG 논문 검색 자동 실행
  - Q&A 노드들은 기존과 동일
- **주요 함수**:
  - `create_analysis_agent_with_rag(llm_client, use_rag)`: RAG 에이전트 생성

### 4. `weekly_plan_graph_rag.py`
- **역할**: RAG가 추가된 주간 계획 LangGraph 에이전트
- **기능**:
  - `weekly_plan_graph.py` 기반, 동일한 구조 유지
  - 최초 계획 생성 시 RAG 논문 검색 자동 실행
  - Q&A 노드들은 기존과 동일
- **주요 함수**:
  - `create_weekly_plan_agent_with_rag(llm_client, use_rag)`: RAG 에이전트 생성

### 5. `llm_service_rag.py`
- **역할**: RAG가 추가된 LLM 서비스 (통합 인터페이스)
- **기능**:
  - 기존 `llm_service.py`와 동일한 인터페이스 제공
  - RAG 사용 여부를 `use_rag` 파라미터로 제어
- **주요 메서드**:
  - `call_status_analysis_llm()`: 건강 상태 분석 (RAG 포함)
  - `chat_with_analysis()`: 분석 결과 Q&A
  - `call_goal_plan_llm()`: 주간 계획 생성 (RAG 포함)
  - `chat_with_plan()`: 계획 Q&A

## 사용 방법

### 기존 서비스 (RAG 없음)

```python
from services.llm.llm_service import LLMService

service = LLMService(model_name="gpt-4o-mini")
result = await service.call_status_analysis_llm(analysis_input, thread_id)
```

### RAG 서비스 (RAG 포함)

```python
from services.llm.llm_service_rag import LLMServiceRAG

# RAG 활성화
service = LLMServiceRAG(model_name="gpt-4o-mini", use_rag=True)
result = await service.call_status_analysis_llm(analysis_input, thread_id)

# RAG 비활성화 (필요 시)
service = LLMServiceRAG(model_name="gpt-4o-mini", use_rag=False)
```

### 반환 값

#### `call_status_analysis_llm()` 반환값
```python
{
    "response": str,        # LLM 분석 결과
    "embedding": Dict,      # 임베딩 벡터 (1536D)
    "rag_context": str      # RAG 검색 결과 (논문 정보, 디버깅용)
}
```

#### `call_goal_plan_llm()` 반환값
```python
{
    "response": str,        # LLM 주간 계획
    "rag_context": str      # RAG 검색 결과 (논문 정보, 디버깅용)
}
```

## RAG 검색 로직

### InBody 분석 시 RAG 쿼리 생성
사용자의 InBody 측정값을 기반으로 자동으로 검색 쿼리를 생성합니다:

```python
# 예시: 남성 30세, 체지방률 28%, 근육 부족
# 생성되는 쿼리: "남성 30세 체지방 감소 근육량 증가 근성장"
```

**쿼리 생성 규칙**:
- 성별, 나이 포함
- BMI 상태 (저체중/과체중/비만)
- 체지방률 상태 (성별 기준)
- 골격근량 상태 (근육조절 필드)
- 내장지방 레벨

### 주간 계획 시 RAG 쿼리 생성
사용자의 목표 및 선호도를 기반으로 검색 쿼리를 생성합니다:

```python
# 예시: 목표 "근성장", 선호 운동 "웨이트"
# 생성되는 쿼리: "근성장 웨이트 근육량 증가"
```

**쿼리 생성 규칙**:
- 주요 목표 (main_goal)
- 선호 운동 종류 (preferred_exercise_types)
- 체성분 기반 키워드 (체지방률, 근육조절)

## RAG 검색 결과 형식

논문 검색 결과는 다음과 같은 형식으로 프롬프트에 추가됩니다:

```markdown
## 📚 과학적 근거 (최신 연구 논문)

다음은 사용자의 체성분 상태와 관련된 최신 연구 결과입니다:

### 📄 논문 1: Effects of resistance training on muscle hypertrophy
- 출처: PubMed (2023)
- 관련도: 85.32%
- 요약: 저항성 운동은 골격근량을 평균 12.5% 증가시키며, 주 3회 이상 실시 시 효과가 극대화됩니다...

### 📄 논문 2: ...
```

## 데이터베이스 요구사항

RAG 기능을 사용하기 위해서는 다음이 필요합니다:

1. **PostgreSQL with pgvector 확장**
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```

2. **paper_nodes 테이블**
   - `embedding_ko_openai` (vector(1536)): 한국어 요약 임베딩
   - `chunk_ko_summary` (TEXT): 한국어 요약 (exaone3.5:7.8b로 생성)
   - `chunk_text` (TEXT): 영어 초록

3. **임베딩 생성 완료**
   - `src/llm/ragdb_collect/build_graph_rag.py --ko-summary --ko-embedding` 실행 완료

## 성능 고려사항

- **임베딩 생성**: 최초 분석/계획 생성 시 OpenAI API 호출 (약 0.1초)
- **Vector 검색**: PostgreSQL pgvector 사용, 빠른 검색 (약 0.05초)
- **검색 개수**: 기본 top_k=5 (필요 시 조정 가능)
- **Graph RAG 없음**: Neo4j 그래프 탐색 없음 (성능 최적화)

## 주의사항

1. **RAG 컨텍스트 크기**: 논문 5개 기준 약 1,500 토큰 추가
2. **프롬프트 길이**: RAG 사용 시 전체 프롬프트가 약 30% 증가
3. **비용**: OpenAI 임베딩 API 호출 비용 발생 (검색당 약 $0.0001)
4. **언어**: 현재 한국어 임베딩만 지원 (embedding_ko_openai)

## 디버깅

RAG 검색 과정을 확인하려면:

```python
service = LLMServiceRAG(use_rag=True)
result = await service.call_status_analysis_llm(analysis_input, thread_id)

# RAG 검색 결과 확인
print(result["rag_context"])
```

출력 예시:
```
🔍 RAG 논문 검색 중...
  검색 쿼리: 남성 30세 체지방 감소 근육량 증가

  📊 1단계: 쿼리 임베딩 생성 중...
    ✓ 임베딩 완료 (차원: 1536)D

  🔎 2단계: Vector 유사도 검색 (PostgreSQL)...
    ✓ 5개 관련 논문 검색 완료

    1. Score: 0.823 - Effects of resistance training on muscle...
    2. Score: 0.795 - High-protein diet and body composition...
    ...
```

## FAQ

### Q1. RAG를 사용하면 응답 품질이 얼마나 개선되나요?
A: 논문 기반 과학적 근거가 추가되어 더 신뢰성 있는 분석을 제공합니다. 특히 "왜 이런 분석 결과가 나왔는지" 설명하는 데 도움이 됩니다.

### Q2. RAG 없이 사용할 수 있나요?
A: 네, `use_rag=False`로 설정하면 기존 LLM 서비스와 동일하게 작동합니다.

### Q3. 검색되는 논문 개수를 늘리고 싶어요.
A: `rag_retriever.py`에서 `retrieve_relevant_papers()` 메서드의 `top_k` 파라미터를 조정하세요.

### Q4. 영어 논문도 검색하고 싶어요.
A: 현재는 한국어 임베딩만 지원합니다. 영어 논문 검색을 위해서는 `embedding_openai` (영어) 필드를 추가로 사용해야 합니다.

## 향후 개선 사항

- [ ] 영어 논문 검색 지원
- [ ] Reranking 모델 추가 (검색 정확도 향상)
- [ ] 사용자 피드백 기반 RAG 개선
- [ ] Cache 기능 추가 (동일 쿼리 재검색 방지)

---

**문의**: RAG 관련 이슈가 있다면 프로젝트 이슈 트래커에 등록해주세요.
