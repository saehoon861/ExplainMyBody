# ExplainMyBody LLM 실험 - 대화 기록

## 프로젝트 개요

InBody 체성분 측정 결과를 분석하여 개인 맞춤형 운동/식단 추천을 생성하는 파이프라인

### 파이프라인 흐름
```
InBody 데이터 → 규칙기반 분석 (rulebase.py) → LLM 추천 생성 → 결과 저장
```

---

## 1. Serena 온보딩

### 생성된 메모리 파일
| 메모리 | 내용 |
|--------|------|
| `project_overview.md` | 프로젝트 목적, 파이프라인 흐름, 기술 스택 |
| `suggested_commands.md` | 실행 명령어, uv, Ollama, WSL 명령어 |
| `style_and_conventions.md` | 코드 스타일, 한국어 주석, Pydantic 패턴 |
| `task_completion.md` | 작업 완료 체크리스트, 일반적인 문제 해결 |

---

## 2. LLM JSON 출력 문제

### 문제 상황
- qwen3:8b, exaone3.5:7.8b 모델이 JSON 대신 마크다운 텍스트 출력
- `[Warning] No JSON block found` 오류 발생

### 원인
```
LLM 응답:
### 주간 피드백 리포트
#### [주간 실행 요약]
...
```
→ JSON `{`가 없어서 파싱 실패

### 시도한 해결책

#### 2.1 프롬프트 강화 (prompt_generator.py)
```python
prompt = """[IMPORTANT] 반드시 JSON만 출력하세요. 설명, 마크다운, 주석 없이 오직 JSON 객체만 출력하세요.
...
[OUTPUT] JSON만 출력 ({{ 로 시작):"""
```

#### 2.2 모델 변경 시도
| 모델 | 크기 | 결과 |
|------|------|------|
| qwen3:8b | 8B | JSON 출력 실패 |
| exaone3.5:7.8b | 7.8B | JSON 출력 실패 |
| qwen2.5:14b | 14B | 추천 (미테스트) |

---

## 3. 텍스트 출력 방식으로 전환

### 변경 사항

#### 3.1 prompt_generator_claude.py 수정
- JSON 요구 제거
- 마크다운 형식으로 자유롭게 출력하도록 변경

```python
prompt = """당신은 전문 피트니스 트레이너이자 영양사입니다.
...
위 내용을 마크다운 형식으로 상세히 작성해주세요."""
```

#### 3.2 run_pipeline_gpt.py 수정

**generate_recommendations 함수:**
```python
def generate_recommendations(analysis_result, client) -> dict | str | None:
    raw_text = client.generate(prompt)

    # JSON 파싱 시도
    try:
        # JSON 파싱 성공 시 dict 반환
        return validated.model_dump()
    except (json.JSONDecodeError, ValidationError):
        pass

    # JSON 실패 시 원본 텍스트 반환
    return raw_text
```

**save_result 함수:**
```python
def save_result(result, output_dir):
    # 텍스트 응답이면 별도 .md 파일로 저장
    if isinstance(result.recommendations, str):
        md_filepath = output_path / (base_filename + "_recommendations.md")
        with open(md_filepath, "w", encoding="utf-8") as f:
            f.write(result.recommendations)
```

**main 함수:**
```python
if isinstance(recs, dict):
    # JSON 파싱 성공한 경우
    print("Body type: " + recs.get("body_analysis_summary", {}).get("body_type", "N/A"))
elif isinstance(recs, str):
    # 텍스트 응답인 경우
    print("[텍스트 응답 - 전체 내용은 저장된 파일 확인]")
```

#### 3.3 ollama_client.py 수정
```python
def __init__(self, base_url, model="exaone3.5:7.8b", max_tokens=4096):
    self.max_tokens = max_tokens

def generate(self, prompt, temperature=0.7, max_tokens=None):
    tokens = max_tokens if max_tokens else self.max_tokens
    # ...
```

### 저장 결과
```
outputs/
├── 박민수_20260121_200000.json              # 분석 결과
└── 박민수_20260121_200000_recommendations.md  # LLM 추천 (마크다운)
```

---

## 4. CLI 옵션 추가

```bash
# 기본 (4096 토큰)
python run_pipeline_gpt.py --profile-id 2

# 더 긴 응답 (8192 토큰)
python run_pipeline_gpt.py --profile-id 2 --max-tokens 8192

# 다른 모델 사용
python run_pipeline_gpt.py --profile-id 2 --model qwen2.5:14b
```

---

## 5. FastAPI + PostgreSQL 통합 계획

### 현재 vs 권장 구조

| 항목 | 현재 (CLI) | 권장 (Web) |
|------|-----------|------------|
| 입력 | JSON 파일 | React Form |
| 검증 | Pydantic | Pydantic (동일) |
| 분석 | rulebase.py | rulebase.py (동일) |
| LLM | ollama_client.py | ollama_client.py (동일) |
| 저장 | .json/.md 파일 | PostgreSQL |
| 출력 | 터미널 | React + 마크다운 렌더러 |

### 워크플로우

```
사용자 입력 → React Form → FastAPI → Pydantic 검증
                                   → 규칙기반 분석
                                   → LLM 호출
                                   → PostgreSQL 저장
                                   → JSON 응답 → React 마크다운 렌더링
```

### PostgreSQL 스키마 (예정)
```sql
CREATE TABLE recommendations (
    id SERIAL PRIMARY KEY,
    profile_id INTEGER REFERENCES profiles(id),
    content TEXT NOT NULL,           -- 마크다운 텍스트 저장
    content_type VARCHAR(20),        -- 'json' or 'markdown'
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Pydantic 모델 (FastAPI용)
```python
class RecommendationResponse(BaseModel):
    id: int
    profile_id: int
    content: Union[dict, str]  # JSON 또는 마크다운 텍스트
    content_type: str          # "json" | "markdown"
    created_at: datetime
```

### 프론트엔드 마크다운 렌더링
```javascript
import ReactMarkdown from 'react-markdown';

function RecommendationView({ data }) {
  return <ReactMarkdown>{data.content}</ReactMarkdown>;
}
```

---

## 6. 핵심 정리

### MD → JSON 변환 없음
- 마크다운은 마크다운 그대로 저장
- 프론트엔드에서 마크다운 렌더러로 표시
- JSON 파싱 실패 시 원본 텍스트 유지

### 재사용 가능한 코드
- `rulebase.py` - 규칙기반 분석
- `ollama_client.py` - LLM 클라이언트
- `models.py` - Pydantic 모델

---

## 7. 추천 모델

| 모델 | 토큰 | 특징 |
|------|------|------|
| `qwen2.5:14b` | 8192+ | JSON 출력 더 안정적 |
| `exaone3.5:7.8b` | 4096 | 한국어 우수, 속도 빠름 |
| `llama3.1:8b` | 8192 | 지시 따르기 우수 |

---

*생성일: 2026-01-21*
