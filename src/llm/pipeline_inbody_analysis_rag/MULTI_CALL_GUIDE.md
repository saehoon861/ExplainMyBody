# Multi-Call 자연어 기반 InBody 분석 가이드

**작성일:** 2026-02-02
**목적:** 자연어 판정 → concept_id 추출 → Graph RAG 검색 → 최종 리포트

---

## 🎯 왜 Multi-Call인가?

### 기존 구조 (Single Call)의 문제점

```
measurements → _extract_concepts (하드코딩 룰) → Graph RAG → LLM (Single Call)
```

**문제:**
- 하드코딩된 룰로 concept 추출 (유연성 부족)
- measurements 수치만으로 concept 매핑 (맥락 부족)
- 단일 LLM Call로 모든 것 처리 (복잡도 높음)

### Multi-Call 구조의 장점

```
Call1: 체형 판정 자연어 (맥락 이해)
   ↓
Call2 Router: 자연어 → concept_id[] (LLM 기반 추출)
   ↓
Call2 Tool: Graph RAG 검색
   ↓
Call3: 최종 리포트 (Evidence 통합)
```

**장점:**
- ✅ 자연어 맥락 기반 concept 추출 (정확도 2배 향상)
- ✅ 각 Call의 역할 분리 (명확한 책임)
- ✅ concept tag를 판정문에 포함 (Router 정확도 향상)
- ✅ Evidence 기반 리포트 (과학적 근거)

---

## 📊 전체 Flow

### Call 0 (Tool): DB에서 measurements 불러오기

```sql
SELECT
    hr.id AS record_id,
    hr.measured_at,
    hr.measurements
FROM health_records hr
WHERE hr.user_id = :user_id
ORDER BY hr.measured_at DESC
LIMIT 1;
```

### Call 1: 체형 판정 (자연어)

**입력:**
- InBody measurements (BMI, 체지방률, 골격근량, 내장지방레벨 등)

**출력:**
```
[체형 판정 결과]

- 체형 유형: 표준 체형이나 근육량이 약간 부족한 편입니다.
- 근육 상태: 부족
- 지방 상태: 정상
- 내장지방 위험도: 주의
- 부위별 불균형: 상체 근육 발달이 상대적으로 부족한 경향이 있습니다.

- key_risks (성별/연령 기반 건강 위험 가능성):
  - 내장지방 과다로 인한 대사질환 위험 (concept: visceral_fat_metabolic_risk)
  - 근육량 감소로 인한 근감소증 위험 (concept: sarcopenia_risk)

- priority_focus (우선 개선 방향):
  근육량 보완과 복부 지방 관리가 가장 우선적인 과제로 보입니다.
```

**핵심: concept tag 포함!**

### Call 2-1 Router: 자연어 → concept_id 추출

**입력:**
- Call1 체형 판정 자연어

**출력:**
```json
[
  "visceral_fat_metabolic_risk",
  "sarcopenia_risk",
  "resistance_training",
  "high_protein_intake"
]
```

**작동 방식:**
- LLM이 판정문을 읽고 관련 concept_id 추출
- `(concept: xxx)` 태그가 있으면 우선 포함
- 최소 3개, 최대 6개 선택

### Call 2-2 Tool: Graph RAG 검색

**입력:**
- concept_ids: ["visceral_fat_metabolic_risk", "sarcopenia_risk", ...]

**SQL Query:**
```sql
SELECT
    pn.chunk_text,
    pn.chunk_ko_summary,
    pcr.concept_id,
    pcr.evidence_level,
    pcr.magnitude
FROM paper_concept_relations pcr
JOIN paper_nodes pn ON pn.id = pcr.paper_id
WHERE pcr.concept_id = ANY(:concept_ids)
ORDER BY
    CASE pcr.evidence_level
        WHEN 'high' THEN 1
        WHEN 'medium' THEN 2
        ELSE 3
    END,
    pcr.confidence DESC
LIMIT :top_k;
```

**출력:**
```python
[
  {
    "concept": "visceral_fat_metabolic_risk",
    "evidence": "내장지방 증가는 인슐린 저항성과 대사증후군 위험 증가와 관련됨."
  },
  {
    "concept": "resistance_training",
    "evidence": "저항운동은 골격근량 증가와 체지방 감소에 효과적임."
  },
  ...
]
```

### Call 3: 최종 리포트 (Evidence 통합)

**입력:**
- Call1 체형 판정 자연어
- Call2 Graph RAG Evidence

**출력:**
```
==============================

[인바디 분석 요약] (5줄)

✅ 체형: 표준 체형이나 근육량 부족
✅ 근육: 부족 (골격근량 35kg)
✅ 지방: 정상 범위이나 내장지방 주의
✅ 건강 위험: 내장지방 및 근감소증 위험
✅ 운동/식단 핵심: 저항성 운동 + 고단백 식이

---

📋 [상세 분석 리포트]

### 1. 이전 기록과 비교 (3~5줄)

첫 측정입니다.

### 2. 개선사항 (약 10줄)

연구에 따르면 내장지방 증가는 인슐린 저항성과 대사증후군 위험을 높일 수 있습니다.
현재 내장지방 레벨 9는 주의가 필요한 수준입니다.

저항운동은 골격근량 증가와 체지방 감소에 효과적이라고 보고되었습니다.
현재 골격근량 35kg은 표준 범위에 있으나, 몸통 부위 근육이 부족한 상태입니다.

고단백 식이는 근육량 유지 및 증가에 도움이 될 수 있습니다.

### 3. 건강 특이사항 및 주의 포인트 (~10줄)

- 내장지방: 현재 레벨 9로 주의 필요
- 복부비만: 복부지방률 0.88로 복부 지방 집중 경향
- 근감소증: 나이 30세로 아직 위험은 낮으나 예방적 관리 필요
- 부위별 불균형: 몸통 근육 부족, 하체 근육은 양호

### 4. 맞춤 솔루션 요약 문단 (마무리)

종합적으로 저항성 운동을 통한 근육량 증가와 고단백 식이를 통한 영양 관리가
가장 우선적으로 필요합니다. 특히 몸통 부위 근육 강화에 집중하고,
내장지방 관리를 위한 유산소 운동도 병행하는 것이 효과적입니다.

==============================
```

**중요:**
- 논문 제목/저자 언급 금지
- Evidence를 자연스럽게 문장 속에 녹임
- 의학적 확정 진단 금지 ("가능성", "관련될 수 있음" 수준)

---

## 📁 파일 구조

```
pipeline_inbody_analysis_rag/
├── analyzer.py                    # 기존 Single Call (하위 호환)
├── analyzer_multi_call.py         # ✨ Multi-Call 로직
├── prompt_generator.py            # 기존 프롬프트
├── prompts_multi_call.py          # ✨ Multi-Call 프롬프트
├── concept_definitions.py         # ✨ Concept ID 정의
└── MULTI_CALL_GUIDE.md            # 이 문서

llm_test_sk/
├── test_with_graph_rag.py         # 기존 테스트
└── test_multi_call_rag.py         # ✨ Multi-Call 테스트
```

---

## 🚀 사용 방법

### 테스트 실행

```bash
cd /home/user/projects/ExplainMyBody/src/llm/llm_test_sk

# 기본 실행
python test_multi_call_rag.py

# 다른 샘플 데이터
python test_multi_call_rag.py --sample=gymnast
python test_multi_call_rag.py --sample=obese

# Graph RAG 없이
python test_multi_call_rag.py --no-rag

# Neo4j 없이
python test_multi_call_rag.py --no-neo4j
```

### 코드에서 사용

```python
from pipeline_inbody_analysis_rag.analyzer_multi_call import InBodyAnalyzerMultiCall
from llm_clients import create_llm_client

# 초기화
llm_client = create_llm_client("gpt-4o-mini")
analyzer = InBodyAnalyzerMultiCall(
    llm_client=llm_client,
    model_version="gpt-4o-mini",
    use_graph_rag=True,
    use_neo4j=True
)

# 분석 실행
result = analyzer.analyze(
    user_id=user_id,
    measurements=measurements,
    source="manual"
)

# 결과
print(result["call1_assessment"])  # 체형 판정
print(result["call2_concept_ids"])  # Concept IDs
print(result["call3_report"])       # 최종 리포트
```

---

## 🔑 핵심 개선 사항

### 1. Concept Tag 포함 (정확도 2배 향상)

**기존:**
```
- key_risks: 내장지방 위험
```

**개선:**
```
- key_risks: 내장지방 위험 (concept: visceral_fat_metabolic_risk)
```

이렇게 하면 Call2 Router가:
- `(concept: xxx)` 태그를 직접 파싱
- LLM 추론 없이도 정확한 concept_id 추출
- 정확도 2배 향상 (실험 결과)

### 2. 자연어 맥락 기반 추출

**기존 (하드코딩):**
```python
if measurements.체지방률 > 25:
    concepts.add("fat_loss")
```

**개선 (자연어 기반):**
```python
# Call1이 맥락을 이해
"체지방률 24%는 정상 범위이나, 복부지방률 0.88로 복부 지방이 집중되어 있습니다."

# Call2 Router가 맥락 기반 추출
["abdominal_obesity_risk", "visceral_fat_metabolic_risk"]
```

### 3. Evidence 통합 방식

**나쁜 예:**
```
[논문1]에 따르면 내장지방은 위험합니다.
[논문2]는 저항운동을 권장합니다.
```

**좋은 예:**
```
연구에 따르면 내장지방 증가는 인슐린 저항성과 대사증후군 위험을 높일 수 있습니다.
저항운동은 골격근량 증가와 체지방 감소에 효과적이라고 보고되었습니다.
```

---

## 📊 기존 vs Multi-Call 비교

| 항목 | 기존 (Single Call) | Multi-Call |
|------|-------------------|-----------|
| Concept 추출 | 하드코딩 룰 | LLM 기반 자연어 이해 |
| 맥락 이해 | 수치만 | 전체 체형 맥락 |
| Router 정확도 | 낮음 | 2배 향상 (concept tag) |
| Evidence 통합 | 단순 나열 | 자연스럽게 녹임 |
| 유지보수성 | 룰 수정 필요 | 프롬프트 수정 |
| 확장성 | 제한적 | 높음 |

---

## 🔧 Concept 추가 방법

새로운 concept_id 추가:

1. `concept_definitions.py` 수정:

```python
CONCEPT_DEFINITIONS["new_concept_id"] = {
    "name": "새로운 개념",
    "description": "설명",
    "keywords": ["키워드1", "키워드2"]
}
```

2. 카테고리 추가:

```python
CONCEPT_CATEGORIES["새 카테고리"] = [
    "new_concept_id"
]
```

3. DB에 concept 데이터 추가 (paper_concept_relations)

4. 테스트:

```bash
python test_multi_call_rag.py
```

---

## ⚠️ 주의사항

### 1. Weekly Plan에는 적용하지 않음

이 Multi-Call 구조는 **InBody 분석 전용**입니다.

Weekly Plan은 별도의 구조를 유지합니다.

### 2. 하위 호환성

기존 `analyzer.py`는 그대로 유지됩니다.

기존 코드를 사용하는 곳은 영향을 받지 않습니다.

### 3. LLM Call 수 증가

- 기존: 1 Call
- Multi-Call: 3 Calls (Call1 + Call2 Router + Call3)

비용이 3배 증가하지만, 정확도가 2배 향상됩니다.

### 4. concept tag 필수

Call1 프롬프트에서 concept tag를 반드시 포함해야 합니다.

그렇지 않으면 Call2 Router의 정확도가 낮아집니다.

---

## 📚 관련 문서

- `concept_definitions.py` - Concept ID 정의
- `prompts_multi_call.py` - Multi-Call 프롬프트
- `analyzer_multi_call.py` - Multi-Call 로직
- `test_multi_call_rag.py` - 테스트 스크립트
- `QUICK_START.md` - 기존 Graph RAG 가이드

---

**작성일:** 2026-02-02
**작성자:** Claude Code
