# SQLAlchemy + pgvector 마이그레이션 완료

**날짜**: 2026-01-26
**상태**: ✅ 완료

---

## 🎉 변경사항 요약

### 1. SQLAlchemy 전환
- **기존**: psycopg2 직접 사용
- **변경**: SQLAlchemy ORM 사용
- **장점**:
  - 타입 안정성 향상
  - 관계(relationship) 자동 관리
  - 더 나은 쿼리 빌더
  - Alembic을 통한 마이그레이션 지원

### 2. pgvector 활성화
- **Vector 타입**: `vector(1536)` - OpenAI text-embedding-3-small 차원
- **Vector 인덱스**: HNSW 인덱스로 빠른 유사도 검색
- **임베딩 저장**: analysis_reports 테이블에 embedding 컬럼 추가
- **Vector RAG**: 실제 유사도 기반 검색 구현

### 3. 새로운 파일 구조
```
llm/shared/
├── database.py              # SQLAlchemy 기반 (기존 psycopg2 버전은 database_psycopg2_backup.py)
├── db_models.py             # SQLAlchemy ORM 모델 정의 (신규)
├── llm_clients.py           # 기존 그대로
└── models.py                # Pydantic 모델 (기존 그대로)

llm/
└── migrate_to_sqlalchemy.py # 마이그레이션 스크립트 (신규)
```

---

## 📊 데이터베이스 스키마 변경

### 변경된 테이블 구조

#### users (변경 없음)
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### health_records
- **변경**: `measured_at` → `record_date`
```sql
CREATE TABLE health_records (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    record_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- 변경
    source VARCHAR(100) DEFAULT 'manual',
    measurements JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### analysis_reports
- **변경**: `generated_at` → `report_date`
- **추가**: `embedding vector(1536), (1024)`
```sql
CREATE TABLE analysis_reports (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    record_id INTEGER REFERENCES health_records(id) ON DELETE CASCADE,
    llm_output TEXT NOT NULL,
    model_version VARCHAR(100),
    report_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- 변경
    embedding_1536 vector(1536),
    embedding_1024 vector(1024)  -- 추가: pgvector
);

-- HNSW 인덱스 (빠른 vector 검색)
CREATE INDEX idx_analysis_reports_embedding_hnsw
ON analysis_reports USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);
```

#### user_goals
- **추가**: `goal_data JSONB`, `is_active INTEGER`
```sql
CREATE TABLE user_goals (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    goal_type VARCHAR(255),
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP,
    goal_data JSONB,      -- 추가
    is_active INTEGER DEFAULT 1,  -- 추가
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### weekly_plans (신규)
```sql
CREATE TABLE weekly_plans (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    week_number INTEGER NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    plan_data JSONB NOT NULL,
    model_version VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 🔧 주요 기능 변경

### 1. Database 클래스 (shared/database.py)

#### 새로운 메서드
```python
# Vector 유사도 검색 (pgvector)
def search_similar_analyses(
    user_id: int,
    query_embedding: List[float],
    top_k: int = 3
) -> List[Dict]:
    """Cosine similarity 기반 vector 검색"""

# 임베딩 업데이트
def update_analysis_embedding(
    report_id: int,
    embedding: List[float]
) -> bool:
    """분석 리포트에 임베딩 추가/업데이트"""

# Weekly Plan 저장
def save_weekly_plan(
    user_id: int,
    week_number: int,
    start_date: date,
    end_date: date,
    plan_data: Dict[str, Any],
    model_version: str,
) -> int:
    """주간 계획 DB 저장"""

# Weekly Plan 조회
def get_weekly_plan(plan_id: int) -> Optional[Dict]:
def get_user_weekly_plans(user_id: int, limit: int = 10) -> List[Dict]:
```

### 2. InBody Embedder (pipeline_inbody_analysis/embedder.py)
- **변경**: 실제로 DB에 임베딩 저장
- **사용**: `db.update_analysis_embedding()`로 embedding 컬럼 업데이트

### 3. RAG Retriever (pipeline_weekly_plan/rag_retriever.py)
- **변경**: pgvector 기반 실제 유사도 검색
- **동작**:
  1. 자연어 쿼리 → OpenAI embedding
  2. pgvector cosine similarity 검색
  3. 가장 유사한 top_k 분석 반환
- **Fallback**: 임베딩 없을 경우 최신 분석 반환

### 4. Weekly Planner (pipeline_weekly_plan/planner.py)
- **변경**: 실제 DB에 weekly_plans 저장
- **사용**: `db.save_weekly_plan()`

---

## 🚀 설정 방법

### 1. 패키지 설치
```bash
cd /home/user/projects/ExplainMyBody
uv sync
```

### 2. 환경변수 설정 (.env)
```bash
# Database
DATABASE_URL=postgresql://sgkim:1234@localhost:5433/explainmybody

# LLM API Keys (최소 하나 필요)
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...        # 임베딩 생성을 위해 필요

# Ollama (선택적)
OLLAMA_HOST=http://localhost:11434
```

**중요**: 임베딩 기능을 사용하려면 **OPENAI_API_KEY 필수**

### 3. 마이그레이션 실행 (기존 DB가 있는 경우)
```bash
cd /home/user/projects/ExplainMyBody/llm

# 옵션 1 선택 (기존 데이터 유지하고 컬럼 추가)
python migrate_to_sqlalchemy.py
```

---

## 📝 사용 예시

### InBody 분석 (임베딩 포함)
```bash
uv run python pipeline_inbody_analysis/main.py \
  --user-id 1 \
  --measurements-file sample_inbody_data.json \
  --model gpt-4o-mini \
  --enable-embedding \
  --output-file result.json
```

### 주간 계획 생성 (Vector RAG 사용)
```bash
uv run python pipeline_weekly_plan/main.py \
  --user-id 1 \
  --goals-file sample_user_goals.json \
  --preferences-file sample_user_preferences.json \
  --week-number 1
```

**Vector RAG 동작**:
1. 사용자의 InBody 분석 중 임베딩된 것들 검색
2. "체형 분석" 쿼리와 유사도 계산 (cosine similarity)
3. 가장 유사한 top 3 분석을 컨텍스트로 사용
4. LLM이 이를 기반으로 맞춤형 주간 계획 생성

---

## 🔍 테스트

### 1. Database 연결 테스트
```python
from shared.database import Database

db = Database()
print(db.test_connection())  # True
```

### 2. Vector 검색 테스트
```python
from shared.database import Database
from shared.llm_clients import OpenAIClient

db = Database()
openai = OpenAIClient()

# 쿼리 임베딩 생성
query = "상체 근육량이 부족하고 체지방률이 높은 경우"
query_embedding = openai.create_embedding(query)

# 유사한 분석 검색
results = db.search_similar_analyses(
    user_id=1,
    query_embedding=query_embedding,
    top_k=3
)

for r in results:
    print(f"ID: {r['id']}, Similarity: {r['similarity']:.3f}")
```

### 3. Weekly Plan DB 저장 테스트
```python
from shared.database import Database
from datetime import date

db = Database()

plan_id = db.save_weekly_plan(
    user_id=1,
    week_number=1,
    start_date=date(2026, 2, 3),
    end_date=date(2026, 2, 9),
    plan_data={"weekly_summary": "테스트 계획"},
    model_version="gpt-4o-mini"
)

print(f"Plan ID: {plan_id}")
```

---

## 📦 설치된 패키지

### 새로 추가된 패키지
- `pgvector>=0.2.0` - pgvector Python 클라이언트

### 기존 패키지
- `sqlalchemy>=2.0.0` - ORM
- `alembic>=1.13.0` - 마이그레이션 도구 (향후 사용)
- `psycopg2-binary>=2.9.9` - PostgreSQL 드라이버

---

## 🎯 성능 향상

### Vector 검색 성능
- **인덱스**: HNSW (Hierarchical Navigable Small World)
- **검색 속도**: O(log N) - 선형 검색 대비 매우 빠름
- **파라미터**:
  - `m = 16`: 그래프 연결 수
  - `ef_construction = 64`: 인덱스 구축 정확도

### Cosine Similarity
- **범위**: 0.0 ~ 1.0
- **의미**: 1.0에 가까울수록 유사함
- **계산**: `1 - cosine_distance`

---

## 🐛 트러블슈팅

### 1. pgvector extension 없음
```sql
-- Docker 컨테이너에 접속
docker exec -it explainmybody-postgres psql -U sgkim -d explainmybody

-- extension 설치
CREATE EXTENSION vector;
```

### 2. 컬럼명 불일치 오류
```bash
# 마이그레이션 스크립트 재실행
python migrate_to_sqlalchemy.py
# 옵션 1 선택
```

### 3. Vector 인덱스 생성 실패
- **원인**: embedding 데이터가 아직 없음
- **해결**: 임베딩 생성 후 자동으로 인덱스 사용 시작

### 4. OpenAI API Key 오류
- **확인**: `.env` 파일에 `OPENAI_API_KEY` 설정 확인
- **주의**: 주석(`#`) 제거 필요

---

## 📚 관련 문서

- [PIPELINE_GUIDE.md](PIPELINE_GUIDE.md) - 파이프라인 사용법
- [POSTGRESQL_SETUP.md](POSTGRESQL_SETUP.md) - PostgreSQL 설정
- [TEST_RESULTS.md](TEST_RESULTS.md) - 테스트 결과

---

## ✅ 체크리스트

- [x] pgvector extension 활성화
- [x] SQLAlchemy ORM 모델 정의
- [x] Database 클래스 SQLAlchemy로 전환
- [x] embedding 컬럼 추가 (vector(1536))
- [x] HNSW 인덱스 생성
- [x] Vector 유사도 검색 구현
- [x] InBody embedder 실제 저장 구현
- [x] RAG retriever pgvector 검색 구현
- [x] Weekly planner DB 저장 구현
- [x] 마이그레이션 스크립트 작성
- [x] 문서 작성

---

## 🔜 향후 작업

1. **Alembic 마이그레이션 설정**
   - 자동 마이그레이션 스크립트 생성
   - 버전 관리

2. **임베딩 배치 처리**
   - 기존 분석 리포트 일괄 임베딩
   - 스케줄러 설정

3. **Vector 검색 최적화**
   - 인덱스 파라미터 튜닝
   - 검색 성능 벤치마크

4. **FastAPI 엔드포인트**
   - RESTful API 구현
   - Swagger 문서

---

**마이그레이션 완료일**: 2026-01-26
**버전**: v2.0 (SQLAlchemy + pgvector)
