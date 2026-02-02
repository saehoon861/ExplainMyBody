# InBodyData 필드 매핑 이슈 및 수정 가이드

**작성일:** 2026-01-30
**분석 대상:** `backend/schemas/inbody.py` → `backend/services/llm/prompt_generator.py` 매핑

---

## 📊 전체 현황

**총 32개 필드 중 30개 사용 (93.75%)**

- ✅ 사용: 30개
- ❌ 미사용: 2개 (체중관리.체지방량, 연구항목.제지방량)

---

## 🔴 Critical Issues (즉시 수정 필요)

### Issue #1: OCR 섹션명 불일치

**파일:** `src/OCR/inbody_result_structured.json` vs `backend/schemas/inbody.py`

**현재 상황:**
```json
// OCR 출력 (inbody_result_structured.json)
{
  "기타": {                    // ❌ 문제!
    "제지방량": "57.1",
    "기초대사량": "1603",
    "권장섭취열량": "2267"
  }
}
```

```python
# Pydantic Schema (backend/schemas/inbody.py)
class InBodyData(BaseModel):
    연구항목: ResearchItems   # ❌ "기타"가 아닌 "연구항목"
```

**영향:**
- OCR 결과를 Pydantic으로 검증할 때 `KeyError` 또는 검증 실패
- `연구항목` 데이터 (기초대사량, 권장섭취열량, 제지방량) 전체 누락 가능

**수정 위치:**
- OCR 후처리 로직 (OCR 결과 → Pydantic 변환 사이)

**수정 코드:**
```python
# OCR result를 InBodyData로 변환하기 전에 전처리
def preprocess_ocr_result(ocr_result: dict) -> dict:
    """OCR 결과를 InBodyData 스키마에 맞게 전처리"""

    # "기타" → "연구항목" 변환
    if "기타" in ocr_result:
        ocr_result["연구항목"] = ocr_result.pop("기타")

    return ocr_result

# 사용 예시
ocr_result = json.load(...)  # OCR 결과 로드
ocr_result = preprocess_ocr_result(ocr_result)  # 전처리
inbody_data = InBodyData(**ocr_result)  # Pydantic 검증
```

---

### Issue #2: 체지방 필드 중복

**파일:** `backend/services/llm/prompt_generator.py` (line 180-181)

**현재 상황:**
```python
# Schema 정의 (backend/schemas/inbody.py)
class BodyComposition(BaseModel):
    체지방: Optional[float] = Field(None, gt=0, description="체지방 (kg)")

class WeightManagement(BaseModel):
    체지방량: Optional[float] = Field(None, gt=0, description="체지방량 (kg)")
```

```python
# Prompt Generator 현재 코드 (line 180-181)
if measurements.체성분.체지방:                    # ✅ 사용 중
    user_prompt_parts.append(f"- 체지방량: {measurements.체성분.체지방} kg")

# measurements.체중관리.체지방량은 완전히 무시됨!  # ❌ 미사용
```

**문제점:**
- 같은 데이터(20.6kg)가 두 필드에 중복 저장
- `체중관리.체지방량`은 Schema에 있지만 prompt에서 사용 안함
- 실제 InBody 기기 데이터가 어느 필드로 들어오는지 불명확
- 필드명 일관성 부족 (`체지방` vs `체지방량`)

**수정 위치:**
- `backend/services/llm/prompt_generator.py` (line 180-181)

**수정 코드 (Option 1: 우선순위 사용):**
```python
# line 180-181 수정
# 체중관리.체지방량 우선 사용 (더 명확한 이름)
if measurements.체중관리.체지방량:
    user_prompt_parts.append(f"- 체지방량: {measurements.체중관리.체지방량} kg")
elif measurements.체성분.체지방:  # fallback (하위 호환성)
    user_prompt_parts.append(f"- 체지방량: {measurements.체성분.체지방} kg")
```

**수정 코드 (Option 2: Schema 정리 - 더 근본적):**
```python
# backend/schemas/inbody.py 수정

# Option 2-1: 체성분.체지방 제거
class BodyComposition(BaseModel):
    체수분: Optional[float] = Field(None, gt=0, description="체수분 (L)")
    단백질: Optional[float] = Field(None, gt=0, description="단백질 (kg)")
    무기질: Optional[float] = Field(None, gt=0, description="무기질 (kg)")
    # 체지방: Optional[float] 제거 (체중관리.체지방량 사용)

# Option 2-2: 또는 체중관리.체지방량 제거
class WeightManagement(BaseModel):
    체중: float = Field(..., gt=10, lt=500, description="체중 (kg)")
    골격근량: float = Field(..., gt=0, lt=200, description="골격근량 (kg)")
    # 체지방량: Optional[float] 제거 (체성분.체지방 사용)
    적정체중: Optional[float] = Field(None, gt=0, description="적정체중 (kg)")
    # ...
```

**권장:** Option 2-1 (체성분.체지방 제거, 체중관리.체지방량만 유지)
- 이유: "체중관리" 섹션이 의미상 더 적절
- InBody 기기 화면에서도 "체중관리" 섹션에 체지방량 표시

---

## 🟡 Low Priority Issues (선택 사항)

### Issue #3: 미사용 필드 (제지방량)

**파일:** `backend/services/llm/prompt_generator.py`

**현재 상황:**
```python
# Schema에는 정의되어 있음
연구항목.제지방량: Optional[float] = Field(None, gt=0, description="제지방량 (kg)")

# 하지만 prompt_generator.py에서 사용하지 않음 ❌
```

**영향:**
- LLM 분석 시 제지방량 정보 누락
- 제지방량 = 체중 - 체지방량 (중요한 체성분 지표)

**수정 위치:**
- `backend/services/llm/prompt_generator.py` (line 199 이후)

**수정 코드:**
```python
# 대사 정보 섹션 (line 193-199) 이후 추가
user_prompt_parts.append("\n## 대사 정보")
if measurements.연구항목.기초대사량:
    user_prompt_parts.append(f"- 기초대사량: {measurements.연구항목.기초대사량} kcal")
if measurements.연구항목.권장섭취열량:
    user_prompt_parts.append(f"- 권장 섭취 열량: {measurements.연구항목.권장섭취열량} kcal")
if measurements.연구항목.제지방량:  # ✨ 추가
    user_prompt_parts.append(f"- 제지방량: {measurements.연구항목.제지방량} kg")
if measurements.체중관리.적정체중:
    user_prompt_parts.append(f"- 적정 체중: {measurements.체중관리.적정체중} kg")
```

---

## 📋 섹션별 필드 매핑 현황

### ✅ 완벽 매핑 (100%)

| 섹션 | 필드 수 | 사용 | 상태 |
|------|---------|------|------|
| 기본정보 | 3 | 3 | ✅ 완벽 |
| 체성분 | 4 | 4 | ✅ 완벽 (중복 이슈 있음) |
| 비만분석 | 5 | 5 | ✅ 완벽 |
| 부위별근육분석 | 5 | 5 | ✅ 완벽 |
| 부위별체지방분석 | 5 | 5 | ✅ 완벽 |

### ⚠️ 부분 매핑

| 섹션 | 필드 수 | 사용 | 미사용 필드 |
|------|---------|------|------------|
| 체중관리 | 7 | 6 | `체지방량` (중복) |
| 연구항목 | 3 | 2 | `제지방량` |

---

## 🎯 수정 우선순위

### 1️⃣ 즉시 수정 필요 (서비스 영향)

- [ ] **Issue #1**: OCR "기타" → "연구항목" 매핑 추가
  - 파일: OCR 후처리 로직
  - 영향: 전체 연구항목 데이터 누락 가능
  - 난이도: ⭐ (쉬움)

- [ ] **Issue #2**: 체지방 필드 중복 정리
  - 파일: `backend/services/llm/prompt_generator.py` 또는 `backend/schemas/inbody.py`
  - 영향: 데이터 일관성, 혼란 방지
  - 난이도: ⭐⭐ (보통)

### 2️⃣ 선택 사항 (품질 개선)

- [ ] **Issue #3**: 제지방량 필드 추가
  - 파일: `backend/services/llm/prompt_generator.py`
  - 영향: 분석 품질 향상
  - 난이도: ⭐ (쉬움)

---

## 🔍 검증 방법

### 1. OCR 매핑 검증
```python
# 테스트 코드
ocr_result = {
    "기본정보": {...},
    "기타": {  # "연구항목"이 아닌 "기타"
        "제지방량": "57.1",
        "기초대사량": "1603",
        "권장섭취열량": "2267"
    }
}

# 전처리 후
ocr_result = preprocess_ocr_result(ocr_result)

# Pydantic 검증 (에러 없어야 함)
try:
    inbody_data = InBodyData(**ocr_result)
    print("✅ 검증 성공")
except ValidationError as e:
    print(f"❌ 검증 실패: {e}")
```

### 2. Prompt 생성 검증
```python
# 체지방 필드 양쪽 모두 테스트
test_cases = [
    {"체성분": {"체지방": 20.6}, "체중관리": {"체지방량": None}},  # 체성분만
    {"체성분": {"체지방": None}, "체중관리": {"체지방량": 20.6}},   # 체중관리만
    {"체성분": {"체지방": 20.6}, "체중관리": {"체지방량": 20.6}},  # 둘 다
]

for case in test_cases:
    prompt = create_inbody_analysis_prompt(case)
    assert "체지방량" in prompt, "체지방량 필드 누락"
```

---

## 📚 참고 자료

### 관련 파일
- `backend/schemas/inbody.py` - Pydantic Schema 정의
- `backend/services/llm/prompt_generator.py` - Prompt 생성 로직
- `src/OCR/inbody_result_structured.json` - OCR 출력 예시

### 필드 매핑 현황
```
총 32개 필드:
  ✅ 사용: 30개 (93.75%)
  ❌ 미사용: 2개 (6.25%)
  ⚠️  중복: 1쌍 (체지방 관련)
```

---

**작성자 참고:** 이 문서는 코드 수정 없이 분석 결과만 정리한 것입니다. 실제 수정 시 위 가이드를 참고하여 진행하세요.
