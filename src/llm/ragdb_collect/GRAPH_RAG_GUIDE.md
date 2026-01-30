# Graph RAG 구축 가이드

ExplainMyBody를 위한 Graph RAG 시스템 구축 완벽 가이드

## 🎯 Graph RAG란?

**전통적 RAG**:
```
질문 → 벡터 검색 → 유사 문서 → LLM → 답변
```

**Graph RAG**:
```
질문 → 벡터 검색 + 그래프 탐색 → 연결된 개념/논문 → LLM → 답변
```

**장점**:
- ✅ 개념 간 관계 파악
- ✅ 다중 홉 추론 (A → B → C)
- ✅ 모순 탐지 (논문 A vs 논문 B)
- ✅ 증거 강도 평가 (여러 논문이 지지)

## 📊 구조 개요

### 3-Layer Architecture

```
┌─────────────────────────────────────┐
│  Knowledge Layer (개념)              │
│  - 근비대, 단백질, 체성분 등         │
│  - 200-500개 concept nodes          │
└─────────────────────────────────────┘
            ↕ MENTIONS
┌─────────────────────────────────────┐
│  Evidence Layer (논문)               │
│  - 2000-5000개 논문 초록            │
│  - Dual embeddings (OpenAI+Ollama) │
└─────────────────────────────────────┘
            ↕ AFFECTS, CORRELATES_WITH
┌─────────────────────────────────────┐
│  Connection Layer (관계)             │
│  - 10,000-50,000개 relationships    │
└─────────────────────────────────────┘
```

### Node Types

1. **Concept Nodes** (개념): `근비대`, `단백질 섭취`, `체지방률`
2. **Paper Nodes** (논문): 초록 1개 = 1개 노드
3. **Metric Nodes** (지표): `SMM`, `PBF`, `VFL` (InBody)
4. **Intervention Nodes** (처방): `저항성 운동`, `고단백 식단`

### Relationship Types

1. **MENTIONS**: (논문) → (개념) - "논문이 개념을 언급함"
2. **AFFECTS**: (처방) → (지표) - "운동이 근육량을 증가시킴"
3. **CORRELATES_WITH**: (지표) ↔ (지표) - "내장지방과 대사증후군 상관"
4. **SIMILAR_TO**: (논문) ↔ (논문) - "논문 간 유사성"
5. **REQUIRES**: (목표) → (처방) - "근비대는 단백질 섭취 필요"
6. **CONTRADICTS**: (논문) ↔ (논문) - "논문 간 모순"

## 🚀 빠른 시작

### Step 1: 논문 수집 (이미 완료)

```bash
# PubMed 영어 논문
python main.py --email your@email.com

# KCI 한국어 논문
python kci_api_collector.py

# 전체 병합
python merge_korean_corpus.py

# → outputs/ragdb_final_corpus_XXXXXX.json 생성
```

### Step 2: Graph RAG 구축

```bash
# NetworkX 설치 (권장)
pip install networkx

# 그래프 구축 실행
python build_graph_rag.py
```

**결과**:
- `outputs/graph_rag_XXXXXX.json` - JSON 형식 그래프
- `outputs/graph_rag_neo4j_XXXXXX.cypher` - Neo4j 임포트용
- `outputs/graph_rag_stats_XXXXXX.json` - 통계

### Step 3: 결과 확인

```bash
# 통계 확인
cat outputs/graph_rag_stats_*.json

# 예상 결과:
# {
#   "total_papers": 3000,
#   "papers_with_concepts": 2850,
#   "unique_concepts": 120,
#   "total_mentions": 8500
# }
```

## 📁 생성된 파일

### 1. `graph_rag_schema.json`

**전체 스키마 정의**:
- 4개 도메인 (protein_hypertrophy, fat_loss, korean_diet, body_composition)
- 6개 카테고리 (body_metrics, fitness_goals, exercise_types, nutrition, health_conditions, measurement_methods)
- 50+ 개념 (근비대, 단백질 섭취, 체지방률 등)
- 7개 관계 유형

### 2. `graph_rag_XXXXXX.json`

**실제 그래프 데이터** (NetworkX node-link format):

```json
{
  "nodes": [
    {
      "id": "muscle_hypertrophy",
      "node_type": "concept",
      "name_ko": "근비대",
      "name_en": "muscle hypertrophy",
      "importance": 0.95
    },
    {
      "id": "paper_12345678",
      "node_type": "paper",
      "title": "High protein intake...",
      "abstract": "...",
      "lang": "en",
      "domain": "protein_hypertrophy"
    }
  ],
  "links": [
    {
      "source": "paper_12345678",
      "target": "muscle_hypertrophy",
      "type": "MENTIONS",
      "confidence": 0.92
    }
  ]
}
```

### 3. `graph_rag_neo4j_XXXXXX.cypher`

**Neo4j 임포트용 Cypher 스크립트**:

```cypher
// Concept Nodes
CREATE (cmuscle_hypertrophy:Concept {id: 'muscle_hypertrophy', name_ko: '근비대', importance: 0.95});

// Paper Nodes
CREATE (ppaper_12345678:Paper {id: 'paper_12345678', title: 'High protein intake...'});

// MENTIONS Relationships
MATCH (p:Paper {id: 'paper_12345678'}), (c:Concept {id: 'muscle_hypertrophy'})
CREATE (p)-[:MENTIONS {confidence: 0.92}]->(c);
```

## 🔍 개념 추출 로직

### 단순 키워드 매칭 (현재)

```python
# 스키마에 정의된 개념
concept = {
  "id": "muscle_hypertrophy",
  "name_ko": "근비대",
  "name_en": "muscle hypertrophy",
  "synonyms_ko": ["근육 증가", "근육 성장"],
  "synonyms_en": ["muscle growth", "muscle gain"]
}

# 논문 초록에서 검색
text = "High protein intake supports muscle hypertrophy..."
if "muscle hypertrophy" in text.lower():
    # MENTIONS 관계 생성
    confidence = 0.92
```

### 고급 방법 (추후 구현 가능)

1. **Named Entity Recognition (NER)**
   - spaCy, BioBERT 등 사용
   - 의학/운동 용어 자동 추출

2. **LLM 기반 추출**
   - GPT-4로 개념 추출
   - 관계 유형 자동 분류

3. **Embedding 유사도**
   - 개념 임베딩 vs 문장 임베딩
   - 코사인 유사도 > 0.8이면 MENTIONS

## 📊 개념 카테고리

### 1. Body Metrics (신체 지표)
- `skeletal_muscle_mass` (골격근량)
- `body_fat_percentage` (체지방률)
- `visceral_fat_level` (내장지방)
- `basal_metabolic_rate` (기초대사량)
- `smi` (골격근량지수)

### 2. Fitness Goals (운동 목표)
- `muscle_hypertrophy` (근비대)
- `fat_loss` (지방 감소)
- `body_recomposition` (체형 개선)
- `strength_gain` (근력 향상)

### 3. Exercise Types (운동 유형)
- `resistance_training` (저항성 운동)
- `cardio` (유산소 운동)
- `hiit` (고강도 인터벌 트레이닝)

### 4. Nutrition (영양소)
- `protein_intake` (단백질 섭취)
- `calorie_deficit` (칼로리 결핍)
- `carbohydrate` (탄수화물)

### 5. Health Conditions (건강 상태)
- `sarcopenia` (근감소증)
- `metabolic_syndrome` (대사증후군)
- `sarcopenic_obesity` (근감소성 비만)

### 6. Measurement Methods (측정 방법)
- `bia` (생체전기저항분석)
- `inbody` (인바디)
- `dxa` (이중에너지 X선 흡수계측법)

## 🎯 사용 예시

### 예시 1: 근비대를 위한 처방 찾기

```cypher
// Neo4j Cypher 쿼리
MATCH (goal:Concept {id: 'muscle_hypertrophy'})
      -[:REQUIRES]->(intervention)
      -[:AFFECTS]->(metric:Metric)
RETURN goal, intervention, metric
```

**결과**:
```
muscle_hypertrophy → resistance_training → skeletal_muscle_mass (증가)
muscle_hypertrophy → protein_intake → muscle_protein_synthesis (증가)
```

### 예시 2: 특정 개념의 증거 강도

```python
# Python (NetworkX)
import networkx as nx

# 그래프 로드
with open('outputs/graph_rag_XXXXXX.json', 'r') as f:
    data = json.load(f)
graph = nx.node_link_graph(data)

# "muscle_hypertrophy"를 언급하는 논문 수
papers_mentioning = [
    source for source, target, data in graph.edges(data=True)
    if target == 'muscle_hypertrophy' and data['type'] == 'MENTIONS'
]

print(f"근비대를 언급하는 논문: {len(papers_mentioning)}개")
# → 근비대를 언급하는 논문: 345개
```

### 예시 3: 다중 홉 쿼리 (A → B → C)

```cypher
// "체지방률이 높으면 어떤 건강 문제가 발생하나?"
MATCH path = (bf:Metric {id: 'body_fat_percentage'})
             -[:CORRELATES_WITH*1..2]->(condition:Concept)
WHERE condition.category = 'health_conditions'
RETURN path
```

**결과**:
```
body_fat_percentage → metabolic_syndrome → diabetes
body_fat_percentage → visceral_fat → cardiovascular_disease
```

## 🔧 커스터마이징

### 새로운 개념 추가

`graph_rag_schema.json` 편집:

```json
{
  "concept_categories": {
    "fitness_goals": {
      "concepts": [
        {
          "id": "endurance",
          "name_ko": "지구력",
          "name_en": "endurance",
          "synonyms_ko": ["심폐 지구력"],
          "synonyms_en": ["cardiovascular endurance"],
          "importance": 0.80
        }
      ]
    }
  }
}
```

재구축:
```bash
python build_graph_rag.py
```

### 신뢰도 임계값 조정

`build_graph_rag.py` 수정:

```python
# 현재: 등장 횟수 기반
confidence = min(0.5 + (count * 0.1), 1.0)

# 수정: 더 엄격하게
confidence = min(0.3 + (count * 0.2), 1.0)  # 2번 이상 등장해야 높은 신뢰도
```

## 📈 성능 최적화

### 1. 개념 검색 속도 향상

**현재** (O(n*m)):
```python
for concept in concepts:
    for term in concept['search_terms']:
        if term in text:
            ...
```

**최적화** (Trie 자료구조):
```python
from pyahocorasick import Automaton

# 한 번만 구축
automaton = Automaton()
for concept_id, concept in concepts.items():
    for term in concept['search_terms']:
        automaton.add_word(term, (concept_id, term))
automaton.make_automaton()

# 빠른 검색
for end_index, (concept_id, term) in automaton.iter(text):
    ...
```

### 2. 대용량 처리

**배치 처리**:
```python
# 논문을 1000개씩 나누어 처리
batch_size = 1000
for i in range(0, len(papers), batch_size):
    batch = papers[i:i+batch_size]
    process_batch(batch)
    print(f"처리: {i+batch_size}/{len(papers)}")
```

### 3. 병렬 처리

```python
from multiprocessing import Pool

def process_paper(paper):
    mentions = extract_mentioned_concepts(paper['abstract'])
    return paper, mentions

with Pool(processes=8) as pool:
    results = pool.map(process_paper, papers)
```

## 🗄️ Neo4j 사용 (권장)

### 설치

```bash
# Docker로 Neo4j 실행
docker run \
    --name neo4j \
    -p 7474:7474 -p 7687:7687 \
    -e NEO4J_AUTH=neo4j/password \
    neo4j:latest
```

### 임포트

```bash
# Cypher 스크립트 실행
cat outputs/graph_rag_neo4j_XXXXXX.cypher | \
cypher-shell -u neo4j -p password
```

### 브라우저 접속

```
http://localhost:7474
```

### 쿼리 예시

```cypher
// 가장 많이 언급된 개념 Top 10
MATCH (p:Paper)-[m:MENTIONS]->(c:Concept)
RETURN c.name_ko, count(p) as mention_count
ORDER BY mention_count DESC
LIMIT 10

// 특정 도메인의 핵심 개념
MATCH (p:Paper {domain: 'body_composition'})-[:MENTIONS]->(c:Concept)
RETURN c.name_ko, count(p) as papers
ORDER BY papers DESC
LIMIT 10
```

## 📚 다음 단계

### 1. Embedding 추가

```python
# 각 Paper Node에 임베딩 추가
import openai

for paper in papers:
    embedding = openai.Embedding.create(
        input=paper['abstract'],
        model="text-embedding-3-small"
    )
    paper['embedding'] = embedding['data'][0]['embedding']
```

### 2. 관계 추론

```python
# AFFECTS 관계 추론 (LLM 사용)
prompt = f"""
논문: {paper['abstract']}

이 논문에서 언급된 처방(운동/영양)이 어떤 지표에 영향을 미치나요?
형식: (처방) → (지표) [효과: 증가/감소, 강도: high/medium/low]
"""

response = llm.generate(prompt)
# → "resistance_training → skeletal_muscle_mass [증가, high]"
```

### 3. RAG 시스템 통합

```python
# Hybrid RAG: Vector + Graph
def hybrid_rag_query(question: str):
    # 1. 벡터 검색
    vector_results = vector_search(question, top_k=10)

    # 2. 그래프 확장
    expanded_papers = []
    for paper in vector_results:
        # 연결된 개념 찾기
        concepts = graph.neighbors(paper['id'])
        # 같은 개념을 언급하는 다른 논문 찾기
        related_papers = find_related_papers(concepts)
        expanded_papers.extend(related_papers)

    # 3. 재랭킹 (그래프 증거 강도 고려)
    ranked = rerank_by_graph_evidence(expanded_papers)

    # 4. LLM 생성
    answer = llm.generate(question, context=ranked)
    return answer
```

## 🎉 완성 체크리스트

- [ ] 논문 수집 완료 (2000-5000개)
- [ ] `graph_rag_schema.json` 검토 및 커스터마이징
- [ ] `build_graph_rag.py` 실행
- [ ] `graph_rag_XXXXXX.json` 생성 확인
- [ ] Neo4j 임포트 (선택)
- [ ] 테스트 쿼리 실행
- [ ] Embedding 추가 (선택)
- [ ] RAG 시스템 통합

## 📞 문제 해결

### "개념이 너무 적게 추출됨"

**원인**: 키워드 매칭이 너무 엄격

**해결**:
1. 동의어 추가 (`graph_rag_schema.json`)
2. 신뢰도 임계값 낮추기
3. 형태소 분석 사용 (한국어)

### "그래프가 너무 커서 느림"

**해결**:
1. Neo4j 사용 (인덱싱 자동)
2. 중요도 낮은 개념 필터링
3. 신뢰도 임계값 높이기

### "논문 간 연결이 없음"

**현재**: MENTIONS만 구현됨

**추가 구현 필요**:
- SIMILAR_TO (임베딩 유사도)
- CONTRADICTS (LLM 판단)
- SUPPORTS (동일 결론)

## 📖 참고 자료

- [Microsoft GraphRAG](https://github.com/microsoft/graphrag)
- [Neo4j Graph Data Science](https://neo4j.com/product/graph-data-science/)
- [NetworkX Documentation](https://networkx.org/)
- [Graph Neural Networks](https://distill.pub/2021/gnn-intro/)
