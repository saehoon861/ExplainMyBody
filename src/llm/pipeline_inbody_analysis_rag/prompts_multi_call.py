"""
Multi-Call 자연어 기반 InBody 분석 프롬프트
- Call1: 체형 판정 (자연어, 운동/식단 제외)
- Call2 Router: 자연어 → concept_id 추출
- Call3: 최종 리포트 (Evidence 통합)
"""

from typing import Tuple, List, Optional
from shared.models import InBodyMeasurements
from .concept_definitions import get_concept_list_for_router_prompt, format_concept_with_tag


# ==================== CALL 1: 체형 판정 ====================

def create_body_assessment_prompt(
    measurements: InBodyMeasurements
) -> Tuple[str, str]:
    """
    Call1: 체형 판정 프롬프트 (자연어 출력, 운동/식단 추천 없음)

    Args:
        measurements: InBody 측정 데이터

    Returns:
        (system_prompt, user_prompt)
    """

    system_prompt = """너는 ExplainMyBody 프로젝트의 체성분 판정 엔진이다.

너의 역할은 사용자의 InBody 측정 데이터를 기반으로
현재 체형 상태를 "자연어 판정 리포트"로 요약하는 것이다.

규칙:

- 운동/식단 추천은 절대 하지 마라
- 논문 근거를 언급하지 마라
- BMI, 체지방률, 골격근량, 내장지방레벨을 중심으로 판정하라
- 성별/연령 기반 위험 가능성을 key_risks로 포함하라
- 출력은 반드시 아래 형식의 자연어 텍스트로 작성하라
- 불필요한 장문 설명 없이 판정만 간결하게 작성하라

**중요: key_risks에는 concept tag를 함께 포함하라**

예시:
- 내장지방 위험: 주의 (concept: visceral_fat_metabolic_risk)
- 근감소증 위험 증가 가능성 (concept: sarcopenia_risk)

이렇게 concept tag를 포함하면 이후 논문 검색 정확도가 2배 향상된다.
"""

    user_prompt_parts = []

    user_prompt_parts.append("다음은 DB에서 불러온 사용자 InBody 측정 데이터이다.\n")
    user_prompt_parts.append("health_records.measurements:\n")

    # 기본 정보
    user_prompt_parts.append("## 기본 정보")
    user_prompt_parts.append(f"- 성별: {measurements.성별}")
    user_prompt_parts.append(f"- 나이: {measurements.나이}세")
    user_prompt_parts.append(f"- 신장: {measurements.신장} cm")
    user_prompt_parts.append(f"- 체중: {measurements.체중} kg")

    # 체성분
    user_prompt_parts.append("\n## 체성분")
    user_prompt_parts.append(f"- BMI: {measurements.BMI}")
    user_prompt_parts.append(f"- 체지방률: {measurements.체지방률}%")
    user_prompt_parts.append(f"- 골격근량: {measurements.골격근량} kg")
    if measurements.내장지방레벨:
        user_prompt_parts.append(f"- 내장지방레벨: {measurements.내장지방레벨}")

    # 부위별
    user_prompt_parts.append("\n## 부위별 근육 등급")
    for part, grade in measurements.근육_부위별등급.items():
        user_prompt_parts.append(f"- {part}: {grade}")

    if measurements.체지방_부위별등급:
        user_prompt_parts.append("\n## 부위별 체지방 등급")
        for part, grade in measurements.체지방_부위별등급.items():
            user_prompt_parts.append(f"- {part}: {grade}")

    # 체형 분류
    if measurements.body_type1 or measurements.body_type2:
        user_prompt_parts.append("\n## 체형 분류")
        if measurements.body_type1:
            user_prompt_parts.append(f"- Body Type 1: {measurements.body_type1}")
        if measurements.body_type2:
            user_prompt_parts.append(f"- Body Type 2: {measurements.body_type2}")

    user_prompt_parts.append("\n---\n")
    user_prompt_parts.append("위 데이터를 기반으로 아래 형식으로 체형 판정을 출력하라.\n")
    user_prompt_parts.append("---\n\n")

    # 출력 형식
    output_format = """[체형 판정 결과]

- 체형 유형: (예: 표준 체형 / 근육 부족형 / 비만형 등)

- 근육 상태: (부족/정상/과다 중 하나로 판정)

- 지방 상태: (부족/정상/과다 중 하나로 판정)

- 내장지방 위험도: (낮음/주의/높음 중 하나로 판정)

- 부위별 불균형:
  (예: 상체 근육 부족, 하체 지방 집중 등)

- key_risks (성별/연령 기반 건강 위험 가능성):
  **중요: 각 위험에 concept tag를 반드시 포함하라**
  예:
  - 내장지방 과다로 인한 대사질환 위험 (concept: visceral_fat_metabolic_risk)
  - 근육량 감소로 인한 근감소증 위험 (concept: sarcopenia_risk)
  - 복부비만 패턴 (concept: abdominal_obesity_risk)

- priority_focus (가장 우선적으로 개선해야 할 방향):
  (예: 근육 증가 필요, 복부 지방 관리 필요 등)

---

운동 방법이나 식단 조언은 절대 작성하지 마라.
상태 판정만 출력하라.
"""

    user_prompt_parts.append(output_format)

    user_prompt = "\n".join(user_prompt_parts)

    return system_prompt, user_prompt


# ==================== CALL 2 Router: 자연어 → concept_id ====================

def create_concept_router_prompt(
    body_assessment_text: str
) -> Tuple[str, str]:
    """
    Call2 Router: 자연어 판정문에서 concept_id 추출

    Args:
        body_assessment_text: Call1에서 생성된 체형 판정 자연어

    Returns:
        (system_prompt, user_prompt)
    """

    concept_list = get_concept_list_for_router_prompt()

    system_prompt = f"""너는 ExplainMyBody 프로젝트의 Graph RAG 검색 라우터이다.

너의 역할은 Call1에서 생성된 체형 판정 자연어를 읽고,
관련된 논문 근거를 검색하기 위한 concept_id 리스트를 생성하는 것이다.

규칙:

- 출력은 반드시 concept_id 배열(JSON)만 가능
- 설명 문장 금지
- 최소 3개, 최대 6개 concept_id 선택
- 아래 범주에서 우선 선택하라:

{concept_list}

**중요: 판정문에 (concept: xxx) 태그가 있으면 해당 concept_id를 우선 포함하라**

출력 예시:
["visceral_fat_metabolic_risk", "resistance_training", "high_protein_intake", "sarcopenia_risk"]
"""

    user_prompt = f"""다음은 사용자 체형 판정 결과이다.

{body_assessment_text}

이 판정문을 기반으로 Graph RAG 검색에 사용할 concept_id 리스트를 JSON 배열로 출력하라.

판정문에 (concept: xxx) 형태의 태그가 있으면 해당 concept_id를 반드시 포함하라.
"""

    return system_prompt, user_prompt


# ==================== CALL 3: 최종 리포트 ====================

def create_final_report_prompt(
    body_assessment_text: str,
    evidence_chunks: List[dict],
    previous_record: Optional[dict] = None
) -> Tuple[str, str]:
    """
    Call3: 최종 리포트 생성 (자연어 판정 + Evidence 통합)

    Args:
        body_assessment_text: Call1 체형 판정 자연어
        evidence_chunks: Graph RAG 검색된 논문 chunks
        previous_record: 이전 InBody 기록 (선택)

    Returns:
        (system_prompt, user_prompt)
    """

    system_prompt = """너는 ExplainMyBody 프로젝트의 인바디 분석 리포트 작성 AI이다.

너의 역할은:

- Call1에서 생성된 체형 판정 자연어
- Graph RAG에서 검색된 연구 근거 Evidence Context

를 기반으로 최종 맞춤 리포트를 작성하는 것이다.

규칙:

1. 논문 제목, 저자, 출처는 절대 언급하지 마라
2. Evidence는 자연스럽게 문장 속 근거로만 녹여라
   - 나쁜 예: "[논문1]에 따르면..."
   - 좋은 예: "연구에 따르면 내장지방 증가는 인슐린 저항성과 관련됨..."
3. 의학적 확정 진단 금지 ("위험 가능성", "관련될 수 있음" 수준)
4. 사용자가 원하는 출력 형식을 반드시 지켜라
5. Summary는 5줄, 상세 내용은 지정 길이로 작성하라
"""

    user_prompt_parts = []

    user_prompt_parts.append("다음은 사용자 분석에 필요한 입력이다.\n")
    user_prompt_parts.append("---\n")

    # (1) 체형 판정 결과
    user_prompt_parts.append("(1) 체형 판정 결과 (Call1 자연어)\n")
    user_prompt_parts.append(body_assessment_text)
    user_prompt_parts.append("\n---\n")

    # (2) Graph RAG Evidence
    user_prompt_parts.append("(2) Graph RAG Evidence Context\n")
    if evidence_chunks:
        for i, chunk in enumerate(evidence_chunks, 1):
            concept = chunk.get("concept_id", "N/A")
            evidence = chunk.get("chunk_ko_summary") or chunk.get("chunk_text", "")[:300]
            user_prompt_parts.append(f"\n[Evidence {i}] (concept: {concept})")
            user_prompt_parts.append(evidence)
    else:
        user_prompt_parts.append("검색된 Evidence가 없습니다.")
    user_prompt_parts.append("\n---\n")

    # (3) 이전 기록
    if previous_record:
        user_prompt_parts.append("(3) 이전 InBody 기록 (비교용)\n")
        user_prompt_parts.append(str(previous_record))
        user_prompt_parts.append("\n---\n")

    # 출력 형식
    output_format = """
아래 형식으로 최종 리포트를 작성하라.

==============================

[인바디 분석 요약] (5줄)

✅ 체형: (한 줄 요약)
✅ 근육: (한 줄 요약)
✅ 지방: (한 줄 요약)
✅ 건강 위험: (한 줄 요약)
✅ 운동/식단 핵심: (한 줄 방향성만)

---

📋 [상세 분석 리포트]

### 1. 이전 기록과 비교 (3~5줄)

(이전 기록이 없으면 "첫 측정입니다"로 시작)

### 2. 개선사항 (약 10줄)
- 근육 개선 방향
- 지방 관리 방향
- 생활습관 개선 방향

※ Evidence 기반 과학적 근거 문장을 최소 2개 자연스럽게 포함할 것
   (논문 번호 언급 금지, "연구에 따르면..." 형식 사용)

---

### 3. 건강 특이사항 및 주의 포인트 (~10줄)
- 내장지방 위험
- 복부비만 관련 위험 가능성
- 연령 기반 근감소증 가능성
- 부위별 불균형

※ Evidence 기반 위험요소 설명 포함

---

### 4. 맞춤 솔루션 요약 문단 (마무리)

==============================

출력은 리포트 텍스트만 작성하라.
"""

    user_prompt_parts.append(output_format)

    user_prompt = "\n".join(user_prompt_parts)

    return system_prompt, user_prompt
