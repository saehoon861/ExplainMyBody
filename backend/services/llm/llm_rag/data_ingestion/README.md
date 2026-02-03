# RAG 데이터 입력 스크립트

JSON 및 Cypher 형식의 논문 데이터를 PostgreSQL에 입력하는 스크립트

## 📁 파일 구조

```
backend/scripts/rag_data_ingestion/
├── __init__.py
├── README.md              # 이 파일
├── ingest_json.py         # JSON → PostgreSQL
└── ingest_cypher.py       # Cypher → PostgreSQL
```

## 🚀 사용 방법

### 1. JSON 데이터 입력

```bash
cd /home/user/projects/ExplainMyBody/backend

python scripts/rag_data_ingestion/ingest_json.py \
  /home/user/projects/ExplainMyBody/src/llm/ragdb_collect/outputs/graph_rag_50papers_20260202_154557.json
```

**옵션:**
- `--batch-size N`: 배치 삽입 크기 (기본: 100)
- `--no-skip-existing`: 이미 존재하는 데이터도 다시 삽입
- `--db-url URL`: PostgreSQL 연결 URL (기본: 환경변수 DATABASE_URL)

**예시:**
```bash
# 대용량 파일 (2577 papers)
python scripts/rag_data_ingestion/ingest_json.py \
  /home/user/projects/ExplainMyBody/src/llm/ragdb_collect/outputs/ragdb_final_corpus_20260129_195141.json \
  --batch-size 200

# 기존 데이터 덮어쓰기
python scripts/rag_data_ingestion/ingest_json.py \
  /path/to/data.json \
  --no-skip-existing
```

### 2. Cypher 데이터 입력

```bash
cd /home/user/projects/ExplainMyBody/backend

python scripts/rag_data_ingestion/ingest_cypher.py \
  /home/user/projects/ExplainMyBody/src/llm/ragdb_collect/outputs/graph_rag_neo4j_2577papers_20260202_171718.cypher
```

**옵션:**
- `--no-skip-existing`: 이미 존재하는 데이터도 다시 삽입
- `--db-url URL`: PostgreSQL 연결 URL

**주의:** Cypher 파일은 제목만 삽입합니다. 전체 데이터는 JSON을 사용하세요.

## 📊 데이터 형식

### JSON 형식

```json
{
  "nodes": [
    {
      "node_type": "paper",
      "id": "paper_41415307",
      "title": "...",
      "chunk_text": "...",
      "chunk_ko_summary": "...",
      "lang": "en",
      "source": "pubmed",
      "year": 2024,
      "pmid": "41415307",
      "doi": "...",
      "embedding_ko": [0.01, 0.02, ...],  // 1024D or 1536D
      "embedding_en": [0.01, 0.02, ...]
    }
  ],
  "links": [...]
}
```

**처리:**
- `embedding_ko` → `embedding_ko_openai` (PostgreSQL vector 컬럼)
- `embedding_en` → `embedding_en_openai`
- paper 노드만 추출 (`node_type: "paper"`)

### Cypher 형식

```cypher
CREATE (ppaper_41415307:Paper {id: 'paper_41415307', title: '...'});
CREATE (cprotein_intake:Concept:Intervention {id: 'protein_intake', name_ko: '단백질 섭취', ...});
CREATE (ppaper_41415307)-[:MENTIONS {confidence: 0.9}]->(cprotein_intake);
```

**처리:**
- Paper 노드: `paper_nodes` 테이블에 제목만 삽입
- Concept 노드: 현재 스킵 (개념 테이블 미사용)
- 관계: 별도 처리 필요

## 💾 PostgreSQL 테이블

### paper_nodes

```sql
CREATE TABLE paper_nodes (
    id SERIAL PRIMARY KEY,
    paper_id VARCHAR(50) UNIQUE NOT NULL,
    title TEXT,
    chunk_text TEXT,
    chunk_ko_summary TEXT,
    lang VARCHAR(10),
    source VARCHAR(50),
    year INTEGER,
    pmid VARCHAR(50),
    doi VARCHAR(100),
    embedding_ko_openai vector(1536),  -- OpenAI text-embedding-3-small
    embedding_en_openai vector(1536),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

## 🔧 커스터마이징

### 다른 embedding 모델 사용

`ingest_json.py` 수정:

```python
# embedding 차원 변경 (예: 1024D)
embedding_ko_openai vector(1024)
```

### 배치 크기 조정

```bash
# 작은 메모리 환경
python ingest_json.py data.json --batch-size 50

# 대용량 처리
python ingest_json.py data.json --batch-size 500
```

### 데이터 전처리 추가

`parse_paper_nodes()` 메서드 수정:

```python
def parse_paper_nodes(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
    paper_nodes = []
    for node in data.get('nodes', []):
        if node.get('node_type') == 'paper':
            # 커스텀 전처리
            title = node.get('title', '').strip()
            if not title:
                continue  # 제목 없는 논문 스킵

            # ... 나머지 로직
```

## ⚠️ 주의사항

1. **환경변수 필수**: `.env`에 `DATABASE_URL` 설정
2. **pgvector 확장 필요**: PostgreSQL에 `pgvector` 설치
3. **중복 방지**: 기본적으로 `paper_id`가 중복되면 스킵
4. **Embedding 차원**: JSON 데이터의 embedding 차원 확인 필요
5. **메모리 사용**: 대용량 파일은 배치 크기 조정

## 📝 문제 해결

### DB 연결 실패

```
ValueError: DATABASE_URL 환경변수가 설정되지 않았습니다.
```

→ `.env` 파일에 `DATABASE_URL` 설정

### pgvector 에러

```
ERROR: type "vector" does not exist
```

→ PostgreSQL에 pgvector 확장 설치:
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

### Embedding 차원 불일치

```
ERROR: expected 1536 dimensions, not 1024
```

→ JSON 데이터의 embedding 차원 확인:
```python
len(node['embedding_ko'])  # 1024 or 1536?
```

테이블 스키마 수정:
```sql
ALTER TABLE paper_nodes
ALTER COLUMN embedding_ko_openai TYPE vector(1024);
```

### 메모리 부족

```
MemoryError: ...
```

→ 배치 크기 감소:
```bash
python ingest_json.py data.json --batch-size 20
```

## 🎯 사용 시나리오

### 초기 데이터 로딩

```bash
# 1. 전체 논문 DB 로딩 (2577개)
python ingest_json.py \
  src/llm/ragdb_collect/outputs/ragdb_final_corpus_20260129_195141.json

# 2. 확인
psql -d dbname -c "SELECT COUNT(*) FROM paper_nodes;"
```

### 증분 업데이트

```bash
# 새로운 논문 추가 (중복 자동 스킵)
python ingest_json.py \
  new_papers_20260203.json
```

### 데이터 재로딩

```bash
# 기존 데이터 삭제
psql -d dbname -c "TRUNCATE paper_nodes CASCADE;"

# 재로딩
python ingest_json.py data.json --no-skip-existing
```

---

**개발자**: SK
**최종 수정**: 2026-02-03
