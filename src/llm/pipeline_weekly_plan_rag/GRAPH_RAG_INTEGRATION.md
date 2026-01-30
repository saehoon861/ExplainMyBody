# Graph RAG Integration 완료 보고서

ExplainMyBody 프로젝트에 Graph RAG 시스템을 성공적으로 통합했습니다.

## 📋 구현 완료 항목

### 1. Backend Models (PostgreSQL + pgvector)

**위치**: `backend/models/`

- ✅ **PaperNode** (`paper_node.py`)
  - 논문 데이터 저장 (2,100+ papers)
  - 임베딩 컬럼: `embedding_openai` (1536D), `embedding_ollama` (1024D), `embedding_ko_openai` (1536D)
  - 메타데이터: title, chunk_text, lang, domain, source, year, pmid, doi
  - pgvector 인덱스 지원

- ✅ **PaperConceptRelation** (`paper_concept_relation.py`)
  - 논문-개념 관계 저장 (9,100+ relations)
  - 관계 타입: MENTIONS, INCREASES, SUPPORTS, REDUCES
  - 메타데이터: confidence, matched_term, count, evidence_level
  - 복합 인덱스: (paper_id, concept_id), (concept_id, relation_type)

### 2. Backend Repositories

**위치**: `backend/repositories/`

- ✅ **PaperRepository** (`paper_repository.py`)
  - Vector 유사도 검색 (pgvector `<=>` operator)
  - 개념 기반 논문 검색
  - Bulk insert 지원

- ✅ **Neo4jRepository** (`neo4j_repository.py`)
  - Graph 탐색 (Cypher queries)
  - 개념 확장 (expand_concepts)
  - 처방 효과 조회 (get_intervention_effects)

### 3. Data Import Script

**위치**: `backend/utils/scripts/import_graph_rag.py`

- ✅ JSON → PostgreSQL 로딩
- ✅ JSON → Neo4j 로딩 (선택적)
- ✅ Bulk insert 최적화
- ✅ Progress tracking
- ✅ Error handling

**사용법**:
```bash
# PostgreSQL + Neo4j
python backend/utils/scripts/import_graph_rag.py --neo4j

# PostgreSQL만
python backend/utils/scripts/import_graph_rag.py

# 기존 데이터 삭제 후 재로드
python backend/utils/scripts/import_graph_rag.py --clear
```

### 4. LLM Pipeline with Graph RAG

**위치**: `src/llm/pipeline_weekly_plan_rag/`

- ✅ **GraphRAGRetriever** (`graph_rag_retriever.py`)
  - Hybrid Search: Vector (pgvector) + Graph (Neo4j)
  - OpenAI text-embedding-3-small 고정
  - Reranking: Vector Score (60%) + Graph Score (40%)

- ✅ **WeeklyPlannerGraphRAG** (`planner.py`)
  - InBody RAG + Graph RAG 통합
  - gpt-4o-mini 고정
  - 논문 컨텍스트 자동 포함

- ✅ **Main Pipeline** (`main.py`)
  - CLI 인터페이스
  - 자동 Graph RAG 적용
  - 결과 파일 저장 지원

**사용법**:
```bash
# 기본 실행
python src/llm/pipeline_weekly_plan_rag/main.py --user-id 1

# 목표/선호도 파일 지정
python src/llm/pipeline_weekly_plan_rag/main.py \
  --user-id 1 \
  --goals-file sample_user_goals.json \
  --preferences-file sample_user_preferences.json \
  --output-file outputs/plan.txt
```

## 🏗️ 아키텍처

### Graph RAG 검색 흐름

```
사용자 요청
    ↓
[1] 목표 분석
    - goal_type → 핵심 개념 추출
    - 예: "근성장" → ["muscle_hypertrophy", "resistance_training", "protein_intake"]
    ↓
[2] InBody RAG 검색
    - 사용자의 과거 InBody 분석 결과
    - Vector 유사도 검색 (pgvector)
    ↓
[3] Graph RAG 검색 (Hybrid)
    │
    ├─ Vector Search (PostgreSQL pgvector)
    │   - 쿼리 임베딩 (text-embedding-3-small, 1536D)
    │   - Cosine Similarity: 1 - (embedding <=> query)
    │   - Top 20 후보 논문 검색
    │
    ├─ Graph Traversal (Neo4j)
    │   - Concept → Paper 탐색
    │   - 관계 타입: MENTIONS, INCREASES, SUPPORTS
    │   - Confidence 기반 필터링
    │   - Top 10 관련 논문 검색
    │
    └─ Reranking
        - Vector Score (0.6 weight)
        - Graph Score (0.4 weight)
        - Final Score = 0.6 * similarity + 0.4 * confidence
        - Top K 최종 선택
    ↓
[4] LLM 계획 생성 (gpt-4o-mini)
    - System Prompt: 역할 정의
    - User Prompt: InBody + 논문 컨텍스트
    - 출력: 주간 운동/식단 계획
    ↓
[5] DB 저장 및 반환
```

### 데이터 흐름

```
graph_rag_*.json (2,149 nodes, 9,176 edges)
    ↓
[import_graph_rag.py]
    ↓
PostgreSQL (pgvector)          Neo4j (Graph DB)
- paper_nodes                  - Paper Nodes
  * embedding_ko_openai        - Concept Nodes
  * embedding_openai           - Relationships
  * embedding_ollama             * MENTIONS
- paper_concept_relations       * INCREASES
  * confidence                   * SUPPORTS
  * relation_type                * REDUCES
    ↓                               ↓
PaperRepository              Neo4jRepository
    ↓                               ↓
    └─────────┬─────────────────────┘
              ↓
      GraphRAGRetriever
              ↓
    WeeklyPlannerGraphRAG
              ↓
        주간 계획 생성
```

## 📊 데이터 통계

- **논문 총 개수**: 2,149개
- **관계 총 개수**: 9,176개
- **임베딩 차원**: 1536D (OpenAI text-embedding-3-small)
- **도메인**: protein_hypertrophy, fat_loss, general_health 등
- **출처**: PubMed, KCI, ScienceON
- **연도 범위**: 2015-2025

## 🔧 기술 스택

| 레이어 | 기술 |
|--------|------|
| Vector DB | PostgreSQL + pgvector |
| Graph DB | Neo4j + Cypher |
| Embedding | OpenAI text-embedding-3-small (1536D) |
| LLM | OpenAI gpt-4o-mini |
| ORM | SQLAlchemy |
| 언어 | Python 3.10+ |

## 📝 설정 가이드

### 1. 환경 변수 설정

`.env` 파일:
```bash
# PostgreSQL
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/explainmybody

# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

# OpenAI
OPENAI_API_KEY=sk-...
```

### 2. pgvector Extension 설치

```bash
# Ubuntu/Debian
sudo apt-get install postgresql-15-pgvector

# macOS
brew install pgvector

# SQL에서 활성화
CREATE EXTENSION IF NOT EXISTS vector;
```

### 3. 데이터베이스 초기화

```bash
# 테이블 생성 및 extension 활성화
python backend/utils/scripts/import_graph_rag.py
```

### 4. Neo4j 설치 (선택적)

```bash
# Docker로 실행
docker run -d \
  --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  neo4j:latest

# 브라우저에서 확인
http://localhost:7474
```

## 🚀 사용 예시

### 예시 1: 근성장 목표

```bash
python src/llm/pipeline_weekly_plan_rag/main.py \
  --user-id 1 \
  --goals-json '[{"goal_type":"근성장","priority":"high"}]' \
  --output-file outputs/plan_muscle.txt
```

**검색되는 개념**: muscle_hypertrophy, resistance_training, protein_intake

**검색되는 논문 예시**:
- "Resistance training-induced appendicular lean tissue mass changes..."
- "Effects of protein supplementation on muscle growth..."
- "Progressive overload and muscle hypertrophy..."

### 예시 2: 체지방감소 목표

```bash
python src/llm/pipeline_weekly_plan_rag/main.py \
  --user-id 1 \
  --goals-json '[{"goal_type":"체지방감소","priority":"high"}]'
```

**검색되는 개념**: fat_loss, caloric_deficit, cardio

**검색되는 논문 예시**:
- "High-intensity interval training for fat loss..."
- "Caloric deficit and body composition changes..."

## 🎯 주요 기능

### 1. Hybrid Search (Vector + Graph)

- **Vector Search**: 자연어 쿼리 → 임베딩 → 유사도 검색
  - 장점: 의미적 유사성 반영, 새로운 개념 발견
  - 단점: 관계 정보 부족

- **Graph Search**: 개념 → 관계 탐색 → 논문 검색
  - 장점: 명확한 관계 정보, 신뢰도 기반 필터링
  - 단점: 정의된 개념에만 제한

- **Hybrid**: 두 방법의 장점 결합
  - Vector로 넓게 탐색 → Graph로 정확도 향상
  - Reranking으로 최적 결과 선택

### 2. 개념 자동 매핑

사용자 목표를 자동으로 과학적 개념으로 변환:

| 사용자 목표 | 추출 개념 |
|------------|---------|
| 근성장 | muscle_hypertrophy, resistance_training, protein_intake |
| 체지방감소 | fat_loss, caloric_deficit, cardio |
| 건강유지 | general_health, exercise, balanced_diet |

### 3. 과학적 근거 제공

LLM 생성 계획에 최신 연구 논문 자동 인용:

```
## 📚 과학적 근거

### 논문 1: Resistance training-induced...
- 출처: PubMed (2025)
- 관련도: 0.82
- 요약: 저항 운동이 근육량 증가에...
```

## 🔍 성능 최적화

### 인덱스 활용

```sql
-- Vector 검색 가속화 (HNSW)
CREATE INDEX idx_embedding_openai ON paper_nodes
USING hnsw (embedding_openai vector_cosine_ops);

-- 복합 인덱스
CREATE INDEX idx_paper_concept ON paper_concept_relations(paper_id, concept_id);
CREATE INDEX idx_concept_relation ON paper_concept_relations(concept_id, relation_type);
```

### Batch Processing

- Vector Search: 후보 2배 검색 (Top 20) → Reranking
- Graph Traversal: 개념당 10개 제한
- Bulk Insert: 500개씩 배치 처리

### Caching (향후 개선)

- 쿼리 임베딩 캐싱
- 자주 사용되는 개념 결과 캐싱
- LRU Cache 적용

## 🐛 문제 해결

### pgvector 관련

**문제**: `operator does not exist: vector <=> vector`

**해결**:
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

### Neo4j 관련

**문제**: Neo4j 연결 실패

**해결**: `--no-neo4j` 플래그 사용 또는 Neo4j 설치

### 임베딩 관련

**문제**: 임베딩이 NULL인 논문

**해결**: JSON 데이터 재수집 또는 임베딩 재생성

## 📚 참고 문서

- `backend/models/README.md`: 데이터베이스 모델 설명
- `backend/utils/scripts/README.md`: 데이터 Import 가이드
- `src/llm/pipeline_weekly_plan_rag/README.md`: 파이프라인 사용법
- `src/llm/ragdb_collect/GRAPH_RAG_GUIDE.md`: Graph RAG 설계 문서

## 🎉 완료!

Graph RAG 시스템이 성공적으로 통합되었습니다. 이제 주간 계획 생성 시 2,100+ 최신 연구 논문을 기반으로 과학적 근거가 있는 계획을 제공할 수 있습니다.

**다음 단계**:
1. 데이터 Import: `python backend/utils/scripts/import_graph_rag.py --neo4j`
2. 테스트 실행: `python src/llm/pipeline_weekly_plan_rag/main.py --user-id 1`
3. API 통합: FastAPI 엔드포인트 추가
4. 프론트엔드 연동: 논문 인용 UI 추가
