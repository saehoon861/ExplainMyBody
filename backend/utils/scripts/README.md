# Backend Scripts

## import_graph_rag.py

Graph RAG 데이터를 PostgreSQL (pgvector) 및 Neo4j에 로드하는 스크립트입니다.

### 사용법

```bash
# 기본 사용 (PostgreSQL만, 최신 JSON 파일 자동 탐색)
python backend/utils/scripts/import_graph_rag.py

# 특정 JSON 파일 지정
python backend/utils/scripts/import_graph_rag.py --json-path src/llm/ragdb_collect/outputs/graph_rag_2577papers_20260130_130411.json

# Neo4j에도 데이터 로드
python backend/utils/scripts/import_graph_rag.py --neo4j

# 기존 데이터 삭제 후 재로드
python backend/utils/scripts/import_graph_rag.py --clear

# 모든 옵션 사용
python backend/utils/scripts/import_graph_rag.py --json-path <PATH> --neo4j --clear
```

### 옵션

- `--json-path PATH`: graph_rag JSON 파일 경로 (기본: 최신 파일 자동 탐색)
- `--neo4j`: Neo4j에도 데이터 로드 (기본: PostgreSQL만)
- `--clear`: 기존 데이터 삭제 후 재로드

### 처리 과정

1. **JSON 로드**: `src/llm/ragdb_collect/outputs/` 에서 최신 `graph_rag_*papers_*.json` 파일 로드
2. **pgvector Extension**: PostgreSQL에 pgvector extension 활성화
3. **테이블 생성**: `paper_nodes`, `paper_concept_relations` 테이블 생성
4. **논문 삽입**: 2,100+ 논문을 `paper_nodes` 테이블에 bulk insert
   - 임베딩: `embedding_ko` → `embedding_ko_openai` (1536D)
   - 메타데이터: title, chunk_text, lang, domain, source, year, pmid, doi
5. **관계 삽입**: 9,000+ 관계를 `paper_concept_relations` 테이블에 bulk insert
   - 관계 타입: MENTIONS, INCREASES, SUPPORTS, REDUCES 등
   - 메타데이터: confidence, matched_term, count
6. **Neo4j 로드** (선택적): Paper, Concept 노드 및 관계 그래프 생성

### 요구사항

- PostgreSQL with pgvector extension
- Neo4j (선택적, `--neo4j` 사용 시)
- 환경변수 설정:
  - `DATABASE_URL`: PostgreSQL 연결 URL
  - `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`: Neo4j 연결 정보

### 예상 결과

```
===========================================================
  Graph RAG Data Import Script
===========================================================

📂 JSON 파일 로드 중: src/llm/ragdb_collect/outputs/graph_rag_2577papers_20260130_130411.json
  ✓ Nodes: 2,149개
  ✓ Edges: 9,176개

🔧 pgvector extension 확인 중...
  ✓ pgvector extension 활성화 완료

🔧 테이블 생성 중...
  ✓ 테이블 생성 완료 (paper_nodes, paper_concept_relations)

📥 PostgreSQL에 2,149개 논문 삽입 중...
  ✓ 진행: 500/2,149 (23.3%)
  ✓ 진행: 1,000/2,149 (46.5%)
  ...
  ✅ 논문 삽입 완료: 2,149개 성공, 0개 스킵

📥 PostgreSQL에 9,176개 관계 삽입 중...
  ✓ 진행: 1,000/9,176 (10.9%)
  ...
  ✅ 관계 삽입 완료: 9,176개 성공, 0개 스킵

===========================================================
  ✅ Graph RAG 데이터 Import 완료!
===========================================================

📊 요약:
  - 총 논문: 2,149개
  - 총 관계: 9,176개
  - PostgreSQL: paper_nodes, paper_concept_relations 테이블
```
