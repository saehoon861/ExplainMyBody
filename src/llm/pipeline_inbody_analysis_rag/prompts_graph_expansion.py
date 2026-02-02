"""
Graph Expansion Pipeline용 프롬프트
- LLM은 글쓰기만 담당 (reasoning 없음)
- Rule-based Seed Extractor가 판정
- Graph Expansion Retriever가 Evidence 확장
- LLM은 자연어 리포트로 정리
"""

from typing import List, Dict, Optional


def create_report_writer_prompt(
    assessment_text: str,
    seed_concepts: List[str],
    risk_concepts: List[Dict[str, any]],
    intervention_concepts: List[Dict[str, any]],
    evidence_chunks: List[Dict[str, any]],
    previous_record: Optional[Dict] = None
) -> tuple[str, str]:
    """
    LLM Report Writer 프롬프트 (글쓰기만)

    Args:
        assessment_text: Rule-based로 생성된 체형 판정
        seed_concepts: 추출된 Seed concept IDs
        risk_concepts: Graph로 확장된 Risk concepts
        intervention_concepts: Graph로 확장된 Intervention concepts
        evidence_chunks: Graph에서 검색된 Evidence
        previous_record: 이전 InBody 기록

    Returns:
        (system_prompt, user_prompt)
    """

    system_prompt = """너는 ExplainMyBody 프로젝트의 리포트 작성 AI이다.

너의 역할:
- **글쓰기만 담당** (분석은 이미 완료됨)
- 제공된 체형 판정, 위험 요소, 처방을 자연어로 정리
- Evidence를 자연스럽게 문장 속에 녹임

규칙:
1. 논문 제목/저자/출처 언급 금지
2. Evidence는 "연구에 따르면..." 형식으로 자연스럽게
3. 의학적 확정 진단 금지 ("가능성", "위험" 수준)
4. 제공된 정보만 사용 (추가 분석/판단 금지)
5. 지정된 출력 형식 준수

**중요: 너는 분석을 하지 않는다. 이미 분석된 결과를 글로 정리할 뿐이다.**
"""

    user_prompt_parts = []

    user_prompt_parts.append("다음은 이미 분석된 InBody 정보이다. 이를 자연어 리포트로 정리하라.\n")
    user_prompt_parts.append("=" * 70)
    user_prompt_parts.append("\n")

    # (1) 체형 판정 (Rule-based)
    user_prompt_parts.append("## (1) 체형 판정 결과 (Rule-based 분석 완료)\n")
    user_prompt_parts.append(assessment_text)
    user_prompt_parts.append("\n\n")

    # (2) Seed Concepts
    user_prompt_parts.append("## (2) 추출된 Seed Concepts\n")
    user_prompt_parts.append(f"Seed: {', '.join(seed_concepts)}\n")
    user_prompt_parts.append("\n")

    # (3) Risk Concepts (Graph 확장)
    user_prompt_parts.append("## (3) Graph 확장된 건강 위험 요소\n")
    if risk_concepts:
        for risk in risk_concepts[:5]:
            concept_id = risk.get("concept_id", "N/A")
            paper_count = risk.get("paper_count", 0)
            user_prompt_parts.append(f"- {concept_id} (논문 {paper_count}개에서 발견)\n")
    else:
        user_prompt_parts.append("검색된 위험 요소 없음\n")
    user_prompt_parts.append("\n")

    # (4) Intervention Concepts (Graph 확장)
    user_prompt_parts.append("## (4) Graph 확장된 처방/개선 방법\n")
    if intervention_concepts:
        for intervention in intervention_concepts[:5]:
            concept_id = intervention.get("concept_id", "N/A")
            paper_count = intervention.get("paper_count", 0)
            user_prompt_parts.append(f"- {concept_id} (논문 {paper_count}개에서 발견)\n")
    else:
        user_prompt_parts.append("검색된 처방 없음\n")
    user_prompt_parts.append("\n")

    # (5) Evidence Chunks
    user_prompt_parts.append("## (5) 과학적 근거 (Evidence)\n")
    if evidence_chunks:
        for i, chunk in enumerate(evidence_chunks[:5], 1):
            concept_id = chunk.get("concept_id", "N/A")
            evidence = chunk.get("evidence", "")
            user_prompt_parts.append(f"\n[Evidence {i}] (concept: {concept_id})\n")
            user_prompt_parts.append(f"{evidence}\n")
    else:
        user_prompt_parts.append("검색된 Evidence 없음\n")
    user_prompt_parts.append("\n")

    # (6) 이전 기록
    if previous_record:
        user_prompt_parts.append("## (6) 이전 InBody 기록\n")
        user_prompt_parts.append(str(previous_record))
        user_prompt_parts.append("\n\n")

    user_prompt_parts.append("=" * 70)
    user_prompt_parts.append("\n\n")

    # 출력 형식
    output_format = """
위 정보를 아래 형식으로 정리하라.

**중요: 분석하지 마라. 제공된 정보를 자연어로 정리만 하라.**

==============================

[인바디 분석 요약] (5줄)

✅ 체형: (체형 판정 결과 요약)
✅ 근육: (근육 상태 요약)
✅ 지방: (지방 상태 요약)
✅ 건강 위험: (Risk concepts를 자연어로)
✅ 운동/식단 핵심: (Intervention concepts를 자연어로)

---

📋 [상세 분석 리포트]

### 1. 이전 기록과 비교 (3~5줄)

(이전 기록이 없으면 "첫 측정입니다"로 시작)

### 2. 개선 방향 (약 10줄)

**근육 개선:**
(Seed + Intervention concepts 기반 서술)

**지방 관리:**
(Seed + Intervention concepts 기반 서술)

**생활습관:**
(종합 조언)

※ Evidence를 자연스럽게 문장 속에 포함 (최소 2개)
   예: "연구에 따르면 저항성 운동은 골격근량 증가에 효과적입니다..."

---

### 3. 건강 특이사항 및 주의 포인트 (~10줄)

**주요 위험 요소:**
(Risk concepts를 자연어로 풀어서 설명)

**부위별 불균형:**
(부위별 불균형 내용)

※ Evidence 기반 위험 설명 포함
   예: "내장지방 증가는 인슐린 저항성과 관련될 수 있습니다..."

---

### 4. 맞춤 솔루션 요약 (마무리 문단)

(Intervention concepts 기반 종합 조언)

==============================

**다시 강조: 너는 분석하지 않는다. 제공된 정보를 글로 정리할 뿐이다.**
논문 제목/저자는 절대 언급하지 마라.
Evidence는 "연구에 따르면..." 형식으로만 녹여라.
"""

    user_prompt_parts.append(output_format)

    user_prompt = "".join(user_prompt_parts)

    return system_prompt, user_prompt


def format_evidence_list(evidence_chunks: List[Dict[str, any]]) -> str:
    """
    Evidence 리스트를 읽기 좋게 포맷팅

    Args:
        evidence_chunks: Evidence chunk 리스트

    Returns:
        포맷팅된 문자열
    """
    if not evidence_chunks:
        return "검색된 Evidence 없음"

    lines = []

    for i, chunk in enumerate(evidence_chunks, 1):
        concept_id = chunk.get("concept_id", "N/A")
        evidence = chunk.get("evidence", "")
        title = chunk.get("title", "N/A")
        year = chunk.get("year", "N/A")

        lines.append(f"\n[Evidence {i}] {concept_id}")
        lines.append(f"Title: {title} ({year})")
        lines.append(f"Content: {evidence}\n")

    return "\n".join(lines)
