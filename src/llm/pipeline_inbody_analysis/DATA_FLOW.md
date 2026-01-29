# InBody 분석 파이프라인 - 데이터 흐름

## 📊 전체 흐름도

```
┌─────────────────────┐
│  1. OCR 입력 데이터  │
│   (JSON 파일)       │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  2. Pydantic 검증   │
│ InBodyMeasurements  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  3. DB 저장 (1차)   │
│  health_records     │
│  measurements JSONB │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  4. LLM 프롬프트    │
│     생성            │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  5. LLM 분석 생성   │
│  (자연어 텍스트)    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  6. DB 저장 (2차)   │
│ inbody_analysis_    │
│      reports        │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  7. 임베딩 생성     │
│ (OpenAI + Ollama)   │
│     (선택사항)      │
└─────────────────────┘
```

---

## 1️⃣ OCR 입력 데이터 (JSON)

### 입력 형식
```json
{
  "성별": "남자",
  "나이": 30,
  "신장": 175.0,
  "체중": 75.0,
  "무기질": 3.5,
  "체수분": 42.0,
  "단백질": 12.5,
  "체지방": 18.0,
  "골격근량": 35.0,
  "BMI": 24.5,
  "체지방률": 24.0,
  "복부지방률": 0.88,
  "내장지방레벨": 9,
  "기초대사량": 1650,
  "비만도": 105,
  "적정체중": 68.0,
  "권장섭취열량": 2200,
  "체중조절": -7.0,
  "지방조절": -5.0,
  "근육조절": 2.0,
  "근육_부위별등급": {
    "왼팔": "표준",
    "오른팔": "표준",
    "몸통": "표준미만",
    "왼다리": "표준이상",
    "오른다리": "표준이상"
  },
  "체지방_부위별등급": {
    "왼팔": "표준",
    "오른팔": "표준",
    "몸통": "과다",
    "왼다리": "표준",
    "오른다리": "표준"
  },
  "body_type1": "근육부족형",
  "body_type2": "복부비만형"
}
```

### 주요 필드 설명

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `성별` | str | ✅ | "남자" 또는 "여자" |
| `나이` | int | ✅ | 1-120 |
| `신장` | float | ✅ | cm 단위 |
| `체중` | float | ✅ | kg 단위 |
| `골격근량` | float | ✅ | kg 단위 |
| `BMI` | float | ✅ | 체질량지수 |
| `체지방률` | float | ✅ | % 단위 |
| `근육_부위별등급` | dict | ✅ | 왼팔, 오른팔, 몸통, 왼다리, 오른다리 |
| `체지방_부위별등급` | dict | ❌ | 부위별 체지방 등급 (선택) |
| `body_type1` | str | ❌ | **1차 체형 분류 (외부 입력)** |
| `body_type2` | str | ❌ | **2차 체형 분류 (외부 입력)** |

**⚠️ 중요:**
- `body_type1`, `body_type2`는 **외부에서 입력**받는 값입니다
- 파이프라인 내부에서 규칙 기반 계산을 하지 않습니다
- 값이 없으면 `null` 또는 생략 가능

---

## 2️⃣ Pydantic 검증 (InBodyMeasurements)

### 코드 위치
`shared/models.py` - `InBodyMeasurements` 클래스

### 검증 과정
```python
from shared.models import InBodyMeasurements

# JSON → Pydantic 모델
measurements = InBodyMeasurements(**measurements_dict)
```

### 검증 항목
- ✅ 필수 필드 존재 여부
- ✅ 데이터 타입 검증
- ✅ 값의 범위 검증 (나이: 1-120, 신장: 100-250 등)
- ✅ JSONB 구조 검증

**검증 실패 시**: `ValidationError` 예외 발생 → 사용자에게 에러 반환

---

## 3️⃣ DB 저장 (1차) - health_records 테이블

### 테이블 구조
```sql
CREATE TABLE health_records (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    record_date TIMESTAMP DEFAULT NOW(),
    measurements JSONB NOT NULL,  -- ← InBody 측정 데이터 전체
    source VARCHAR(50) DEFAULT 'manual'
);
```

### 저장 코드
```python
# analyzer.py
m = measurements.model_dump()  # Pydantic → dict
record_id = self.db.save_health_record(
    user_id=user_id,
    measurements=m,
    source=source,
)
```

### measurements JSONB에 저장되는 내용
```json
{
  "성별": "남자",
  "나이": 30,
  "신장": 175.0,
  "체중": 75.0,
  ...
  "근육_부위별등급": {...},
  "체지방_부위별등급": {...},
  "body_type1": "근육부족형",
  "body_type2": "복부비만형"
}
```

**💡 핵심:**
- `body_type1`, `body_type2`가 **measurements JSONB에 포함**되어 저장됨
- 이후 LLM 프롬프트 생성 시 이 데이터를 그대로 사용

---

## 4️⃣ LLM 프롬프트 생성

### 코드 위치
`pipeline_inbody_analysis/prompt_generator.py` - `create_inbody_analysis_prompt()`

### 프롬프트 구조

**System Prompt:**
- 인바디 분석가 역할 정의
- 분석 항목 및 출력 형식 가이드

**User Prompt:**
```
# InBody 측정 데이터

## 기본 정보
- 성별: 남자
- 나이: 30세
- 신장: 175.0 cm
- 체중: 75.0 kg

## 체성분 분석
- BMI: 24.5
- 체지방률: 24.0%
- 골격근량: 35.0 kg
...

## 부위별 근육 등급
- 왼팔: 표준
- 오른팔: 표준
- 몸통: 표준미만
- 왼다리: 표준이상
- 오른다리: 표준이상

## 부위별 체지방 등급
- 왼팔: 표준
- 오른팔: 표준
- 몸통: 과다
- 왼다리: 표준
- 오른다리: 표준

## 체형 분류
- Body Type 1: 근육부족형
- Body Type 2: 복부비만형
```

**💡 핵심:**
- `measurements` 객체에서 직접 `body_type1`, `body_type2`를 읽어서 프롬프트에 포함
- LLM은 이 정보를 참고하여 분석 텍스트 생성

---

## 5️⃣ LLM 분석 생성

### 코드
```python
# analyzer.py
system_prompt, user_prompt = create_inbody_analysis_prompt(measurements)
analysis_text = self.llm_client.generate_chat(system_prompt, user_prompt)
```

### LLM 출력 예시 (자연어 텍스트)
```
### [종합 체형 평가]
현재 체형은 BMI 24.5로 정상 범위에 있으나, 체지방률 24%로 다소 높은 편입니다.
골격근량이 35.0kg으로 체중 대비 부족하며, 특히 몸통 근육이 표준 미달입니다.

주요 특징:
1. 근육부족형 - 전체적인 근육량 증가 필요
2. 복부비만형 - 몸통 체지방 과다, 내장지방 레벨 9
3. 상하체 불균형 - 하체는 양호하나 상체 및 몸통 약함

### [체성분 상세 분석]
**체지방 분석**
체지방률 24%는 30세 남성 기준 정상 상한선을 초과합니다...

[... 상세 분석 계속 ...]

### [체형 분류 해석]
**Body Type 1: 근육부족형**
전체 골격근량이 표준 대비 부족하며, 특히 몸통 근육이 취약합니다...

**Body Type 2: 복부비만형**
내장지방 레벨 9로 주의가 필요한 수준이며, 복부지방률 0.88은...
```

---

## 6️⃣ DB 저장 (2차) - inbody_analysis_reports 테이블

### 테이블 구조
```sql
CREATE TABLE inbody_analysis_reports (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    record_id INTEGER NOT NULL REFERENCES health_records(id),
    report_date TIMESTAMP DEFAULT NOW(),
    llm_output TEXT NOT NULL,  -- ← LLM 생성 자연어 분석 텍스트
    model_version VARCHAR(100),
    embedding_1536 vector(1536),  -- OpenAI 임베딩
    embedding_1024 vector(1024)   -- Ollama bge-m3 임베딩
);
```

### 저장 코드
```python
# analyzer.py
analysis_id = self.db.save_analysis_report(
    user_id=user_id,
    record_id=record_id,
    llm_output=analysis_text,
    model_version=self.model_version,
)
```

**💡 핵심:**
- `llm_output`에 LLM이 생성한 자연어 분석 텍스트 저장
- `record_id`로 원본 측정 데이터(`health_records`)와 연결
- 임베딩은 아직 생성 전 (null)

---

## 7️⃣ 임베딩 생성 (선택사항)

### 코드 위치
`pipeline_inbody_analysis/embedder.py` - `InBodyEmbedder`

### 생성 과정
```python
# main.py
if enable_embedding:
    embedder = InBodyEmbedder(db, llm_client)
    embedding = embedder.create_and_save_embedding(
        result["analysis_id"],
        result["analysis_text"]
    )
```

### 이중 임베딩 시스템

**1. OpenAI text-embedding-3-small (1536D)**
```python
openai_client = OpenAIClient()
embedding_1536 = openai_client.create_embedding(text=analysis_text)
```

**2. Ollama bge-m3 (1024D)**
```python
ollama_client = OllamaClient(embedding_model="bge-m3:latest")
embedding_1024 = ollama_client.create_embedding(text=analysis_text)
```

### DB 업데이트
```python
# embedder.py
self.db.update_analysis_embedding(
    analysis_id,
    embedding_1536=embedding_1536,
    embedding_1024=embedding_1024,
)
```

**💡 핵심:**
- 분석 텍스트(`llm_output`)를 벡터로 변환
- 두 가지 임베딩을 동시에 생성하여 저장
- 이후 주간 계획 생성 시 Vector RAG에 사용

---

## 📋 데이터 조회 흐름 (LLM으로 전달되는 과정)

### OCR → DB → LLM 상세 흐름

```
1. OCR 데이터 (JSON)
   └─> measurements_dict = {..., "body_type1": "근육부족형", "body_type2": "복부비만형"}

2. Pydantic 검증
   └─> measurements = InBodyMeasurements(**measurements_dict)
       └─> measurements.body_type1 = "근육부족형"
       └─> measurements.body_type2 = "복부비만형"

3. DB 저장 (health_records)
   └─> m = measurements.model_dump()
       └─> {"성별": "남자", ..., "body_type1": "근육부족형", "body_type2": "복부비만형"}
       └─> DB INSERT measurements JSONB

4. LLM 프롬프트 생성
   └─> user_prompt += f"- Body Type 1: {measurements.body_type1}"
       └─> "- Body Type 1: 근육부족형"
   └─> user_prompt += f"- Body Type 2: {measurements.body_type2}"
       └─> "- Body Type 2: 복부비만형"

5. LLM 호출
   └─> llm_client.generate_chat(system_prompt, user_prompt)
       └─> User Prompt에 포함됨:
           """
           ## 체형 분류
           - Body Type 1: 근육부족형
           - Body Type 2: 복부비만형
           """

6. LLM 분석 생성
   └─> analysis_text = "### [체형 분류 해석]\n**Body Type 1: 근육부족형**\n..."
```

---

## 🔍 주요 변경사항 (규칙기반 제거 후)

### ❌ 삭제된 것들

1. **규칙 기반 알고리즘 import**
   ```python
   # analyzer.py (삭제됨)
   from rule_based_bodytype.body_analysis.pipeline import BodyCompositionAnalyzer
   ```

2. **BodyCompositionAnalyzer 인스턴스**
   ```python
   # analyzer.py (삭제됨)
   self.body_analyzer = BodyCompositionAnalyzer()
   ```

3. **calculate_stages() 메서드**
   ```python
   # analyzer.py (삭제됨)
   def calculate_stages(self, measurements: InBodyMeasurements) -> Dict[str, str]:
       stage_results = self.body_analyzer.analyze_full_pipeline(body_data)
       return {"stage2": ..., "stage3": ...}
   ```

4. **Pydantic 모델의 stage 필드**
   ```python
   # shared/models.py (삭제됨)
   stage2_근육보정체형: Optional[str] = None
   stage3_상하체밸런스: Optional[str] = None
   ```

### ✅ 추가된 것들

1. **Pydantic 모델에 body_type 필드**
   ```python
   # shared/models.py (추가됨)
   body_type1: Optional[str] = Field(None, description="1차 체형 분류")
   body_type2: Optional[str] = Field(None, description="2차 체형 분류")
   ```

2. **외부 입력 체형 정보 확인**
   ```python
   # analyzer.py (추가됨)
   if measurements.body_type1:
       print_and_capture(f"  ✓ Body Type 1: {measurements.body_type1}")
   if measurements.body_type2:
       print_and_capture(f"  ✓ Body Type 2: {measurements.body_type2}")
   ```

3. **프롬프트 생성 시 body_type 사용**
   ```python
   # prompt_generator.py (수정됨)
   if measurements.body_type1 or measurements.body_type2:
       user_prompt_parts.append("\n## 체형 분류")
       if measurements.body_type1:
           user_prompt_parts.append(f"- Body Type 1: {measurements.body_type1}")
       if measurements.body_type2:
           user_prompt_parts.append(f"- Body Type 2: {measurements.body_type2}")
   ```

---

## 💾 DB 스키마 확인

### health_records.measurements JSONB 구조

```json
{
  "성별": "남자",
  "나이": 30,
  "신장": 175.0,
  "체중": 75.0,
  "무기질": 3.5,
  "체수분": 42.0,
  "단백질": 12.5,
  "체지방": 18.0,
  "골격근량": 35.0,
  "BMI": 24.5,
  "체지방률": 24.0,
  "복부지방률": 0.88,
  "내장지방레벨": 9,
  "기초대사량": 1650,
  "비만도": 105,
  "적정체중": 68.0,
  "권장섭취열량": 2200,
  "체중조절": -7.0,
  "지방조절": -5.0,
  "근육조절": 2.0,
  "근육_부위별등급": {
    "왼팔": "표준",
    "오른팔": "표준",
    "몸통": "표준미만",
    "왼다리": "표준이상",
    "오른다리": "표준이상"
  },
  "체지방_부위별등급": {
    "왼팔": "표준",
    "오른팔": "표준",
    "몸통": "과다",
    "왼다리": "표준",
    "오른다리": "표준"
  },
  "body_type1": "근육부족형",
  "body_type2": "복부비만형"
}
```

### JSONB 쿼리 예시

```sql
-- body_type1 조회
SELECT measurements->>'body_type1' AS body_type1
FROM health_records
WHERE user_id = 2;

-- body_type1이 '근육부족형'인 레코드 검색
SELECT *
FROM health_records
WHERE measurements->>'body_type1' = '근육부족형';
```

---

## 🚀 실행 예시

```bash
uv run python pipeline_inbody_analysis/main.py \
  --user-id 2 \
  --measurements-file sample_inbody_data.json \
  --model gpt-4o-mini \
  --enable-embedding \
  --output-file output1.txt
```

### 출력 흐름
```
============================================================
InBody 분석 시작 (User ID: 2)
============================================================

📊 1단계: 체형 정보 확인...
  ✓ Body Type 1: 근육부족형
  ✓ Body Type 2: 복부비만형

💾 2단계: 측정 데이터 저장...
  ✓ Record ID: 123

🤖 3단계: LLM 분석 생성...
  - LLM 호출 중...
  ✓ 분석 완료 (2847 글자)

💾 4단계: 분석 결과 저장...
  ✓ Analysis ID: 456

============================================================
✨ InBody 분석 완료!
============================================================

🔢 임베딩 생성 중...
  ✓ OpenAI 임베딩 생성 완료 (차원: 1536)
  ✓ Ollama bge-m3 임베딩 생성 완료 (차원: 1024)
  ✓ DB 저장 완료

============================================================
📋 분석 결과
============================================================
✅ 성공!
   - Record ID: 123
   - Analysis ID: 456

[LLM이 생성한 자연어 분석 텍스트 출력...]

💾 결과 저장 완료: /home/user/projects/ExplainMyBody/llm/pipeline_inbody_analysis/output1.txt
```

---

## 📝 요약

### 핵심 포인트

1. **외부 입력**: `body_type1`, `body_type2`는 JSON 입력에서 받음
2. **규칙기반 없음**: 파이프라인 내부에서 체형 계산 안 함
3. **DB 저장**: measurements JSONB에 body_type1/2 포함되어 저장
4. **LLM 사용**: 프롬프트에 body_type1/2가 포함되어 LLM이 해석
5. **임베딩**: LLM 분석 텍스트를 벡터화하여 RAG에 활용

### 데이터 흐름 요약

```
OCR JSON (body_type1/2 포함)
  → Pydantic 검증
    → DB 저장 (measurements JSONB)
      → LLM 프롬프트 생성 (body_type1/2 포함)
        → LLM 분석 생성 (자연어)
          → DB 저장 (llm_output)
            → 임베딩 생성 (선택)
              → 주간 계획 RAG에 활용
```
