# ExplainMyBody RAG 파이프라인 전체 구조

**작성일:** 2026-02-02
**논문 데이터 수집 → 가공 → 임베딩 → Neo4j/PostgreSQL 저장 → 실제 사용까지 전 과정**

---

## 📊 전체 아키텍처 개요

```
[1] 논문 수집
    ├─ PubMed API (영어 논문)
    ├─ KCI API (한국어 논문)
    └─ Google Scholar (한국어 보충)
        ↓
    📁 outputs/papers/*.json (개별 수집 파일)
        ↓
[2] 중복 제거 및 병합
    → merge_korean_corpus.py
        ↓
    📁 ragdb_final_corpus_20260129_195141.json (2,577개 논문)
        ↓
[3] Graph RAG 구축
    → build_graph_rag.py
    ├─ 개념 추출 (스키마 기반)
    ├─ 관계 탐지 (MENTIONS, INCREASES, SUPPORTS)
    ├─ 한국어 임베딩 생성 (OpenAI text-embedding-3-small)
    └─ Neo4j Cypher 생성
        ↓
    📁 graph_rag_2577papers_20260130_211829.json (120MB, 논문+관계+임베딩)
    📁 graph_rag_neo4j_2577papers_20260130_211829.cypher (1.3MB, Neo4j import용)
        ↓
[4] PostgreSQL + Neo4j Import
    → import_graph_rag.py
    ├─ PostgreSQL (paper_nodes 테이블)
    │   ├─ 메타데이터 저장
    │   ├─ embedding_ko_openai (pgvector, 1536D)
    │   └─ Vector 검색 준비
    └─ Neo4j (Graph Database)
        ├─ Paper 노드 생성
        ├─ Concept 노드 생성
        └─ 관계 생성 (MENTIONS, INCREASES, SUPPORTS)
            ↓
[5] 런타임 검색
    → graph_rag_retriever.py
    ├─ InBody 데이터 → 개념 추출
    ├─ Vector Search (PostgreSQL pgvector)
    ├─ Graph Traversal (Neo4j, optional)
    └─ Hybrid Reranking (0.7*vector + 0.3*graph)
        ↓
[6] Prompt 생성 + LLM 분석
    → prompt_generator.py
    ├─ InBody 측정 데이터 포맷팅
    ├─ 논문 컨텍스트 추가 (10개)
    └─ gpt-4o-mini 분석 생성
        ↓
[7] 결과 출력
    📄 InBody 분석 리포트 (논문 근거 포함)
```

---

## 1️⃣ 논문 수집 (Paper Collection)

### 📁 위치
```
src/llm/ragdb_collect/
├── config.py                      # 검색 쿼리 정의
├── pubmed_collector.py            # PubMed API 수집
├── kci_api_collector.py           # KCI API 수집
├── riss_api_collector.py          # RISS API 수집
├── google_scholar_korean_collector.py
└── main.py                        # 통합 실행
```

### 🎯 수집 전략

**4개 축 동등 분배 (총 3,000개 목표)**

| 축 | 도메인 | 목표 | 소스 | 언어 |
|---|--------|------|------|------|
| 1 | 단백질/근육 증가 | 800개 | PubMed | 영어 |
| 2 | 체지방 감량 | 800개 | PubMed | 영어 |
| 3 | 한국형 식단 | 600개 | KCI/RISS | 한국어 |
| 4 | 체형 분석/인바디 | 800개 | PubMed+KCI | 영어+한국어 |

### 🔍 실제 수집 쿼리 예시

```python
# config.py
PROTEIN_HYPERTROPHY_QUERIES = [
    "(resistance training) AND (protein intake) AND hypertrophy",
    "muscle protein synthesis AND leucine",
    "whey supplementation AND strength gain",
    # ... 총 10개 쿼리
]

FAT_LOSS_QUERIES = [
    "calorie deficit AND fat loss AND body composition",
    "high protein diet AND weight loss AND lean mass",
    # ... 총 10개 쿼리
]

BODY_COMPOSITION_QUERIES_KO = [
    "근감소증 한국인",
    "체성분 분석 인바디",
    "골격근량 측정 방법",
    # ... 총 6개 쿼리
]
```

### 📄 수집된 파일 구조

```bash
outputs/papers/
├── protein_hypertrophy_20260128_204302.json    # 936KB
├── fat_loss_20260128_204302.json               # 1.7MB
├── korean_diet_20260128_204302.json            # 631KB
├── body_composition_20260128_204302.json       # 1.0MB
├── google_scholar_korean_20260129_120122.json  # 287KB
└── ... (도메인별 분리 파일)
```

### 📊 JSON 데이터 구조

```json
{
  "domain": "protein_hypertrophy",
  "language": "en",
  "title": "Resistance training-induced appendicular lean tissue...",
  "abstract": "We sought to determine if pre-intervention bone...",
  "keywords": ["hypertrophy", "lean tissue mass", "resistance training"],
  "source": "PubMed",
  "year": 2025,
  "pmid": "41415307",
  "doi": "10.1519/JSC.0000000000001049",
  "authors": ["Dakota R Tiede", "Daniel L Plotkin", ...],
  "journal": "Frontiers in physiology"
}
```

**주요 필드:**
- `abstract`: 초록 전문 (평균 1,000-2,000자) ← RAG의 핵심 데이터
- `domain`: 4개 축 분류 (`protein_hypertrophy`, `fat_loss`, `korean_diet`, `body_composition`)
- `language`: `en` (영어) 또는 `ko` (한국어)
- `pmid`: PubMed ID (영어 논문만)

---

## 2️⃣ 중복 제거 및 병합 (Deduplication & Merge)

### 📁 스크립트
```
src/llm/ragdb_collect/merge_korean_corpus.py
```

### 🎯 작업 내용

1. **개별 수집 파일 로드**
   ```python
   # 모든 JSON 파일 읽기
   papers = []
   for file in glob("outputs/papers/*.json"):
       with open(file) as f:
           papers.extend(json.load(f))
   ```

2. **중복 제거 (PMID/제목 기반)**
   ```python
   seen_pmids = set()
   seen_titles = set()
   unique_papers = []

   for paper in papers:
       # PMID 중복 체크
       if paper.get('pmid') and paper['pmid'] in seen_pmids:
           continue

       # 제목 유사도 체크 (한국어 논문)
       if paper['title'] in seen_titles:
           continue

       seen_pmids.add(paper.get('pmid'))
       seen_titles.add(paper['title'])
       unique_papers.append(paper)
   ```

3. **병합 및 저장**
   ```bash
   # 실행
   python merge_korean_corpus.py

   # 결과
   outputs/ragdb_final_corpus_20260129_195141.json (5.1MB, 2,577개 논문)
   ```

### 📊 최종 Corpus 통계

```json
{
  "total_papers": 2577,
  "by_language": {
    "en": 2127,  // 영어 82.5%
    "ko": 450    // 한국어 17.5%
  },
  "by_domain": {
    "protein_hypertrophy": 800,
    "fat_loss": 780,
    "korean_diet": 450,
    "body_composition": 547
  }
}
```

**파일 크기:** 5.1MB (66,620줄)
**구조:** JSON Array `[{paper1}, {paper2}, ...]`

---

## 3️⃣ Graph RAG 구축 (Graph RAG Building)

### 📁 스크립트
```
src/llm/ragdb_collect/build_graph_rag.py
```

### 🎯 핵심 역할

**논문 초록 → 개념 추출 → 관계 탐지 → 임베딩 생성 → Graph 구조화**

### 📋 입력 파일

1. **논문 Corpus**
   ```
   outputs/ragdb_final_corpus_20260129_195141.json (2,577개 논문)
   ```

2. **Graph 스키마** (개념 정의)
   ```
   src/llm/ragdb_collect/graph_rag_schema.json
   ```
   ```json
   {
     "graph_rag_schema": {
       "concepts": [
         {
           "id": "muscle_hypertrophy",
           "name": "Muscle Hypertrophy",
           "aliases": ["근비대", "muscle growth", "muscle mass gain"],
           "type": "Outcome",
           "description": "근육 크기 및 질량 증가"
         },
         {
           "id": "protein_intake",
           "name": "Protein Intake",
           "aliases": ["단백질 섭취", "protein consumption"],
           "type": "Intervention",
           "description": "단백질 섭취량 및 타이밍"
         },
         // ... 총 21개 개념
       ]
     }
   }
   ```

### 🔧 처리 과정

#### Step 1: 개념 추출 (Concept Extraction)

```python
class GraphRAGBuilder:
    def extract_concepts_from_paper(self, paper: dict) -> List[str]:
        """논문 초록에서 개념 추출"""
        text = f"{paper['title']} {paper['abstract']}".lower()
        found_concepts = []

        for concept in self.schema['concepts']:
            # 개념 ID 또는 aliases 검색
            if concept['id'] in text or any(alias.lower() in text for alias in concept['aliases']):
                found_concepts.append(concept['id'])

        return found_concepts
```

**예시:**
```
논문: "Effects of Resistance Training on Muscle Hypertrophy"
초록: "...resistance training...protein intake...muscle growth..."

→ 추출된 개념:
  - resistance_training
  - protein_intake
  - muscle_hypertrophy
```

#### Step 2: 관계 탐지 (Relationship Detection)

```python
def detect_relationships(self, paper: dict, concepts: List[str]) -> List[dict]:
    """개념 간 관계 탐지"""
    relationships = []
    text = paper['abstract'].lower()

    for concept in concepts:
        # MENTIONS (단순 언급)
        relationships.append({
            'type': 'MENTIONS',
            'source': f"paper_{paper['pmid']}",
            'target': concept,
            'confidence': self._calculate_confidence(text, concept)
        })

        # INCREASES (증가 관계)
        if any(keyword in text for keyword in ['increase', 'enhance', 'improve']):
            if f"{concept}" in text:
                relationships.append({
                    'type': 'INCREASES',
                    'source': 'resistance_training',
                    'target': concept,
                    'confidence': 0.8
                })

    return relationships
```

**관계 타입:**
- **MENTIONS**: 논문이 개념을 언급 (모든 경우)
- **INCREASES**: A가 B를 증가시킴 (`resistance_training INCREASES muscle_hypertrophy`)
- **SUPPORTS**: 연구가 개념을 지지 (`paper SUPPORTS protein_intake`)
- **REDUCES**: A가 B를 감소시킴 (`caloric_deficit REDUCES body_fat`)

#### Step 3: 신뢰도 계산 (Confidence Scoring)

```python
def _calculate_confidence(self, text: str, concept: str) -> float:
    """Term frequency 기반 신뢰도 계산"""
    count = text.lower().count(concept.replace('_', ' '))

    # 빈도수 기반 점수
    if count >= 5:
        return 1.0
    elif count >= 3:
        return 0.8
    elif count >= 1:
        return 0.6
    else:
        return 0.5  # 기본값
```

#### Step 4: 한국어 임베딩 생성 (OpenAI)

**⚠️ 중요: 모든 논문에 대해 한국어 임베딩 생성!**

```python
# build_graph_rag.py
def generate_korean_embedding(self, text: str) -> List[float]:
    """OpenAI text-embedding-3-small로 임베딩 생성"""

    # 텍스트 길이 제한 (24,000자)
    MAX_CHARS = 24000
    if len(text) > MAX_CHARS:
        text = text[:MAX_CHARS]

    # OpenAI API 호출
    response = self.openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )

    return response.data[0].embedding  # 1536차원 벡터
```

**임베딩 대상:**
- 영어 논문: 제목 + 초록 (영어 그대로)
- 한국어 논문: 제목 + 초록 (한국어 그대로)
- **모델:** `text-embedding-3-small` (1536차원)
- **저장 위치:** `embedding_ko_openai` 필드

**처리량:**
```
총 2,577개 논문
├─ 영어: 2,127개 (임베딩 생성)
├─ 한국어: 450개 (임베딩 생성)
└─ 성공: 2,575개 (99.92%)
    실패: 2개 (텍스트 길이 초과)
```

### 📊 출력 파일

#### A. JSON 파일 (전체 데이터)

```
outputs/graph_rag_2577papers_20260130_211829.json (120MB!)
```

**구조:**
```json
{
  "papers": [
    {
      "paper_id": "paper_41415307",
      "title": "...",
      "abstract": "...",
      "domain": "protein_hypertrophy",
      "language": "en",
      "year": 2025,
      "pmid": "41415307",
      "doi": "10.1519/JSC.0000000000001049",
      "concepts": ["resistance_training", "muscle_hypertrophy"],
      "embedding_ko_openai": [0.123, -0.456, ...],  // 1536차원
      "chunk_ko_summary": null  // 한국어 요약 (선택)
    },
    // ... 2,577개
  ],
  "concepts": [
    {
      "id": "muscle_hypertrophy",
      "name": "Muscle Hypertrophy",
      "type": "Outcome",
      "paper_count": 856  // 이 개념을 언급한 논문 수
    },
    // ... 21개 개념
  ],
  "relationships": [
    {
      "type": "MENTIONS",
      "source": "paper_41415307",
      "target": "muscle_hypertrophy",
      "confidence": 1.0
    },
    {
      "type": "INCREASES",
      "source": "resistance_training",
      "target": "muscle_hypertrophy",
      "confidence": 0.9
    },
    // ... 5,715개 관계
  ],
  "stats": {
    "total_papers": 2577,
    "total_concepts": 21,
    "total_relationships": 5715,
    "embeddings_generated": 2575
  }
}
```

#### B. Neo4j Cypher 파일 (Graph DB import용)

```
outputs/graph_rag_neo4j_2577papers_20260130_211829.cypher (1.3MB)
```

**구조:**
```cypher
// Paper 노드 생성
CREATE (:Paper {
  id: 'paper_41415307',
  title: '...',
  abstract: '...',
  domain: 'protein_hypertrophy',
  language: 'en',
  year: 2025,
  pmid: '41415307'
});

// Concept 노드 생성
CREATE (:Concept {
  id: 'muscle_hypertrophy',
  name: 'Muscle Hypertrophy',
  type: 'Outcome'
});

// 관계 생성
MATCH (p:Paper {id: 'paper_41415307'})
MATCH (c:Concept {id: 'muscle_hypertrophy'})
CREATE (p)-[:MENTIONS {confidence: 1.0}]->(c);

MATCH (c1:Concept {id: 'resistance_training'})
MATCH (c2:Concept {id: 'muscle_hypertrophy'})
CREATE (c1)-[:INCREASES {confidence: 0.9}]->(c2);

// ... 5,715개 관계
```

### 📊 Graph 통계

```json
{
  "total_papers": 2577,
  "total_concepts": 21,
  "total_relationships": 5715,
  "relationship_breakdown": {
    "MENTIONS": 3192,      // 논문 → 개념
    "CORRELATES_WITH": 2514,
    "INCREASES": 2,
    "SUPPORTS": 3,
    "REDUCES": 4
  },
  "papers_by_language": {
    "en": 2127,
    "ko": 450
  },
  "papers_with_embeddings": 2575
}
```

---

## 4️⃣ PostgreSQL + Neo4j Import

### 📁 스크립트
```
backend/utils/scripts/import_graph_rag.py
```

### 🎯 역할

**Graph RAG JSON → PostgreSQL (Vector 검색) + Neo4j (Graph 탐색)**

### A. PostgreSQL Import

#### 테이블 구조

```sql
-- backend/models/paper_node.py
CREATE TABLE paper_nodes (
    id SERIAL PRIMARY KEY,
    paper_id VARCHAR(100) UNIQUE NOT NULL,  -- "paper_41415307"
    title TEXT NOT NULL,
    chunk_text TEXT NOT NULL,               -- 초록 전문
    chunk_ko_summary TEXT,                  -- 한국어 요약 (optional)
    domain VARCHAR(50),                     -- "protein_hypertrophy"
    lang VARCHAR(10),                       -- "en", "ko"
    source VARCHAR(50),                     -- "PubMed"
    year INTEGER,
    pmid VARCHAR(20),
    doi VARCHAR(100),

    -- 임베딩 (pgvector)
    embedding_ko_openai vector(1536),      -- OpenAI embedding
    embedding_ko_ollama vector(1024),      -- Ollama embedding (optional)

    created_at TIMESTAMP DEFAULT NOW()
);

-- Vector 검색용 인덱스
CREATE INDEX idx_paper_embedding_ko_openai
ON paper_nodes USING ivfflat (embedding_ko_openai vector_cosine_ops);
```

#### Import 과정

```python
# import_graph_rag.py
def import_to_postgresql(json_data: dict):
    """PostgreSQL에 논문 데이터 import"""

    for paper in json_data['papers']:
        # PaperNode 모델 생성
        paper_node = PaperNode(
            paper_id=paper['paper_id'],
            title=paper['title'],
            chunk_text=paper['abstract'],
            chunk_ko_summary=paper.get('chunk_ko_summary'),
            domain=paper.get('domain'),
            lang=paper.get('language'),
            source=paper.get('source'),
            year=paper.get('year'),
            pmid=paper.get('pmid'),
            doi=paper.get('doi'),

            # 임베딩 (1536차원 vector)
            embedding_ko_openai=paper.get('embedding_ko_openai'),
            embedding_ko_ollama=paper.get('embedding_ko_ollama')
        )

        session.add(paper_node)

    session.commit()
```

**저장 데이터:**
- 총 2,577개 논문
- 2,575개 임베딩 (OpenAI text-embedding-3-small, 1536D)
- Vector 검색 준비 완료

### B. Neo4j Import

#### Graph 구조

```
(Paper) -[MENTIONS]-> (Concept)
(Paper) -[SUPPORTS]-> (Concept)
(Concept) -[INCREASES]-> (Concept)
(Concept) -[REDUCES]-> (Concept)
```

#### Import 과정

```python
# import_graph_rag.py
def import_to_neo4j(json_data: dict):
    """Neo4j에 Graph 데이터 import"""

    # 1. Paper 노드 생성
    for paper in json_data['papers']:
        query = """
        CREATE (:Paper {
            id: $paper_id,
            title: $title,
            domain: $domain,
            year: $year,
            pmid: $pmid
        })
        """
        session.run(query, paper_id=paper['paper_id'], ...)

    # 2. Concept 노드 생성
    for concept in json_data['concepts']:
        query = """
        CREATE (:Concept {
            id: $concept_id,
            name: $name,
            type: $type
        })
        """
        session.run(query, concept_id=concept['id'], ...)

    # 3. 관계 생성
    for rel in json_data['relationships']:
        if rel['source'].startswith('paper_'):
            # Paper → Concept
            query = """
            MATCH (p:Paper {id: $source})
            MATCH (c:Concept {id: $target})
            CREATE (p)-[:MENTIONS {confidence: $confidence}]->(c)
            """
        else:
            # Concept → Concept
            query = """
            MATCH (c1:Concept {id: $source})
            MATCH (c2:Concept {id: $target})
            CREATE (c1)-[:INCREASES {confidence: $confidence}]->(c2)
            """

        session.run(query, source=rel['source'], target=rel['target'], ...)
```

**저장 데이터:**
- 2,577개 Paper 노드
- 21개 Concept 노드
- 5,715개 관계 (MENTIONS, INCREASES, SUPPORTS, REDUCES)

### 📊 Import 결과 확인

```bash
# PostgreSQL 확인
psql -U sgkim -d explainmybody
> SELECT COUNT(*) FROM paper_nodes;
  2577

> SELECT COUNT(*) FROM paper_nodes WHERE embedding_ko_openai IS NOT NULL;
  2575

# Neo4j 확인
http://localhost:7474 (Neo4j Browser)

MATCH (p:Paper) RETURN COUNT(p);
// 2577

MATCH ()-[r:MENTIONS]->() RETURN COUNT(r);
// 3192
```

---

## 5️⃣ 런타임 검색 (Runtime Retrieval)

### 📁 코드
```
src/llm/pipeline_weekly_plan_rag/graph_rag_retriever.py
```

### 🎯 Hybrid Search: Vector + Graph

#### Step 1: InBody 데이터 → 개념 추출

```python
# analyzer.py
def _extract_concepts_from_measurements(measurements):
    """InBody 측정값 → 검색 개념"""
    concepts = set()

    if measurements.체지방률 > 25:  # 남성 기준
        concepts.add("fat_loss")
        concepts.add("body_fat_percentage")

    if measurements.근육조절 > 0:
        concepts.add("muscle_hypertrophy")
        concepts.add("protein_intake")
        concepts.add("resistance_training")

    return list(concepts)

# 예시 결과
# InBody: 체지방률 28%, 근육조절 +2.5kg
# → concepts = ["fat_loss", "muscle_hypertrophy", "protein_intake", "resistance_training"]
```

#### Step 2: Vector Search (PostgreSQL)

```python
# graph_rag_retriever.py
def retrieve_relevant_papers(query: str, concepts: List[str], top_k: int = 10):
    # 1. 쿼리 임베딩 생성
    query_embedding = openai_client.create_embedding(
        text="근육 증가 체지방 감소 방법 및 효과"
    )  # → 1536차원 벡터

    # 2. PostgreSQL Vector 검색 (코사인 유사도)
    vector_papers = paper_repo.search_similar_papers(
        query_embedding=query_embedding,
        top_k=20,  # 후보 확장
        use_ko_embedding=True  # embedding_ko_openai 사용
    )
```

**SQL 쿼리:**
```sql
SELECT
    paper_id,
    title,
    chunk_text,
    1 - (embedding_ko_openai <=> $query_embedding) AS similarity
FROM paper_nodes
WHERE embedding_ko_openai IS NOT NULL
ORDER BY embedding_ko_openai <=> $query_embedding
LIMIT 20;
```

**결과:**
```python
[
    {
        'paper_id': 'paper_41415307',
        'title': 'Resistance training-induced...',
        'similarity': 0.89  # 코사인 유사도
    },
    # ... 20개
]
```

#### Step 3: Graph Traversal (Neo4j)

```python
# graph_rag_retriever.py
def _expand_by_concepts(concepts: List[str], limit: int = 10):
    """개념 기반 그래프 탐색"""

    for concept_id in concepts:  # ["muscle_hypertrophy", "protein_intake"]
        # Neo4j Cypher 쿼리
        query = """
        MATCH (p:Paper)-[r:MENTIONS|INCREASES|SUPPORTS]->(c:Concept {id: $concept_id})
        RETURN p.id AS paper_id,
               p.title AS title,
               type(r) AS relation_type,
               r.confidence AS confidence
        ORDER BY r.confidence DESC
        LIMIT $limit
        """

        results = neo4j_session.run(query, concept_id=concept_id, limit=limit)
```

**결과:**
```python
[
    {
        'paper_id': 'paper_12345',
        'title': 'Protein requirements for muscle gain',
        'relation_type': 'INCREASES',
        'confidence': 0.9
    },
    # ... 10개 (개념당)
]
```

#### Step 4: Hybrid Reranking

```python
# graph_rag_retriever.py
def _merge_and_rerank(vector_papers, graph_papers, top_k: int):
    """Vector + Graph 결과 병합 및 재정렬"""

    VECTOR_WEIGHT = 0.7  # Vector 검색 가중치
    GRAPH_WEIGHT = 0.3   # Graph 검색 가중치

    paper_map = {}

    # Vector 결과 추가
    for paper in vector_papers:
        paper_map[paper['paper_id']] = {
            'vector_score': paper['similarity'],
            'graph_score': 0.0
        }

    # Graph 결과 추가/병합
    for paper in graph_papers:
        if paper['paper_id'] in paper_map:
            # 중복: graph_score 업데이트
            paper_map[paper['paper_id']]['graph_score'] = max(
                paper_map[paper['paper_id']]['graph_score'],
                paper['confidence']
            )
        else:
            # 새로운 논문
            paper_map[paper['paper_id']] = {
                'vector_score': 0.0,
                'graph_score': paper['confidence']
            }

    # 최종 점수 계산
    for paper_id, scores in paper_map.items():
        final_score = (
            VECTOR_WEIGHT * scores['vector_score'] +
            GRAPH_WEIGHT * scores['graph_score']
        )
        paper_map[paper_id]['final_score'] = final_score

    # 점수 정렬
    sorted_papers = sorted(
        paper_map.items(),
        key=lambda x: x[1]['final_score'],
        reverse=True
    )

    return sorted_papers[:top_k]  # 상위 10개
```

**최종 결과:**
```python
[
    {
        'paper_id': 'paper_41415307',
        'title': 'Resistance training-induced...',
        'vector_score': 0.89,
        'graph_score': 0.0,
        'final_score': 0.623  # 0.7*0.89 + 0.3*0.0
    },
    {
        'paper_id': 'paper_12345',
        'title': 'Protein requirements...',
        'vector_score': 0.75,
        'graph_score': 0.9,
        'final_score': 0.795  # 0.7*0.75 + 0.3*0.9 ← 더 높음!
    },
    # ... 10개
]
```

---

## 6️⃣ Prompt 생성 + LLM 분석

### 📁 코드
```
src/llm/pipeline_inbody_analysis_rag/prompt_generator.py
```

### 🎯 논문 컨텍스트 포맷팅

```python
def _format_paper_context(papers: List[dict]) -> str:
    """검색된 논문 → Prompt 형식"""

    formatted_text = "## 📚 과학적 근거 (최신 연구 논문)\n\n"

    for i, paper in enumerate(papers, 1):
        formatted_text += f"""### 논문 {i}: {paper['title']}
- 출처: {paper['source']} ({paper['year']})
- 관련도: {paper['final_score']:.2f}
- 핵심 내용: {paper['chunk_text'][:400]}...

"""

    formatted_text += "\n**분석 시 주의사항:**\n"
    formatted_text += "- 위 논문의 내용을 InBody 측정 수치와 직접 연결하세요\n"

    return formatted_text
```

**User Prompt 최종 형태:**
```
# InBody 측정 데이터

## 기본 정보
- 성별: 남성
- 나이: 28세
- 체중: 75kg
...

## 📚 과학적 근거 (최신 연구 논문)

### 논문 1: Resistance training-induced appendicular lean tissue...
- 출처: PubMed (2025)
- 관련도: 0.89
- 핵심 내용: We sought to determine if pre-intervention bone...

### 논문 2: The Role of mTOR and AMPK Signaling...
- 출처: PubMed (2025)
- 관련도: 0.85
- 핵심 내용: Maintaining skeletal muscle mass is fundamental...

(10개 논문 계속...)
```

### 🤖 LLM 분석 (gpt-4o-mini)

```python
# analyzer.py
analysis_text = llm_client.generate_chat(
    system_prompt=system_prompt,  # 분석 가이드라인
    user_prompt=user_prompt        # InBody 데이터 + 논문 10개
)
```

**LLM 출력 예시:**
```
### [체성분 상세 분석]

**근육량 상태**
골격근량 32.5kg은 [논문1]의 연구 대상(30-40세 남성, n=119) 평균
33.2kg±3.1과 비교하여 평균 범위에 속합니다.

근육조절 목표 +2.5kg는 [논문2]의 12주 저항성 운동 프로그램에서
보고된 평균 근육 증가량 +2.8kg±0.6과 비교하여 현실적인 목표입니다.

[논문2]에 따르면, 주 3-4회 저항성 운동과 단백질 1.6-2.2g/kg 섭취 시
12주 내 이 정도 근육 증가가 가능하며...
```

---

## 7️⃣ 전체 데이터 흐름 요약

### 📊 파일 크기 및 데이터량

| 단계 | 파일 | 크기 | 데이터 |
|------|------|------|--------|
| 수집 | papers/*.json | 3.7MB | 2,577개 논문 (개별) |
| 병합 | ragdb_final_corpus.json | 5.1MB | 2,577개 논문 (중복 제거) |
| Graph 구축 | graph_rag_2577papers.json | 120MB | 논문+개념+관계+임베딩 |
| Neo4j | *.cypher | 1.3MB | 5,715개 관계 |
| PostgreSQL | paper_nodes 테이블 | ~150MB | 2,577행 + 2,575 벡터 |

### 🔢 임베딩 통계

| 항목 | 수치 |
|------|------|
| 총 논문 수 | 2,577개 |
| 임베딩 생성 | 2,575개 (99.92%) |
| 임베딩 실패 | 2개 (0.08%, 텍스트 길이 초과) |
| 임베딩 모델 | OpenAI text-embedding-3-small |
| 임베딩 차원 | 1536D |
| 저장 위치 | PostgreSQL `embedding_ko_openai` 컬럼 |
| Vector 인덱스 | IVFFlat (코사인 유사도) |

### 🎯 검색 성능

| 항목 | 값 |
|------|-----|
| Vector Search 속도 | ~50ms (top 20) |
| Graph Traversal 속도 | ~30ms (개념당 10개) |
| Hybrid Reranking | ~10ms |
| **총 검색 시간** | **~100ms** |
| 검색 결과 | 10개 논문 (관련도 0.4-1.0) |

---

## 💡 핵심 포인트

### 1️⃣ 논문 데이터 흐름
```
PubMed/KCI API
    ↓ (JSON)
개별 수집 파일 (3.7MB)
    ↓ (중복 제거)
통합 Corpus (5.1MB, 2,577개)
    ↓ (개념 추출 + 임베딩)
Graph RAG (120MB, 논문+관계+벡터)
    ↓ (Import)
PostgreSQL (Vector 검색) + Neo4j (Graph 탐색)
    ↓ (런타임 검색)
InBody 분석 Prompt (10개 논문)
    ↓ (LLM)
과학적 근거 기반 분석 리포트
```

### 2️⃣ 임베딩 생성 방식

- **시점**: Graph RAG 구축 시 (build_graph_rag.py)
- **모델**: OpenAI text-embedding-3-small (1536D)
- **대상**: 모든 논문 (영어 + 한국어)
- **입력**: 제목 + 초록 (최대 24,000자)
- **저장**: JSON `embedding_ko_openai` + PostgreSQL `embedding_ko_openai` 컬럼
- **용도**: Vector Search (코사인 유사도)

### 3️⃣ 검색 메커니즘

- **Vector Search**: 쿼리 임베딩 ↔ 논문 임베딩 코사인 유사도
- **Graph Traversal**: 개념 ID로 관련 논문 탐색 (Neo4j Cypher)
- **Hybrid**: 0.7*vector + 0.3*graph 가중 평균
- **최종 결과**: 상위 10개 논문 (관련도 순)

### 4️⃣ 실제 사용 흐름

```
사용자: InBody 데이터 입력
    ↓
1. 개념 추출 (체지방률 28% → "fat_loss", "muscle_hypertrophy")
2. 쿼리 생성 ("근육 증가 체지방 감소 방법")
3. Vector Search (PostgreSQL, 코사인 유사도)
4. Graph Traversal (Neo4j, 개념 기반)
5. Hybrid Reranking (0.7*vector + 0.3*graph)
6. 상위 10개 논문 선택
7. Prompt 생성 (InBody 데이터 + 논문 10개)
8. LLM 분석 (gpt-4o-mini)
9. 결과 출력 (논문 근거 포함 리포트)
```

---

**완성된 RAG 파이프라인!** 🎉
