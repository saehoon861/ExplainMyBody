# LLM RAG 모듈

RAG(Retrieval-Augmented Generation) 기반 건강 분석 및 주간 계획 생성 시스템

## 📁 디렉토리 구조

```
services/llm/llm_rag/
├── __init__.py                    # 모듈 진입점
├── README.md                      # 이 파일
│
├── llm_service_rag.py             # RAG LLM 서비스 (메인)
├── rag_retriever.py               # 논문 검색 (pgvector)
├── prompt_generator_rag.py        # 프롬프트 생성
│
├── agent_graph_rag.py             # InBody 분석 에이전트
├── weekly_plan_graph_rag.py       # 주간 계획 에이전트
├── weekly_plan_service_rag.py     # 주간 계획 서비스
│
├── data_ingestion/                # 데이터 입력 스크립트
│   ├── __init__.py
│   ├── ingest_json.py             # JSON → PostgreSQL
│   ├── ingest_cypher.py           # Cypher → PostgreSQL
│   └── README.md
│
└── docs/                          # 문서
    ├── RAG_INTEGRATION_SUMMARY.md
    └── RAG_USAGE_GUIDE.md
```

## 🚀 사용 방법

### 1. LLM 서비스 초기화

```python
from services.llm.llm_rag import LLMServiceRAG

llm_service = LLMServiceRAG(model_version="gpt-4o-mini", use_rag=True)
```

### 2. InBody 분석 (LLM1 + RAG)

```python
from schemas.llm import StatusAnalysisInput

result = await llm_service.call_status_analysis_llm(
    analysis_input=StatusAnalysisInput(...),
    thread_id="analysis_123"
)

# 결과: {"analysis_text": "...", "embedding": {...}, "rag_context": "..."}
```

### 3. 주간 계획 생성 (LLM2 + RAG)

```python
from schemas.llm import GoalPlanInput

result = await llm_service.call_goal_plan_llm(
    plan_input=GoalPlanInput(...),
    thread_id="plan_123"
)

# 결과: {"plan_text": "...", "thread_id": "...", "rag_context": "..."}
```

## 🔧 컴포넌트

### LLMServiceRAG

메인 서비스 클래스

- `call_status_analysis_llm()`: InBody 분석
- `call_goal_plan_llm()`: 주간 계획 생성
- `chat_with_analysis()`: 분석 결과 Q&A
- `chat_with_plan()`: 계획 수정 Q&A

### SimpleRAGRetriever

논문 검색 엔진

- PostgreSQL pgvector 사용
- OpenAI text-embedding-3-small (1536D)
- 코사인 유사도 검색

### Agent Graphs

LangGraph 기반 에이전트

- `agent_graph_rag.py`: 건강 상태 분석 + RAG
- `weekly_plan_graph_rag.py`: 주간 계획 생성 + RAG

## 📊 데이터 입력

### JSON 데이터 입력

```bash
cd backend

python -m services.llm.llm_rag.data_ingestion.ingest_json \
  /path/to/papers.json
```

### Cypher 데이터 입력

```bash
python -m services.llm.llm_rag.data_ingestion.ingest_cypher \
  /path/to/papers.cypher
```

자세한 내용은 `data_ingestion/README.md` 참고

## 🔗 의존성

### 내부 의존성

- `services/llm/llm_clients.py`: OpenAI 클라이언트
- `services/common/health_service_rag.py`: 건강 서비스 RAG
- `schemas/llm.py`: 입력/출력 스키마
- `schemas/inbody.py`: InBody 데이터 스키마
- `database.py`: PostgreSQL 연결

### 외부 패키지

- `langgraph`: 에이전트 그래프
- `openai`: LLM 및 임베딩
- `sqlalchemy`: DB 연결
- `pgvector`: 벡터 검색

## 📖 문서

- **RAG_INTEGRATION_SUMMARY.md**: RAG 통합 요약
- **RAG_USAGE_GUIDE.md**: 사용 가이드
- **data_ingestion/README.md**: 데이터 입력 가이드

## ⚙️ 환경 변수

`.env` 파일에 다음 설정 필요:

```bash
OPENAI_API_KEY=your_api_key
DATABASE_URL=postgresql://user:pass@host:port/db
```

## 🎯 사용 예시

### Router에서 사용

```python
# routers/llm/analysis_rag.py
from services.llm.llm_rag import LLMServiceRAG

llm_service_rag = LLMServiceRAG(model_version="gpt-4o-mini", use_rag=True)

@router.post("/{record_id}")
async def analyze_health_record_with_rag(...):
    result = await llm_service_rag.call_status_analysis_llm(...)
    return result
```

### Service에서 사용

```python
# services/common/health_service_rag.py
from services.llm.llm_rag import LLMServiceRAG

class HealthServiceRAG:
    def __init__(self):
        self.llm_service_rag = LLMServiceRAG(use_rag=True)
```

---

**개발자**: SK
**최종 수정**: 2026-02-03
