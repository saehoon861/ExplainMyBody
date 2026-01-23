# 대화 원본 기록

---

## User:
```
Profile: 김철수 (표준 체형 - 균형잡힌 일반 성인 남성)
============================================================
[1/2] Rule-based body analysis...
  BMI: 23.5 (과체중)
  Stage1: 근육형
  Stage2: 근육형
  Stage3: 표준형
[2/2] LLM recommendation generation...
[Warning] No JSON block found
[Debug] Full response:
### 주간 피드백: 28세 남자 (체중 72.0kg, BMI 23.5)

---

#### **1. 수행률 및 성실도 분석**
- **운동 계획 대비 수행률**:
  - **완료율**: 75% (예: 4일 중 3일 운동 완료, 1일 중간 중단, 1일 미 수행).
...
  [Warning] Failed or validation error
  Saved: outputs/김철수_20260121_161212.json
```

---

## Assistant:
LLM 응답이 JSON이 아닌 마크다운 텍스트를 출력함. `{`가 없어서 JSON 파싱 실패.

---

## User:
이거 ollama모델 바꾸는거 ollama_client.py에서 model: =" 여기만 바꾸면돼?

#### 5. 문제점 및 개선 방안
- **운동 중 어려움**: 푸시업 10회 후 근육...
  [Warning] Failed or validation error
  Saved: outputs/송민재_20260121_162231.json
============================================================ 이 오류 나는데 모델 8b라서 용량 부족이야? 다른 모델은 어때? qwen 14b나 exaone? 다른 모델 추천해줄거있어?

---

## Assistant:
모델 변경 방법과 추천 모델 알려줄게.

## 모델 변경 방법

### 1. `ollama_client.py`에서 기본값 변경
```python
def __init__(self, base_url: str = "http://localhost:11434", model: str = "qwen3:8b"):
```
여기서 `"qwen3:8b"` → `"exaone3.5:7.8b"` 등으로 변경

### 2. `run_pipeline.py`에서 클라이언트 생성 시 지정
```python
client = OllamaClient(model="exaone3.5:7.8b")
```

## 문제 원인
qwen3:8b가 JSON 대신 마크다운(`#### 5. 문제점...`)을 출력함. 모델이 JSON 형식 지시를 제대로 따르지 않는 것.

## 추천 모델

| 모델 | 크기 | 특징 |
|------|------|------|
| **exaone3.5:7.8b** | 7.8B | 한국어 특화, LG AI Research |
| **qwen2.5:14b** | 14B | qwen3보다 JSON 출력 안정적 |
| **llama3.1:8b** | 8B | JSON 형식 잘 따름 |
| **gemma2:9b** | 9B | 구조화 출력 우수 |
| **mistral:7b** | 7B | 지시 따르기 우수 |

## 내 추천
한국어 컨텐츠니까 **exaone3.5:7.8b** 먼저 시도해봐:

```bash
# 모델 다운로드
ollama pull exaone3.5:7.8b

# 또는 qwen2.5:14b
ollama pull qwen2.5:14b
```

모델 기본값 바꿔줄까?

---

## User:
```
============================================================
Profile: 김철수 (표준 체형 - 균형잡힌 일반 성인 남성)
============================================================
[1/2] Rule-based body analysis...
  BMI: 23.5 (과체중)
  Stage1: 근육형
  Stage2: 근육형
  Stage3: 표준형
[2/2] LLM recommendation generation...
[Warning] No JSON block found
[Debug] Full response:
### 주간 피드백: 28세 남자 (체중 72.0kg, BMI 23.5)
...
```
이거 no json block found 이유?

---

## Assistant:
## 원인

LLM 응답을 보면:
```
### 주간 피드백: 28세 남자 (체중 72.0kg, BMI 23.5)
---
#### **1. 수행률 및 성실도 분석**
...
```

**JSON이 아니라 마크다운 텍스트**를 출력함. `{`가 아예 없어서 JSON 파싱 실패.

## qwen3 특성

qwen3는 "thinking mode"가 기본 활성화되어 있어서 추론/설명을 먼저 출력하는 경향이 있음.

## 해결 방법

### 1. 프롬프트에 `/no_think` 추가 (qwen3 전용)
```python
prompt = prompt + "\n/no_think"
```

### 2. 더 강한 JSON 지시 추가
프롬프트 끝에:
```
반드시 JSON만 출력하세요. 마크다운, 설명, 주석 없이 오직 JSON만 출력하세요.
```

### 3. 다른 모델 사용 (추천)
```bash
ollama pull exaone3.5:7.8b
```

어떻게 할래?
1. `prompt_generator.py`에 `/no_think` 추가
2. 모델을 exaone3.5로 변경
3. 둘 다

---

## User:
```
============================================================
Profile: 김철수 (표준 체형 - 균형잡힌 일반 성인 남성)
============================================================
[1/2] Rule-based body analysis...
...
[Warning] No JSON block found
[Debug] Full response:
### 주간 피드백 보고서

#### 사용자 정보 요약
- **성별**: 남자
...
```
이거 exaone 으로 변경했는데 왜 같은 문제? json 출력이 문제야?

---

## Assistant:
exaone도 같은 문제네. 프롬프트가 JSON 출력을 강제하지 못하고 있어.

프롬프트 시작 부분에 강한 JSON 지시를 추가할게.

[prompt_generator.py 수정 - 강한 JSON 지시 추가]

---

## User:
prompt_generator_claude.py 에서 어느부분이 json 출력을 요구하는거야? json 출력할 필요 없게 바꾸려면 어떻게해?

---

## Assistant:
## JSON 출력 요구 부분

`prompt_generator_claude.py` 맨 끝에:
```python
   [OUTPUT] JSON만 출력 ({{ 로 시작):
```

이 한 줄이 JSON 출력을 요구하는 부분이야.

## JSON 없이 자유 텍스트 출력하려면

### 1. 프롬프트 수정
마지막 줄 삭제하면 됨

[prompt_generator_claude.py 수정]

### 2. 파이프라인도 수정 필요

`run_pipeline_claude.py`에서 `generate_json()` 대신 `generate()`를 사용해야 해.

```python
def generate_recommendations(analysis_result, client) -> str | None:
    prompt = create_fitness_prompt(analysis_result.model_dump())
    return client.generate(prompt)  # 텍스트 그대로 반환
```

이렇게 하면:
- ✅ JSON 파싱 없음
- ✅ Pydantic 검증 없음
- ✅ LLM 출력 그대로 마크다운 텍스트

수정할까?

---

## User:
수정해줘

---

## Assistant:
[run_pipeline_gpt.py 수정 - generate_recommendations, run_pipeline, save_result, main 함수들 수정]

---

## User:
```
(llm) user@sgkim:~/projects/ExplainMyBody/experiments/llm$ python run_pipeline_gpt.py --profile-id 2
Ollama connected (model: exaone3.5:7.8b)
Loaded 10 validated profiles
============================================================
Profile: 이영희 (마른 체형 - 체중 정상이나 근육량 부족)
============================================================
[1/2] Rule-based body analysis...
  BMI: 19.8 (정상)
  Stage1: 마른비만형
  Stage2: 마른비만형
  Stage3: 표준형
[2/2] LLM recommendation generation...
[Warning] No JSON block found
[Debug] Full response:
### 주간 피드백 리포트
...
  [Warning] Failed or validation error
Result saved: outputs/이영희_20260121_195309.json
```
이거 result save가 실제 출력값이 제대로 반영되지 못하는데 확인

---

## Assistant:
문제 확인됨. 현재 흐름:

```
LLM 출력 (마크다운) → generate_json() → JSON 없음 → None 반환 → 저장 시 recommendations: null
```

**실제 LLM 출력이 저장되지 않고 `null`만 저장됨.**

[저장된 파일 확인 - recommendations: null]

[run_pipeline_gpt.py 수정 - 텍스트 응답도 저장하도록]

---

## User:
```json
  "recommendations": "### 주간 피드백 리포트\n\n#### [주간 실행 요약]\n- **계획 대비 실제 이행률**:\n...",
  "generated_at": "2026-01-21T19:56:27.087894"
```
이거 한줄로 나오는데 실제 읽기 좋도록 구성해줘. 그리고
```
Result saved: outputs/박민수_20260121_195627.json
=== Recommendation Summary ===
Traceback (most recent call last):
  File "/home/user/projects/ExplainMyBody/experiments/llm/run_pipeline_gpt.py", line 277, in <module>
    main()
  File "/home/user/projects/ExplainMyBody/experiments/llm/run_pipeline_gpt.py", line 260, in main
    print("Body type: " + recs.body_analysis_summary.body_type)
                          ^^^^^^^^^^^^^^^^^^^^^^^^^^
AttributeError: 'str' object has no attribute 'body_analysis_summary'
```
이 오류랑, llm 모델 파라미터 늘려도 될것같은데 모델추

---

## Assistant:
두 가지 문제 수정할게:

1. **텍스트 저장 포맷** - 줄바꿈이 `\n`으로 저장됨
2. **main() 오류** - 문자열인데 `.body_analysis_summary` 접근 시도

[main 함수 수정 - isinstance 체크 추가]

[save_result 수정 - 별도 .md 파일로 저장]

[ollama_client.py 수정 - max_tokens 파라미터 추가]

수정 완료! 이제:

## 변경 사항

1. **텍스트 응답 저장** → 별도 `.md` 파일로 저장 (읽기 쉬움)
2. **main() 오류 수정** → 문자열/dict 둘 다 처리
3. **max-tokens 파라미터** → CLI에서 조정 가능

## 사용법

```bash
# 기본 (4096 토큰)
python run_pipeline_gpt.py --profile-id 2

# 더 긴 응답 (8192 토큰)
python run_pipeline_gpt.py --profile-id 2 --max-tokens 8192
```

## 저장 파일

```
outputs/
├── 박민수_20260121_200000.json              # 분석 결과
└── 박민수_20260121_200000_recommendations.md  # LLM 추천 (마크다운)
```

---

## User:
지금처럼 md파일로 저장했을시 fastapi로 frontend 적용하고 postgresql db 저장했을때 문제없을까? 그리고 pydantic 지정 따로해야해?

---

## Assistant:
좋은 질문이야. 현재 구조와 FastAPI + PostgreSQL 통합 시 고려사항 정리해줄게.

## 현재 구조의 문제점

```
현재: LLM 응답 → .md 파일 저장 → 파일 시스템 의존
```

**문제:**
- 파일 시스템 의존 → 스케일링 어려움
- DB와 파일 동기화 문제
- 파일 경로 관리 복잡

## 권장 구조 (FastAPI + PostgreSQL)

```
권장: LLM 응답 → TEXT 컬럼에 직접 저장 → 프론트엔드에서 마크다운 렌더링
```

### 1. PostgreSQL 스키마

```sql
CREATE TABLE recommendations (
    id SERIAL PRIMARY KEY,
    profile_id INTEGER REFERENCES profiles(id),
    content TEXT NOT NULL,           -- 마크다운 텍스트 저장
    content_type VARCHAR(20),        -- 'json' or 'markdown'
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 2. Pydantic 모델 (FastAPI용)

```python
class RecommendationResponse(BaseModel):
    id: int
    profile_id: int
    content: Union[dict, str]  # JSON 또는 마크다운 텍스트
    content_type: str          # "json" | "markdown"
    created_at: datetime
```

### 3. 프론트엔드 마크다운 렌더링

```javascript
import ReactMarkdown from 'react-markdown';

function RecommendationView({ data }) {
  return <ReactMarkdown>{data.content}</ReactMarkdown>;
}
```

## 결론

| 항목 | 현재 | 권장 |
|------|------|------|
| 저장 | .md 파일 | PostgreSQL TEXT 컬럼 |
| Pydantic | 파일용 | API 요청/응답용 별도 정의 |
| 렌더링 | 파일 열기 | 프론트엔드 마크다운 라이브러리 |

**Pydantic 모델은 별도로 정의하는 게 좋아** - API 계층과 내부 로직 분리.

FastAPI + PostgreSQL 구조로 바꿔줄까?

---

## User:
지금 바꾸지는 말고, 만약 나중에 구현하면 어떤식으로 workflow가 돼?

---

## Assistant:
## 전체 Workflow (FastAPI + PostgreSQL)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              사용자 Flow                                      │
└─────────────────────────────────────────────────────────────────────────────┘

사용자 입력 → React Form → FastAPI → Pydantic 검증
                                   → 규칙기반 분석
                                   → LLM 호출
                                   → PostgreSQL 저장
                                   → JSON 응답 → React 마크다운 렌더링
```

### Step 1-2: 사용자 입력 → API 요청
```javascript
const submitProfile = async (formData) => {
  const response = await fetch('/api/profile', {
    method: 'POST',
    body: JSON.stringify({...})
  });
};
```

### Step 3-4: FastAPI 프로필 저장
```python
@app.post("/api/profile")
async def create_profile(profile: InBodyProfile, db: AsyncSession = Depends(get_db)):
    db_profile = Profile(**profile.model_dump())
    db.add(db_profile)
    await db.commit()
```

### Step 5-7: 분석 + LLM 추천 생성
```python
@app.post("/api/recommendations/{profile_id}")
async def generate_recommendation(profile_id: int):
    analysis = full_body_analysis_from_inbody(profile.to_dict())
    llm_response = ollama_client.generate(prompt)
    return {"analysis": analysis, "recommendations": llm_response}
```

## 핵심 포인트

| 구분 | 현재 (CLI) | 나중에 (Web) |
|------|-----------|-------------|
| 입력 | JSON 파일 | React Form |
| 검증 | Pydantic | Pydantic (동일) |
| 분석 | rulebase.py | rulebase.py (동일) |
| LLM | ollama_client.py | ollama_client.py (동일) |
| 저장 | .json/.md 파일 | PostgreSQL |
| 출력 | 터미널 | React + 마크다운 렌더러 |

**핵심 로직(rulebase, ollama_client, models)은 그대로 재사용** 가능

---

## User:
위 로직에서 md파일을 json파일로 변환한다고 나와있는데 이거 어떻게 구현된거야? 지금 코드에 있어?

---

## Assistant:
아니, MD → JSON 변환은 없어. 내가 설명한 워크플로우를 다시 정리해줄게:

## 현재 코드 흐름

```
LLM 응답 → JSON 파싱 시도 → 성공: dict 저장
                         → 실패: 원본 텍스트(.md) 저장
```

**변환이 아니라 "시도 후 분기"**

## 실제 코드 (run_pipeline_gpt.py)

```python
def generate_recommendations(...):
    raw_text = client.generate(prompt)

    try:
        # JSON 파싱 시도
        parsed = json.loads(json_str)
        return parsed  # ✅ JSON 성공 → dict 반환
    except:
        pass

    return raw_text  # ❌ JSON 실패 → 원본 텍스트 반환
```

## 정리

| LLM 응답 | 파싱 결과 | 저장 형태 |
|----------|----------|----------|
| `{"body_type": "근육형"...}` | JSON 성공 | `.json` 파일 내 포함 |
| `### 주간 피드백...` | JSON 실패 | 별도 `.md` 파일 |

**MD → JSON 변환 로직은 없음.** 마크다운은 마크다운 그대로 저장하고, 프론트엔드에서 마크다운 렌더러로 표시하는 방식이야.

---

## User:
지금 대화 내용 md파일로 저장해줘

---

## Assistant:
[conversation_summary.md 생성]

---

## User:
아니 위 대화 내용 원본 그대로 저장해줘

---

*생성일: 2026-01-21*
