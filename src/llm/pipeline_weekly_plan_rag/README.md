# 주간 계획 생성 파이프라인 (Graph RAG)

InBody 분석 결과 + 최신 연구 논문 기반 주간 운동/식단 계획 생성 파이프라인입니다.

## 특징

- ✅ **Graph RAG 자동 적용**: Vector Search (pgvector) + Graph Traversal (Neo4j) 하이브리드 검색
- ✅ **고정 모델**: gpt-4o-mini, text-embedding-3-small 항상 사용
- ✅ **과학적 근거**: 최신 연구 논문 (2,100+ papers) 기반 계획 생성
- ✅ **개인화**: InBody 분석 결과 + 사용자 목표/선호도 반영

## Graph RAG 구조

```
사용자 목표 입력
    ↓
1. InBody RAG 검색 (기존)
    - 사용자의 과거 InBody 분석 결과 검색
    - pgvector 벡터 유사도 검색
    ↓
2. Graph RAG 검색 (신규)
    ├─ Vector Search (PostgreSQL pgvector)
    │   - 쿼리 임베딩 생성 (text-embedding-3-small)
    │   - 유사한 논문 검색 (cosine similarity)
    │
    ├─ Graph Traversal (Neo4j)
    │   - 목표 → 핵심 개념 추출 (muscle_hypertrophy, protein_intake 등)
    │   - 개념 → 관련 논문 탐색 (MENTIONS, INCREASES, SUPPORTS 관계)
    │
    └─ Reranking
        - Vector Score (60%) + Graph Score (40%)
        - 상위 K개 최종 선택
    ↓
3. LLM 계획 생성 (gpt-4o-mini)
    - InBody 컨텍스트 + 논문 컨텍스트 → 주간 계획
    ↓
4. DB 저장 및 반환
```

## 사용법

### 기본 실행

```bash
# 최소 인자 (기본 목표/선호도 사용)
python src/llm/pipeline_weekly_plan_rag/main.py --user-id 1

# 목표 및 선호도 JSON 파일 지정
python src/llm/pipeline_weekly_plan_rag/main.py \
  --user-id 1 \
  --goals-file src/llm/pipeline_weekly_plan_rag/sample_user_goals.json \
  --preferences-file src/llm/pipeline_weekly_plan_rag/sample_user_preferences.json

# 결과를 파일로 저장
python src/llm/pipeline_weekly_plan_rag/main.py \
  --user-id 1 \
  --output-file outputs/weekly_plan_graph_rag.txt
```

### 고급 옵션

```bash
# Neo4j 그래프 탐색 비활성화 (Vector만 사용)
python src/llm/pipeline_weekly_plan_rag/main.py \
  --user-id 1 \
  --no-neo4j

# 주차 및 시작 날짜 지정
python src/llm/pipeline_weekly_plan_rag/main.py \
  --user-id 1 \
  --week-number 2 \
  --start-date 2026-02-03

# 커스텀 DB URL
python src/llm/pipeline_weekly_plan_rag/main.py \
  --user-id 1 \
  --db-url postgresql://user:pass@localhost:5432/mydb
```

### CLI 옵션

| 옵션 | 설명 | 필수 | 기본값 |
|------|------|------|--------|
| `--user-id` | 사용자 ID | ✅ | - |
| `--goals-json` | 목표 JSON 문자열 | | 기본 목표 |
| `--goals-file` | 목표 JSON 파일 | | 기본 목표 |
| `--preferences-json` | 선호도 JSON 문자열 | | 기본 선호도 |
| `--preferences-file` | 선호도 JSON 파일 | | 기본 선호도 |
| `--week-number` | 주차 | | 1 |
| `--start-date` | 시작 날짜 (YYYY-MM-DD) | | 다음 주 월요일 |
| `--db-url` | 데이터베이스 URL | | 환경변수 |
| `--output-file` | 결과 저장 TXT 파일 | | 출력 안함 |
| `--no-neo4j` | Neo4j 비활성화 | | False |

## 입력 형식

### sample_user_goals.json

```json
[
  {
    "goal_type": "근성장",
    "priority": "high"
  },
  {
    "goal_type": "체지방감소",
    "priority": "medium"
  }
]
```

**goal_type 옵션**: 근성장, 체지방감소, 건강유지, 체력증진, 근력증가

**priority 옵션**: high, medium, low

### sample_user_preferences.json

```json
{
  "preferred_exercise_types": ["웨이트", "유산소"],
  "exercise_frequency": 4,
  "exercise_duration": 60,
  "exercise_intensity": "high",
  "dietary_restrictions": [],
  "preferred_cuisine": ["한식"],
  "disliked_foods": [],
  "meal_frequency": 3,
  "health_conditions": [],
  "injuries": [],
  "medications": []
}
```

## 출력 형식

### 콘솔 출력

```
============================================================
주간 계획 생성 시작 (User ID: 1, Week 1)
  🔧 모델: gpt-4o-mini
  🔧 Graph RAG: ✅ Enabled
============================================================

🔍 1단계: InBody 분석 결과 검색...
  ✓ 6개 유사 분석 검색 완료

🔍 2단계: Graph RAG 논문 검색...
  - 쿼리: '근성장, 체지방감소 목표를 위한 웨이트, 유산소 운동 효과'
  - 개념: ['muscle_hypertrophy', 'fat_loss', 'resistance_training']

  📊 1단계: 쿼리 임베딩 생성 중...
    ✓ 임베딩 완료 (차원: 1536)

  🔎 2단계: Vector 유사도 검색 (PostgreSQL)...
    ✓ 10개 후보 논문 검색 완료

  🔷 3단계: Graph 탐색 (Neo4j)...
    ✓ 5개 그래프 기반 논문 발견

  🎯 4단계: 결과 병합 및 Reranking...
    ✓ 최종 5개 논문 선정

    1. [hybrid] Score: 0.823 - Resistance training-induced appendicular lean...
    2. [vector] Score: 0.742 - Effects of protein supplementation on muscle...
    3. [graph] Score: 0.681 - The role of resistance training in fat loss...

📝 3단계: 프롬프트 생성...

🤖 4단계: LLM 주간 계획 생성 (gpt-4o-mini)...
  ✓ 계획 생성 완료 (3247 글자)

============================================================
✨ 주간 계획 생성 완료!
============================================================

💾 주간 계획 저장...
  ✓ DB 저장 완료 (Plan ID: 123)

============================================================
📋 주간 계획 결과 (Graph RAG)
============================================================
✅ 성공!
   - Plan ID: 123
   - 모델: gpt-4o-mini
   - Embedding: text-embedding-3-small
   - Graph RAG: ✅ 적용됨

[주간 계획 내용...]
```

### 파일 출력 (--output-file 사용 시)

```
================================================================================
주간 운동/식단 계획 (Graph RAG 적용)
================================================================================

Plan ID: 123
주차: 1
기간: 2026-02-03 ~ 2026-02-09
모델: gpt-4o-mini
Embedding: text-embedding-3-small
Graph RAG: ✅ 적용됨

--------------------------------------------------------------------------------

[LLM이 생성한 주간 계획 자연어 출력...]

## 📚 과학적 근거

이번 주 계획은 다음 최신 연구 결과를 기반으로 작성되었습니다:

### 논문 1: Resistance training-induced appendicular lean...
- 출처: PubMed (2025)
- 관련도: 0.82
- 요약: 저항 운동이 근육량 증가에 미치는 영향...

[추가 논문들...]
```

## Graph RAG 개념 매핑

| 사용자 목표 | 자동 추출 개념 |
|------------|--------------|
| 근성장 | muscle_hypertrophy, resistance_training, protein_intake |
| 체지방감소 | fat_loss, caloric_deficit, cardio |
| 건강유지 | general_health, exercise, balanced_diet |
| 체력증진 | endurance, cardiovascular_fitness |
| 근력증가 | strength_training, progressive_overload |

## 환경 변수

프로젝트 루트의 `.env` 파일에 다음 변수 설정:

```bash
# PostgreSQL (pgvector)
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/explainmybody

# Neo4j (선택적, --no-neo4j 플래그로 비활성화 가능)
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

# OpenAI (필수)
OPENAI_API_KEY=sk-...
```

## 데이터 준비

Graph RAG를 사용하기 전에 논문 데이터를 데이터베이스에 로드해야 합니다:

```bash
# PostgreSQL + Neo4j에 데이터 로드
python backend/utils/scripts/import_graph_rag.py --neo4j

# PostgreSQL만 사용 (Neo4j 없이)
python backend/utils/scripts/import_graph_rag.py
```

자세한 내용은 `backend/utils/scripts/README.md` 참고.

## 파일 구조

```
pipeline_weekly_plan_rag/
├── __init__.py                    # 패키지 초기화
├── main.py                        # 실행 파일 (CLI)
├── planner.py                     # 계획 생성 로직 (Graph RAG 통합)
├── graph_rag_retriever.py         # Graph RAG 검색기 (Vector + Graph)
├── prompt_generator.py            # 프롬프트 생성 (기존과 동일)
├── sample_user_goals.json         # 샘플 목표
├── sample_user_preferences.json   # 샘플 선호도
└── README.md                      # 이 파일
```

## 성능

- **Vector Search**: ~100ms (pgvector cosine similarity)
- **Graph Traversal**: ~200ms (Neo4j Cypher query)
- **Reranking**: ~10ms
- **LLM 생성**: ~5-10s (gpt-4o-mini)
- **Total**: ~6-11s per request

## 기존 파이프라인과의 차이점

| 기능 | pipeline_weekly_plan | pipeline_weekly_plan_rag |
|------|---------------------|--------------------------|
| InBody RAG | ✅ | ✅ |
| 논문 검색 | ❌ | ✅ (Graph RAG) |
| Vector Search | InBody만 | InBody + Papers |
| Graph Traversal | ❌ | ✅ (Neo4j) |
| 모델 | 사용자 지정 | gpt-4o-mini 고정 |
| Embedding | 사용자 선택 | text-embedding-3-small 고정 |
| 과학적 근거 | ❌ | ✅ (논문 인용) |

## 문제 해결

### Neo4j 연결 실패

```
⚠️  Neo4j 연결 실패. Vector 검색만 사용합니다.
```

**해결**: `--no-neo4j` 플래그를 사용하거나 Neo4j를 설치하고 환경변수를 설정하세요.

### pgvector extension 오류

```
❌ pgvector extension을 찾을 수 없습니다
```

**해결**: PostgreSQL에 pgvector extension을 설치하세요:
```bash
sudo apt-get install postgresql-15-pgvector
```

### 논문 데이터 없음

```
⚠️  관련 논문이 없습니다.
```

**해결**: `backend/utils/scripts/import_graph_rag.py`를 실행하여 논문 데이터를 로드하세요.

## 참고

- Graph RAG 논문 수집: `src/llm/ragdb_collect/`
- 데이터 Import: `backend/utils/scripts/import_graph_rag.py`
- 기존 파이프라인: `src/llm/pipeline_weekly_plan/`
