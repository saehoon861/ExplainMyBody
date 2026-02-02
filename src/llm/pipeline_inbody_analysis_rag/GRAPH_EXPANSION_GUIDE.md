# Graph Expansion Pipeline 완전 가이드

**작성일:** 2026-02-02
**목적:** Rule-based Seed + Graph Hop + LLM 글쓰기 = 완전 Deterministic Pipeline

---

## 🎯 핵심 아이디어

### 기존 문제점

```
❌ LLM이 reasoning → concept 추출 (불안정)
❌ 하드코딩 룰 → concept 추출 (확장성 부족)
❌ LLM이 분석 + 글쓰기 (역할 혼재)
```

### Graph Expansion 해결책

```
✅ Rule-based Seed 추출 (deterministic)
✅ Graph Hop 자동 확장 (SQL reasoning)
✅ LLM은 글쓰기만 (역할 분리)
```

---

## 📊 전체 Flow

```
┌─────────────────────────────────────────────────────────┐
│ Step 0: DB InBody Load                                  │
└────────────────┬────────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────────────────────────┐
│ Step 1: Rule-based Seed Extractor                      │
│                                                         │
│ Input:  InBody measurements                            │
│ Output: Seed concept IDs + 체형 판정 자연어              │
│                                                         │
│ 예: skeletal_muscle_low (seed: skeletal_muscle_low)    │
│     visceral_fat_high (seed: visceral_fat_high)        │
│                                                         │
│ ✅ LLM 없음 (완전 deterministic)                        │
└────────────────┬────────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────────────────────────┐
│ Step 2: Graph Expansion Retriever (SQL Hop)            │
│                                                         │
│ Step A: Seed → Papers                                  │
│   SELECT DISTINCT paper_id                             │
│   FROM paper_concept_relations                         │
│   WHERE concept_id = ANY(:seed_concepts)               │
│                                                         │
│ Step B: Papers → Risk Concepts (자동 확장)              │
│   SELECT concept_id, COUNT(*) as paper_count           │
│   FROM paper_concept_relations                         │
│   WHERE paper_id = ANY(:paper_ids)                     │
│   GROUP BY concept_id                                   │
│   ORDER BY paper_count DESC                            │
│                                                         │
│ Step C: Papers → Intervention Concepts (자동 확장)      │
│   (동일한 SQL, concept_type 필터만 다름)                 │
│                                                         │
│ Step D: Evidence Chunks                                │
│   SELECT pn.*, pcr.*                                   │
│   FROM paper_nodes pn                                  │
│   JOIN paper_concept_relations pcr ON ...              │
│   WHERE ...                                             │
│                                                         │
│ ✅ LLM 없음 (Graph가 reasoning)                         │
└────────────────┬────────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────────────────────────┐
│ Step 3: DB Save (health_records)                       │
└────────────────┬────────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────────────────────────┐
│ Step 4: LLM Report Writer (글쓰기만)                    │
│                                                         │
│ Input:                                                  │
│   - 체형 판정 (Rule-based)                              │
│   - Seed concepts                                       │
│   - Risk concepts (Graph 확장)                          │
│   - Intervention concepts (Graph 확장)                  │
│   - Evidence chunks                                     │
│                                                         │
│ Output: 자연어 리포트 (분석 없음, 정리만)                 │
│                                                         │
│ ✅ LLM은 reasoning 안 함 (글쓰기만)                      │
└────────────────┬────────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────────────────────────┐
│ Step 5: DB Save (analysis_reports)                     │
└─────────────────────────────────────────────────────────┘
```

---

## 🔑 핵심 개선 사항

### 1. Seed Tag 포함 (완전 Deterministic)

**Call1 출력 예시:**

```
[체형 판정 결과]

- 체형 유형: 근육 부족형 + 내장지방 과다

- 근육 상태: 부족 (seed: skeletal_muscle_low)

- 지방 상태: 과다 (seed: body_fat_high)

- 내장지방 위험도: 주의 (seed: visceral_fat_high)

- key_risks:
  - 내장지방 과다 (seed: visceral_fat_high)
  - 근육량 부족 (seed: skeletal_muscle_low)
```

**장점:**
- LLM 추론 없이 `(seed: xxx)` 태그로 직접 파싱
- 100% deterministic
- 동일 입력 → 동일 출력 보장

### 2. Graph Hop 자동 확장

**기존:**
```python
# 하드코딩 룰
if 체지방률 > 25:
    concepts = ["fat_loss", "body_fat_percentage"]
```

**개선:**
```sql
-- SQL이 자동 확장
Seed: visceral_fat_high
  ↓ (SQL Hop)
Papers: [논문1, 논문2, 논문3]
  ↓ (SQL Hop)
Risk: [metabolic_syndrome_risk, cardiovascular_disease_risk]
  ↓ (SQL Hop)
Intervention: [resistance_training, aerobic_exercise, high_protein_diet]
```

**장점:**
- 확장성 높음 (새 논문 추가 시 자동 확장)
- Graph 구조가 reasoning 담당
- LLM reasoning 제거

### 3. LLM 역할 분리

**기존:**
```
LLM이 모든 것 담당:
- 분석
- 판정
- concept 추출
- Evidence 통합
- 글쓰기
```

**개선:**
```
역할 분리:
- Rule이 판정 (deterministic)
- Graph가 확장 (SQL reasoning)
- LLM은 글쓰기만 (no reasoning)
```

---

## 📁 파일 구조

```
pipeline_inbody_analysis_rag/
├── analyzer.py                         # 기존 Single Call
├── analyzer_multi_call.py              # Multi-Call (이전 버전)
├── analyzer_graph_expansion.py         # ✨ Graph Expansion (최신)
│
├── prompt_generator.py                 # 기존
├── prompts_multi_call.py               # Multi-Call
├── prompts_graph_expansion.py          # ✨ Graph Expansion
│
├── concept_definitions.py              # 기존 concept (deprecated)
├── seed_concept_definitions.py         # ✨ Seed concepts (21개 관계 기반)
│
├── rule_based_seed_extractor.py        # ✨ Rule-based Seed 추출
├── graph_expansion_retriever.py        # ✨ Graph Hop SQL
│
├── MULTI_CALL_GUIDE.md                 # 이전 버전
└── GRAPH_EXPANSION_GUIDE.md            # ✨ 이 문서

llm_test_sk/
├── test_with_graph_rag.py              # 기존
├── test_multi_call_rag.py              # Multi-Call
└── test_graph_expansion.py             # ✨ Graph Expansion
```

---

## 🚀 사용 방법

### 테스트 실행

```bash
cd /home/user/projects/ExplainMyBody/src/llm/llm_test_sk

# 기본 실행
python test_graph_expansion.py

# 다른 샘플
python test_graph_expansion.py --sample=gymnast
python test_graph_expansion.py --sample=obese

# Graph Expansion 없이
python test_graph_expansion.py --no-expansion
```

### 코드에서 사용

```python
from pipeline_inbody_analysis_rag.analyzer_graph_expansion import InBodyAnalyzerGraphExpansion
from llm_clients import create_llm_client

# 초기화
llm_client = create_llm_client("gpt-4o-mini")
analyzer = InBodyAnalyzerGraphExpansion(
    llm_client=llm_client,
    model_version="gpt-4o-mini",
    use_graph_expansion=True
)

# 분석
result = analyzer.analyze(
    user_id=user_id,
    measurements=measurements,
    source="manual"
)

# 결과
print(result["seed_concepts"])           # Seed IDs
print(result["risk_concepts"])           # Graph 확장된 Risk
print(result["intervention_concepts"])   # Graph 확장된 Intervention
print(result["final_report"])            # LLM 리포트
```

---

## 🔧 Seed Concept 추가 방법

### 1. `seed_concept_definitions.py` 수정

```python
SEED_CONCEPTS["new_seed_id"] = {
    "name_ko": "새로운 Seed",
    "concept_type": "Seed",
    "description": "설명",
    "extraction_rule": {
        "field": "필드명",
        "condition": lambda measurements: (
            # 추출 조건
            measurements.BMI > 30
        )
    }
}
```

### 2. DB에 관계 추가

```sql
INSERT INTO paper_concept_relations (paper_id, concept_id, ...)
VALUES (...);
```

### 3. 테스트

```bash
python test_graph_expansion.py
```

---

## 📊 기존 vs Graph Expansion 비교

| 항목 | 기존 (Multi-Call) | Graph Expansion |
|------|------------------|-----------------|
| **Seed 추출** | LLM Router | Rule-based (deterministic) |
| **Concept 확장** | LLM 추론 | Graph SQL Hop |
| **맥락 이해** | LLM | Rule + Graph |
| **Evidence 검색** | Vector + Graph | Graph Hop 전용 |
| **LLM 역할** | 분석 + 글쓰기 | 글쓰기만 |
| **Deterministic** | ❌ (LLM 변동성) | ✅ (완전 재현) |
| **확장성** | 중간 | 높음 (Graph 자동 확장) |
| **LLM Calls** | 3회 | 1회 (글쓰기만) |
| **비용** | 중간 | 낮음 |
| **정확도** | 중간 | 높음 (Graph reasoning) |

---

## 🎯 Graph Expansion의 장점

### 1. 완전 Deterministic

```
동일 InBody 입력 → 동일 Seeds → 동일 Graph Hop → 동일 Evidence
```

- 재현성 100%
- 디버깅 쉬움
- A/B 테스트 가능

### 2. Graph가 Reasoning

```
LLM: "내장지방이 높네? 어떤 concept을 써야 할까?"
  ↓ (불안정)

Graph: "visceral_fat_high seed → 논문 [1,2,3] → Risk [A,B] → Intervention [X,Y]"
  ↓ (안정적)
```

### 3. 자동 확장

```
새 논문 추가:
  ↓
Graph 자동 업데이트:
  ↓
Concept 자동 확장:
  ↓
추가 코드 수정 불필요!
```

### 4. LLM 역할 최소화

```
기존: LLM이 모든 것 담당 (불안정)
개선: LLM은 글쓰기만 (안정)
```

---

## ⚠️ 주의사항

### 1. Paper-Concept 관계 필수

Graph Expansion은 `paper_concept_relations` 테이블이 필수입니다.

테이블이 비어있으면 확장 불가능.

### 2. Seed는 하드코딩 룰

Rule-based Seed Extractor는 하드코딩 룰입니다.

새로운 패턴은 수동으로 추가해야 합니다.

### 3. Weekly Plan에는 적용 안 함

이 구조는 **InBody 분석 전용**입니다.

Weekly Plan은 별도 구조 유지.

### 4. concept_id 매핑 필요

기존 `paper_concept_relations`의 `concept_id`와

새로운 `seed_concept_definitions`의 seed_id를 매핑해야 합니다.

`LEGACY_CONCEPT_TO_SEED_MAPPING` 참고.

---

## 🔍 디버깅 팁

### Seed 추출 확인

```python
from pipeline_inbody_analysis_rag.rule_based_seed_extractor import RuleBasedSeedExtractor

extractor = RuleBasedSeedExtractor()
seeds = extractor.extract_seeds(measurements)
print(seeds)
```

### Graph Expansion 단계별 확인

```python
from pipeline_inbody_analysis_rag.graph_expansion_retriever import GraphExpansionRetriever

retriever = GraphExpansionRetriever()
result = retriever.expand_and_retrieve(
    seed_concept_ids=["skeletal_muscle_low", "visceral_fat_high"]
)

print(f"Papers: {len(result['seed_papers'])}")
print(f"Risks: {len(result['risk_concepts'])}")
print(f"Interventions: {len(result['intervention_concepts'])}")
```

---

## 📚 관련 문서

- `seed_concept_definitions.py` - Seed 정의 (21개 관계)
- `rule_based_seed_extractor.py` - Rule-based 추출
- `graph_expansion_retriever.py` - Graph Hop SQL
- `prompts_graph_expansion.py` - LLM 글쓰기 프롬프트
- `analyzer_graph_expansion.py` - 전체 Pipeline
- `test_graph_expansion.py` - 테스트 스크립트

---

**작성일:** 2026-02-02
**작성자:** Claude Code
**Pipeline:** Rule + Graph + LLM = Deterministic
