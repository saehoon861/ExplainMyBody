# ExplainMyBody LLM 실험 프로젝트

InBody 데이터 기반 체형 분석 및 LLM 추천 생성 시스템

## 빠른 시작

```bash
# 의존성 설치
pip install -r requirements.txt

# 샘플 프로필 확인
python run_pipeline.py

# 실행 (프로필 ID=1)
python run_pipeline_gpt.py --profile-id 1
```

📖 **자세한 사용법**: [USAGE.md](USAGE.md)

---

## 프로젝트 구조

### 🎯 실행 파일 (메인)

| 파일 | 설명 | 사용 모델 |
|------|------|-----------|
| `run_pipeline.py` | 통합 파이프라인 (모든 모델 지원) | Ollama / Claude / OpenAI |
| `run_pipeline_claude.py` | Claude API 전용 파이프라인 | Claude (Anthropic) |
| `run_pipeline_gpt.py` | OpenAI API 전용 파이프라인 | GPT (OpenAI) |
| `langgraph_pipeline.py` | LangGraph 2단계 파이프라인 | Claude / OpenAI |

**💡 실행 명령어 예시:**
```bash
# Ollama (로컬 모델)
python run_pipeline.py --model qwen3:14b --profile-id 1

# Claude API
python run_pipeline_claude.py --model claude-3-5-sonnet-20241022 --all

# OpenAI API
python run_pipeline_gpt.py --model gpt-4o-mini --profile-id 1

# LangGraph (2단계: 자연어 → JSON)
python langgraph_pipeline.py --model claude-3-5-sonnet-20241022
```

---

### 🔧 핵심 모듈

| 파일 | 역할 |
|------|------|
| `models.py` | Pydantic 데이터 모델 정의 (InBodyProfile, BodyAnalysisResult, LLMRecommendation 등) |
| `rulebase.py` | 규칙 기반 체형 분석 로직 (BMI, 근육/지방 분석) |
| `rulebase_wrapper.py` | rulebase.py의 래퍼 함수 제공 |

---

### 🤖 LLM 클라이언트

| 파일 | LLM API |
|------|---------|
| `ollama_client.py` | Ollama (로컬 모델: qwen3, llama 등) |
| `claude_client.py` | Anthropic Claude API |
| `openai_client.py` | OpenAI GPT API |

**환경변수 설정 (`.env`):**
```bash
ANTHROPIC_API_KEY=your_claude_api_key
OPENAI_API_KEY=your_openai_api_key
```

---

### 📝 프롬프트 생성기

| 파일 | 대상 모델 | 특징 |
|------|----------|------|
| `prompt_generator_claude.py` | Claude | Claude 최적화 프롬프트 (system + user) |
| `prompt_generator_gpt.py` | GPT | GPT 최적화 프롬프트 (system + user) |

---

### 📊 데이터 파일

| 파일/폴더 | 내용 |
|----------|------|
| `sample_profiles.json` | 테스트용 InBody 프로필 데이터 (10개 샘플) |
| `outputs/` | **LLM 모델 출력 결과물 저장 폴더** (JSON/Markdown) |
| `json/` | 기타 JSON 데이터 |

**outputs 폴더 구조:**
```
outputs/
├── 이영희_20260122_143020.json              # 분석 결과 + 추천
├── 이영희_20260122_143020_recommendations.md # 자연어 추천 (텍스트 응답 시)
└── ...
```

---

### 📚 문서

| 파일 | 내용 |
|------|------|
| `README.md` | 이 파일 (프로젝트 개요) |
| `USAGE.md` | 상세 사용 가이드 (모델별 실행 명령어) |
| `LANGGRAPH_GUIDE.md` | LangGraph 2단계 파이프라인 원리 및 사용법 |

---

### 🧪 테스트 파일

| 파일 | 용도 |
|------|------|
| `test_claude.py` | Claude API 연결 테스트 |

---

## 워크플로우

```
InBody 데이터 (sample_profiles.json)
        ↓
규칙 기반 분석 (rulebase.py)
        ↓
체형 분석 결과 (BodyAnalysisResult)
        ↓
프롬프트 생성 (prompt_generator_*.py)
        ↓
LLM 호출 (ollama_client / claude_client / openai_client)
        ↓
추천 생성 (자연어 or JSON)
        ↓
결과 저장 (outputs/)
```

---

## 주요 기능

### ✅ Pydantic 데이터 검증
- 모든 입력/출력을 Pydantic 모델로 검증
- 타입 안전성 및 데이터 무결성 보장

### ✅ 다중 LLM 지원
- **Ollama**: 로컬 모델 (qwen3, llama 등)
- **Claude**: Anthropic API
- **OpenAI**: GPT API

### ✅ 유연한 출력 형식
- JSON 구조화 응답
- 자연어 텍스트 응답
- JSON 파싱 실패 시 자동으로 텍스트 저장

### ✅ LangGraph 파이프라인
- 2단계 처리: 자연어 생성 → JSON 변환
- 상태 그래프 기반 워크플로우 관리

---

## 사용 예시

### 1. 단일 프로필 실행
```bash
python run_pipeline_gpt.py --profile-id 1
```

### 2. 전체 프로필 실행
```bash
python run_pipeline_claude.py --all --output-dir outputs/claude_results
```

### 3. 조용히 실행 (로그 최소화)
```bash
python run_pipeline.py --profile-id 1 --quiet
```

### 4. LangGraph 실행
```bash
python langgraph_pipeline.py --model claude-3-5-sonnet-20241022
```

---

## 출력 결과 예시

### JSON 형식 (성공 시)
```json
{
  "body_analysis_summary": {
    "body_type": "마른비만형",
    "key_issues": ["복부 지방 과다", "근육량 부족"]
  },
  "exercise_plan": {
    "weekly_goal": "주 4회 근력 운동",
    "recommended_exercises": [...]
  },
  "diet_plan": {
    "daily_calorie_target": 2000
  }
}
```

### Markdown 형식 (텍스트 응답 시)
```markdown


## 참고 자료

- [USAGE.md](USAGE.md) - 상세 사용 가이드
- [LANGGRAPH_GUIDE.md](LANGGRAPH_GUIDE.md) - LangGraph 원리 및 활용법
- [Anthropic Claude API](https://docs.anthropic.com/)
- [OpenAI API](https://platform.openai.com/docs/)
- [LangGraph 공식 문서](https://langchain-ai.github.io/langgraph/)
