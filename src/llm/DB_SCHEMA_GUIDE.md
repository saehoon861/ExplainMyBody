# ExplainMyBody 데이터베이스 스키마 가이드

**생성일:** 2026-02-02
**DB:** PostgreSQL + pgvector
**시각화:** dbdiagram.io

---

## 🎨 dbdiagram.io에서 보기

### 1. 파일 열기

```bash
cat /home/user/projects/ExplainMyBody/backend/DB_SCHEMA.dbml
```

### 2. dbdiagram.io에 붙여넣기

1. https://dbdiagram.io/ 접속
2. 좌측 상단 "New Diagram" 클릭
3. `DB_SCHEMA.dbml` 내용 전체 복사
4. 에디터에 붙여넣기
5. **자동으로 다이어그램 생성됨!** ✨

### 3. 시각화 결과 확인

자동으로 다음 요소들이 표시됩니다:
- ✅ 7개 테이블
- ✅ 모든 컬럼 (데이터 타입, NULL 여부, 기본값)
- ✅ Primary Key / Foreign Key
- ✅ 관계선 (1:N)
- ✅ 인덱스
- ✅ 주석 (Note)
- ✅ 테이블 그룹 (색상별 구분)

---

## 📊 테이블 구조

### 사용자 관리 (User Management)

#### users (사용자 기본 정보)
```
id              INTEGER PK
username        VARCHAR(255) UNIQUE
email           VARCHAR(255) UNIQUE
password_hash   VARCHAR(255)
created_at      TIMESTAMP
```

#### user_details (사용자 목표/상세정보)
```
id                  INTEGER PK
user_id             INTEGER FK -> users.id
goal_type           VARCHAR(255)      # 체중감량, 근육증가 등
goal_description    TEXT              # JSON 형태
preferences         TEXT
health_specifics    TEXT
started_at          TIMESTAMP
ended_at            TIMESTAMP         # NULL = 진행중
is_active           INTEGER           # 1=활성, 0=비활성
```

**관계:**
- users (1) → (N) user_details
- 한 사용자가 여러 목표 설정 이력 보유 가능

---

### 건강 데이터 (Health Data)

#### health_records (건강 기록)
```
id              INTEGER PK
user_id         INTEGER FK -> users.id
source          VARCHAR(100)    # manual, ocr, api
measured_at     TIMESTAMP
measurements    JSONB           # InBody 측정 데이터 전체
created_at      TIMESTAMP
```

**measurements JSONB 구조:**
```json
{
  "기본정보": {"키": 175.0, "체중": 70.0, ...},
  "체성분": {"체수분": 42.0, "단백질": 12.5, ...},
  "체중관리": {"체중": 70.0, "골격근량": 32.5, ...},
  "비만분석": {"BMI": 22.9, "체지방률": 18.5, ...},
  "부위별근육분석": {...},
  "부위별체지방분석": {...},
  "연구항목": {"기초대사량": 1603, ...},
  "body_type1": "비만형",
  "body_type2": "상체발달형"
}
```

#### inbody_analysis_reports (InBody 분석 리포트)
```
id                  INTEGER PK
user_id             INTEGER FK -> users.id
record_id           INTEGER FK -> health_records.id
llm_output          TEXT            # LLM 분석 결과 (마크다운)
model_version       VARCHAR(100)    # gpt-4o-mini 등
analysis_type       VARCHAR(50)     # status_analysis, goal_plan
generated_at        TIMESTAMP
embedding_1536      VECTOR(1536)    # OpenAI 임베딩
embedding_1024      VECTOR(1024)    # Ollama 임베딩
```

**관계:**
- users (1) → (N) inbody_analysis_reports
- health_records (1) → (N) inbody_analysis_reports
- 한 건강 기록에 여러 분석 보고서 생성 가능 (재분석)

#### weekly_plans (주간 계획)
```
id              INTEGER PK
user_id         INTEGER FK -> users.id
week_number     INTEGER         # 주차
start_date      DATE
end_date        DATE
plan_data       JSONB           # 주간 계획 데이터
model_version   VARCHAR(100)
created_at      TIMESTAMP
```

**plan_data JSONB 구조:**
```json
{
  "monday": {
    "exercise": "상체 근력 운동 (30분)",
    "nutrition": "단백질 150g, 탄수화물 250g"
  },
  "tuesday": {...},
  ...
}
```

---

### Graph RAG (논문 검색)

#### paper_nodes (논문 노드)
```
id                      INTEGER PK
paper_id                VARCHAR(100) UNIQUE  # paper_12345678

# 텍스트
title                   TEXT
chunk_text              TEXT                 # 원본 초록
lang                    VARCHAR(10)          # ko, en
chunk_ko_summary        TEXT                 # 한국어 요약

# 메타데이터
domain                  VARCHAR(100)         # protein_hypertrophy, fat_loss
source                  VARCHAR(50)          # pubmed, kci, scienceon
year                    INTEGER
pmid                    VARCHAR(50)
doi                     VARCHAR(100)
authors                 JSONB                # ["Author1", "Author2"]
journal                 VARCHAR(200)
keywords                JSONB                # ["keyword1", "keyword2"]

# 임베딩
embedding_openai        VECTOR(1536)         # OpenAI
embedding_ollama        VECTOR(1024)         # Ollama
embedding_ko_openai     VECTOR(1536)         # 한국어 임베딩

embedding_provider      VARCHAR(50)          # openai, ollama

created_at              TIMESTAMP
updated_at              TIMESTAMP
```

**데이터 예시:**
```
paper_id: "paper_41415307"
title: "Effects of resistance training on sarcopenia in elderly"
chunk_text: "This study examined the effects of resistance training..."
lang: "en"
chunk_ko_summary: "본 연구는 노인 근감소증에 대한 저항성 운동의 효과를 조사했습니다..."
domain: "protein_hypertrophy"
source: "pubmed"
year: 2023
```

#### paper_concept_relations (논문-개념 관계)
```
id                  INTEGER PK
paper_id            INTEGER FK -> paper_nodes.id
concept_id          VARCHAR(100)    # muscle_hypertrophy, protein_intake

# 관계 타입
relation_type       VARCHAR(50)     # MENTIONS, INCREASES, SUPPORTS, REDUCES

# 메타데이터
confidence          FLOAT           # 0.0 ~ 1.0
matched_term        VARCHAR(200)    # 매칭된 용어
count               INTEGER         # 등장 횟수
evidence_level      VARCHAR(50)     # high, medium, low
magnitude           FLOAT           # 효과 크기

# 개념 정보 (비정규화)
concept_name_ko     VARCHAR(100)    # 근비대
concept_name_en     VARCHAR(100)    # muscle_hypertrophy
concept_type        VARCHAR(50)     # Outcome, Intervention, Biomarker

created_at          TIMESTAMP
```

**데이터 예시:**
```
paper_id: 1
concept_id: "muscle_hypertrophy"
relation_type: "INCREASES"
confidence: 0.92
matched_term: "resistance training"
count: 15
evidence_level: "high"
magnitude: 0.35
concept_name_ko: "근비대"
concept_name_en: "muscle hypertrophy"
concept_type: "Outcome"
```

---

## 🔗 관계 (Relationships)

### 1:N 관계

```
users (1) → (N) user_details
users (1) → (N) health_records
users (1) → (N) inbody_analysis_reports
users (1) → (N) weekly_plans

health_records (1) → (N) inbody_analysis_reports

paper_nodes (1) → (N) paper_concept_relations
```

### Cascade 삭제

모든 FK는 `ON DELETE CASCADE` 설정:
- User 삭제 시 → 모든 관련 데이터 자동 삭제
- HealthRecord 삭제 시 → 관련 AnalysisReport 자동 삭제
- PaperNode 삭제 시 → 관련 Relation 자동 삭제

---

## 📑 인덱스 전략

### Primary Key 인덱스
모든 테이블의 `id` 컬럼

### Foreign Key 인덱스
```sql
-- 사용자 관련
idx_user_details_user_id
idx_health_records_user_id
idx_inbody_analysis_user_id
idx_inbody_analysis_record_id

-- Graph RAG
idx_paper_nodes_paper_id (UNIQUE)
idx_paper_nodes_lang
idx_paper_nodes_domain
idx_paper_nodes_year
idx_paper_concept_relations_paper_id
idx_paper_concept_relations_concept_id
idx_paper_concept_relations_relation_type
```

### 복합 인덱스
```sql
-- paper_concept_relations 테이블
idx_paper_concept (paper_id, concept_id)
idx_concept_relation (concept_id, relation_type)
```

---

## 🎯 주요 쿼리 패턴

### 1. 사용자의 최신 건강 기록 조회

```sql
SELECT hr.*, iar.llm_output
FROM health_records hr
LEFT JOIN inbody_analysis_reports iar ON hr.id = iar.record_id
WHERE hr.user_id = ?
ORDER BY hr.measured_at DESC
LIMIT 1;
```

### 2. 활성 사용자 목표 조회

```sql
SELECT *
FROM user_details
WHERE user_id = ?
  AND is_active = 1
  AND ended_at IS NULL
ORDER BY started_at DESC
LIMIT 1;
```

### 3. Graph RAG: 벡터 유사도 검색

```sql
SELECT
  paper_id,
  title,
  chunk_text,
  1 - (embedding_ko_openai <=> ?::vector) AS similarity
FROM paper_nodes
WHERE lang = 'ko' OR chunk_ko_summary IS NOT NULL
ORDER BY embedding_ko_openai <=> ?::vector
LIMIT 10;
```

### 4. Graph RAG: 개념 기반 논문 검색

```sql
SELECT DISTINCT
  pn.paper_id,
  pn.title,
  pcr.relation_type,
  pcr.confidence
FROM paper_nodes pn
INNER JOIN paper_concept_relations pcr ON pn.id = pcr.paper_id
WHERE pcr.concept_id IN (?, ?, ?)
  AND pcr.confidence > 0.7
ORDER BY pcr.confidence DESC
LIMIT 10;
```

### 5. 하이브리드 검색 (Vector + Graph)

```sql
WITH vector_results AS (
  SELECT
    id,
    paper_id,
    1 - (embedding_ko_openai <=> ?::vector) AS vector_score
  FROM paper_nodes
  ORDER BY embedding_ko_openai <=> ?::vector
  LIMIT 20
),
graph_results AS (
  SELECT DISTINCT
    pn.id,
    pn.paper_id,
    AVG(pcr.confidence) AS graph_score
  FROM paper_nodes pn
  INNER JOIN paper_concept_relations pcr ON pn.id = pcr.paper_id
  WHERE pcr.concept_id IN (?, ?, ?)
  GROUP BY pn.id, pn.paper_id
  ORDER BY AVG(pcr.confidence) DESC
  LIMIT 20
)
SELECT
  pn.*,
  COALESCE(vr.vector_score, 0) * 0.7 + COALESCE(gr.graph_score, 0) * 0.3 AS final_score
FROM paper_nodes pn
LEFT JOIN vector_results vr ON pn.id = vr.id
LEFT JOIN graph_results gr ON pn.id = gr.id
WHERE vr.id IS NOT NULL OR gr.id IS NOT NULL
ORDER BY final_score DESC
LIMIT 10;
```

---

## 🛠️ 특수 데이터 타입

### JSONB (PostgreSQL)
- `health_records.measurements`
- `weekly_plans.plan_data`
- `paper_nodes.authors`
- `paper_nodes.keywords`

**장점:**
- 유연한 스키마
- JSON 쿼리 지원 (`->`, `->>`, `@>`)
- 인덱싱 가능 (GIN 인덱스)

### VECTOR (pgvector)
- `inbody_analysis_reports.embedding_1536`
- `inbody_analysis_reports.embedding_1024`
- `paper_nodes.embedding_openai`
- `paper_nodes.embedding_ollama`
- `paper_nodes.embedding_ko_openai`

**사용:**
```sql
-- 코사인 유사도 검색
SELECT * FROM paper_nodes
ORDER BY embedding_ko_openai <=> '[0.1, 0.2, ...]'::vector
LIMIT 10;

-- L2 거리
SELECT * FROM paper_nodes
ORDER BY embedding_ko_openai <-> '[0.1, 0.2, ...]'::vector
LIMIT 10;
```

---

## 📝 마이그레이션 히스토리

### v1.0 (2026-01-29)
- 초기 스키마 생성
- users, health_records, analysis_reports

### v1.1 (2026-01-30)
- user_goals → user_details 이름 변경
- weekly_plans 테이블 추가
- analysis_reports → inbody_analysis_reports 이름 변경

### v1.2 (2026-02-01)
- paper_nodes 테이블 추가 (Graph RAG)
- paper_concept_relations 테이블 추가
- pgvector 확장 설치

### v1.3 (2026-02-02)
- embedding_ko_openai 컬럼 추가
- chunk_ko_summary 컬럼 추가

---

## 🔧 데이터베이스 생성

### PostgreSQL 설정

```sql
-- 데이터베이스 생성
CREATE DATABASE explainmybody;

-- pgvector 확장 설치
CREATE EXTENSION IF NOT EXISTS vector;

-- 테이블 생성 (SQLAlchemy로 자동 생성됨)
-- python -c "from backend.database import engine; from backend.models import *; Base.metadata.create_all(engine)"
```

### 샘플 데이터 삽입

```sql
-- 테스트 사용자
INSERT INTO users (username, email, password_hash)
VALUES ('testuser', 'test@example.com', 'hashed_password');

-- 건강 기록
INSERT INTO health_records (user_id, source, measurements)
VALUES (1, 'manual', '{"기본정보": {"키": 175.0, "체중": 70.0}}');
```

---

## 📚 참고 자료

- **dbdiagram.io:** https://dbdiagram.io/
- **DBML 문법:** https://dbml.dbdiagram.io/docs/
- **PostgreSQL JSONB:** https://www.postgresql.org/docs/current/datatype-json.html
- **pgvector:** https://github.com/pgvector/pgvector

---

**작성일:** 2026-02-02
**작성자:** Claude Code
