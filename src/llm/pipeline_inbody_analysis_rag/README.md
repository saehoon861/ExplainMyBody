# InBody Analysis Pipeline with Graph RAG

InBody 측정 데이터를 분석하고 Graph RAG를 통해 관련 과학 논문을 검색하여 근거 기반 분석을 제공하는 파이프라인입니다.

## 주요 특징

- **Graph RAG 통합**: 사용자의 체성분 상태에 맞는 과학 논문 자동 검색
- **Hybrid Search**: Vector 유사도 검색 + Neo4j 그래프 탐색
- **고정 모델**: 항상 `gpt-4o-mini` 및 `text-embedding-3-small` 사용
- **근거 기반 분석**: 최신 연구 논문 기반으로 현재 체형 상태 분석

## 파일 구조

```
pipeline_inbody_analysis_rag/
├── __init__.py
├── analyzer.py              # Graph RAG 적용 InBody 분석기
├── prompt_generator.py      # 프롬프트 생성 (논문 컨텍스트 포함)
├── embedder.py              # 임베딩 생성 (원본과 동일)
├── main.py                  # 실행 파일
├── sample_inbody_data.json  # 샘플 데이터
└── README.md                # 이 파일
```

## 설치 및 준비

### 1. 데이터베이스 준비
- PostgreSQL (InBody 데이터 저장, Vector 검색)
- Neo4j (Graph RAG, 선택적)

### 2. Graph RAG 데이터 Import
```bash
# PostgreSQL + Neo4j에 논문 데이터 import
python backend/utils/scripts/import_graph_rag.py \
  --json-file src/llm/ragdb_collect/outputs/graph_rag_2577papers_*.json \
  --neo4j
```

## 사용법

### 기본 실행

```bash
python src/llm/pipeline_inbody_analysis_rag/main.py \
  --user-id 1 \
  --measurements-file src/llm/pipeline_inbody_analysis_rag/sample_inbody_data.json
```

### 옵션

```bash
python src/llm/pipeline_inbody_analysis_rag/main.py \
  --user-id 1 \
  --measurements-file sample_inbody_data.json \
  --output-file output.txt \
  --enable-embedding \
  --no-neo4j  # Neo4j 없이 Vector 검색만 사용
```

### 파라미터

- `--user-id`: 사용자 ID (필수)
- `--measurements-file`: InBody 측정 데이터 JSON 파일 (필수)
- `--measurements-json`: 또는 JSON 문자열로 직접 전달
- `--output-file`: 결과 저장 파일 경로
- `--db-url`: 데이터베이스 URL (기본: 환경변수)
- `--source`: 데이터 소스 (기본: "manual")
- `--enable-embedding`: 임베딩 생성 활성화
- `--no-neo4j`: Neo4j 그래프 탐색 비활성화 (Vector만 사용)

## 작동 방식

### 1단계: 체형 정보 확인
- Body Type 1/2 확인
- 기본 측정 데이터 검증

### 2단계: Graph RAG 논문 검색
- InBody 데이터에서 핵심 개념 추출:
  - 체지방률 → `fat_loss`, `body_fat_percentage`
  - 근육조절 → `muscle_hypertrophy`, `resistance_training`, `protein_intake`
  - 내장지방 → `visceral_fat`, `metabolic_health`
  - BMI → `overweight`, `weight_loss`, `caloric_deficit`
- Vector 검색 (PostgreSQL pgvector)
- Graph 탐색 (Neo4j, 선택적)
- Hybrid Reranking

### 3단계: 측정 데이터 저장
- PostgreSQL `health_records` 테이블에 저장
- Record ID 반환

### 4단계: 프롬프트 생성
- InBody 측정 데이터 포맷팅
- Graph RAG 논문 컨텍스트 추가

### 5단계: LLM 분석
- gpt-4o-mini로 분석 생성
- 논문 기반 근거 포함

### 6단계: 분석 결과 저장
- PostgreSQL `inbody_analysis_reports` 테이블에 저장
- Analysis ID 반환

### (선택적) 임베딩 생성
- OpenAI text-embedding-3-small (1536D)
- Ollama bge-m3 (1024D, 선택적)

## 출력 형식

분석 결과는 다음 섹션을 포함합니다:

1. **종합 체형 평가**: 체형 유형 및 주요 특징
2. **체성분 상세 분석**: 체지방, 근육량, 영양 상태
3. **부위별 불균형 분석**: 근육 발달, 체지방 분포, 좌우 대칭성
4. **대사 및 건강 지표**: 기초대사량, 체중 조절 목표, 건강 리스크
5. **체형 분류 해석**: Body Type 1/2 결과 (있는 경우)
6. **과학적 근거 분석**: 관련 연구 논문 기반 분석 (Graph RAG)
7. **우선순위 개선 과제**: 최우선/차순위/장기 과제
8. **분석 요약**: 강점과 약점 요약

## 원본 파이프라인과의 차이점

| 항목 | 원본 (`pipeline_inbody_analysis`) | Graph RAG (`pipeline_inbody_analysis_rag`) |
|------|----------------------------------|-------------------------------------------|
| 모델 | 사용자 선택 가능 | 항상 `gpt-4o-mini` |
| Embedding | 사용자 선택 가능 | 항상 `text-embedding-3-small` |
| 논문 검색 | ❌ 없음 | ✅ Graph RAG (Vector + Graph) |
| Database | 필수 | 필수 |
| Neo4j | 불필요 | 선택적 (권장) |
| 분석 섹션 | 6개 | 8개 (과학적 근거 추가) |

## 예제

### 입력 (sample_inbody_data.json)
```json
{
  "성별": "남성",
  "나이": 28,
  "신장": 175,
  "체중": 75,
  "BMI": 24.5,
  "체지방률": 22,
  "골격근량": 32.5,
  "근육조절": 2.5,
  "지방조절": -3.0,
  ...
}
```

### 출력
```
=============================================================
InBody 분석 시작 (User ID: 1, Graph RAG)
  🔧 모델: gpt-4o-mini
  🔧 Graph RAG: ✅ Enabled
=============================================================

📊 1단계: 체형 정보 확인...
  ✓ Body Type 1: C형
  ✓ Body Type 2: I형

🔍 2단계: Graph RAG 논문 검색...
  🔎 Vector 유사도 검색...
  🔷 Graph 탐색...
  ✓ 5개 관련 논문 검색 완료

💾 3단계: 측정 데이터 저장...
  ✓ Record ID: 123

📝 4단계: 프롬프트 생성...

🤖 5단계: LLM 분석 생성 (gpt-4o-mini)...
  ✓ 분석 완료 (2,345 글자)

💾 6단계: 분석 결과 저장...
  ✓ Analysis ID: 456

✨ InBody 분석 완료!
```

## 주의사항

1. **Database 필수**: 원본 파이프라인과 달리 Graph RAG는 실제 DB 저장이 필요합니다
2. **모델 고정**: 비용 최적화를 위해 gpt-4o-mini로 고정되어 있습니다
3. **Neo4j 선택적**: Neo4j 없이도 Vector 검색만으로 작동 가능합니다
4. **논문 품질**: Graph RAG 검색 결과는 import한 논문 데이터에 의존합니다

## 문제 해결

### Graph RAG 검색 실패
```
⚠️ Graph RAG 초기화 실패
```
→ PostgreSQL 또는 Neo4j 연결 확인, import 스크립트 실행 확인

### 관련 논문이 없음
```
⚠️ 관련 논문이 없습니다
```
→ 정상 (해당 체형 상태에 맞는 논문이 DB에 없을 수 있음)

### 임베딩 생성 실패
```
⚠️ OpenAI 임베딩 생성 실패
```
→ API 키 확인, 환경변수 설정 확인

## 관련 문서

- [Graph RAG Integration Guide](../pipeline_weekly_plan_rag/GRAPH_RAG_INTEGRATION.md)
- [Original InBody Analysis](../pipeline_inbody_analysis/README.md)
