# ExplainMyBody 파이프라인 가이드

## 📁 프로젝트 구조

```
llm/
├── shared/                              # 공유 모듈
│   ├── llm_clients.py                   # LLM 클라이언트 (Claude, OpenAI, Ollama)
│   ├── database.py                      # PostgreSQL 데이터베이스
│   └── models.py                        # Pydantic 데이터 모델
│
├── pipeline_inbody_analysis/            # 📊 파이프라인 1: InBody 분석
│   ├── main.py                          # 실행 파일 (Endpoint)
│   ├── analyzer.py                      # 분석 로직
│   ├── prompt_generator.py              # 프롬프트 생성
│   └── embedder.py                      # 임베딩 생성
│
├── pipeline_weekly_plan/                # 📅 파이프라인 2: 주간 계획 생성
│   ├── main.py                          # 실행 파일 (Endpoint)
│   ├── planner.py                       # 계획 생성 로직
│   ├── prompt_generator.py              # 프롬프트 생성
│   └── rag_retriever.py                 # Vector RAG 검색
│
├── rule_based_bodytype/                 # 규칙 기반 체형 분석 (기존)
├── sample_inbody_data.json              # 샘플 InBody 데이터
├── sample_user_goals.json               # 샘플 사용자 목표
└── sample_user_preferences.json         # 샘플 사용자 선호도
```

---

## 🚀 파이프라인 1: InBody 분석

### 개요

**InBody OCR 데이터 + 규칙기반 Stage → LLM 상세 분석 → 임베딩 저장**

- **입력**: InBody 측정 데이터 (JSON)
- **처리**:
  1. 규칙 기반 Stage 2/3 계산
  2. health_records에 저장
  3. LLM으로 상세 분석 생성
  4. analysis_reports에 저장
  5. (선택) 임베딩 생성
- **출력**: 분석 텍스트

### 실행 방법

#### 기본 실행
```bash
cd /home/user/projects/ExplainMyBody/llm/pipeline_inbody_analysis

python main.py \
  --user-id 1 \
  --measurements-file ../sample_inbody_data.json \
  --model gpt-4o-mini
```

#### Claude 모델 사용
```bash
python main.py \
  --user-id 1 \
  --measurements-file ../sample_inbody_data.json \
  --model claude-3-5-sonnet-20241022
```

#### 임베딩 생성 포함
```bash
python main.py \
  --user-id 1 \
  --measurements-file ../sample_inbody_data.json \
  --enable-embedding \
  --output-file result.json
```

#### JSON 문자열로 직접 입력
```bash
python main.py \
  --user-id 1 \
  --measurements-json '{"성별":"남자","나이":30,"신장":175.0,...}' \
  --model gpt-4o-mini
```

### API 엔드포인트 예시

```python
# FastAPI 엔드포인트
from fastapi import FastAPI
from shared.models import InBodyAnalysisRequest, InBodyAnalysisResponse
from pipeline_inbody_analysis.main import run_inbody_analysis

app = FastAPI()

@app.post("/api/inbody/analysis")
async def analyze_inbody(request: InBodyAnalysisRequest) -> InBodyAnalysisResponse:
    return run_inbody_analysis(
        user_id=request.user_id,
        measurements_dict=request.measurements.model_dump(),
        source=request.source,
        model="gpt-4o-mini",
        enable_embedding=True
    )
```

---

## 📅 파이프라인 2: 주간 계획 생성

### 개요

**InBody 분석 (RAG) + 사용자 목표/선호도 → LLM 주간 운동/식단 계획**

- **입력**:
  - 사용자 목표 (체중감량, 근육증가 등)
  - 사용자 선호도 (운동/식단 선호, 건강 특이사항)
- **처리**:
  1. Vector RAG로 InBody 분석 결과 검색
  2. 목표/선호도와 결합하여 프롬프트 생성
  3. LLM으로 주간 계획 생성 (JSON)
  4. (선택) DB 저장
- **출력**: 주간 운동/식단 계획 (JSON)

### 실행 방법

#### 기본 실행
```bash
cd /home/user/projects/ExplainMyBody/llm/pipeline_weekly_plan

python main.py \
  --user-id 1 \
  --goals-file ../sample_user_goals.json \
  --preferences-file ../sample_user_preferences.json \
  --week-number 1
```

#### 특정 기간 지정
```bash
python main.py \
  --user-id 1 \
  --goals-file ../sample_user_goals.json \
  --preferences-file ../sample_user_preferences.json \
  --week-number 2 \
  --start-date 2026-02-03 \
  --output-file week2_plan.json
```

#### 기본 설정으로 간단 실행
```bash
python main.py --user-id 1
```

#### JSON 문자열로 직접 입력
```bash
python main.py \
  --user-id 1 \
  --goals-json '[{"goal_type":"체중감량","priority":"high"}]' \
  --preferences-json '{"exercise_frequency":3,...}'
```

### API 엔드포인트 예시

```python
# FastAPI 엔드포인트
from fastapi import FastAPI
from shared.models import WeeklyPlanRequest, WeeklyPlanResponse
from pipeline_weekly_plan.main import run_weekly_plan_generation

app = FastAPI()

@app.post("/api/weekly-plan/generate")
async def generate_weekly_plan(request: WeeklyPlanRequest) -> WeeklyPlanResponse:
    return run_weekly_plan_generation(
        user_id=request.user_id,
        goals_dict_list=[g.model_dump() for g in request.goals],
        preferences_dict=request.preferences.model_dump(),
        week_number=request.week_number,
        start_date=request.start_date,
        model="gpt-4o-mini"
    )
```

---

## 🔄 전체 워크플로우 예시

### 시나리오: 새 사용자 온보딩

```bash
# 1단계: 사용자 등록 (수동)
# DB에 users 테이블에 INSERT

# 2단계: InBody 분석
cd /home/user/projects/ExplainMyBody/llm/pipeline_inbody_analysis
python main.py \
  --user-id 1 \
  --measurements-file ../sample_inbody_data.json \
  --enable-embedding \
  --output-file user1_inbody_analysis.json

# 3단계: 주간 계획 생성 (InBody 분석 결과 활용)
cd ../pipeline_weekly_plan
python main.py \
  --user-id 1 \
  --goals-file ../sample_user_goals.json \
  --preferences-file ../sample_user_preferences.json \
  --week-number 1 \
  --output-file user1_week1_plan.json
```

### 시나리오: 주차별 계획 생성

```bash
# 1주차
python pipeline_weekly_plan/main.py --user-id 1 --week-number 1 --goals-file sample_user_goals.json --preferences-file sample_user_preferences.json

# 2주차 (강도 상승)
python pipeline_weekly_plan/main.py --user-id 1 --week-number 2 --goals-file sample_user_goals.json --preferences-file sample_user_preferences.json

# 3주차
python pipeline_weekly_plan/main.py --user-id 1 --week-number 3 --goals-file sample_user_goals.json --preferences-file sample_user_preferences.json
```

---

## 🧪 테스트

### InBody 분석 테스트
```bash
cd pipeline_inbody_analysis

# 샘플 데이터로 테스트
python main.py \
  --user-id 999 \
  --measurements-file ../sample_inbody_data.json \
  --model gpt-4o-mini \
  --output-file test_analysis.json

# 결과 확인
cat test_analysis.json
```

### 주간 계획 테스트
```bash
cd pipeline_weekly_plan

# 샘플 데이터로 테스트
python main.py \
  --user-id 999 \
  --goals-file ../sample_user_goals.json \
  --preferences-file ../sample_user_preferences.json \
  --output-file test_plan.json

# 결과 확인
cat test_plan.json
```

---

## 🔧 설정

### 환경 변수 (.env)
```bash
# LLM API Keys
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...

# Database
DATABASE_URL=postgresql://sgkim:1234@localhost:5433/explainmybody
```

### 지원 모델

#### InBody 분석
- `gpt-4o-mini` (기본, 권장)
- `gpt-4o`
- `claude-3-5-sonnet-20241022`
- `claude-3-opus-20240229`

#### 주간 계획 생성
- `gpt-4o-mini` (기본, 권장)
- `gpt-4o` (더 정교한 계획)
- `claude-3-5-sonnet-20241022`

---

## 📊 데이터 모델

### InBodyMeasurements
```python
{
  "성별": "남자",
  "나이": 30,
  "신장": 175.0,
  "체중": 75.0,
  "BMI": 24.5,
  "체지방률": 24.0,
  "골격근량": 35.0,
  "근육_부위별등급": {...},
  "stage2_근육보정체형": "표준형",  # 자동 계산
  "stage3_상하체밸런스": "균형형"    # 자동 계산
}
```

### UserGoal
```python
{
  "goal_type": "체중감량",
  "target_weight": 68.0,
  "target_body_fat": 18.0,
  "deadline": "3개월",
  "priority": "high"
}
```

### UserPreferences
```python
{
  "preferred_exercise_types": ["웨이트", "유산소"],
  "exercise_frequency": 4,
  "exercise_duration": 60,
  "dietary_restrictions": [],
  "health_conditions": [],
  "injuries": ["왼쪽 무릎 불편"]
}
```

### WeeklyPlan (출력)
```python
{
  "week_number": 1,
  "start_date": "2026-02-03",
  "end_date": "2026-02-09",
  "weekly_summary": "...",
  "weekly_goal": "...",
  "tips": ["...", "..."],
  "daily_plans": [
    {
      "day_of_week": "월요일",
      "exercises": [...],
      "meals": [...],
      "total_calories": 1800
    }
  ]
}
```

---

## 🚧 TODO (향후 기능)

### pgvector 활성화
```sql
-- analysis_reports에 embedding 컬럼 추가
ALTER TABLE analysis_reports ADD COLUMN embedding vector(1536);

-- 인덱스 생성
CREATE INDEX ON analysis_reports
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
```

### weekly_plans 테이블 생성
```sql
CREATE TABLE weekly_plans (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    week_number INTEGER,
    start_date DATE,
    end_date DATE,
    plan_data JSONB,
    model_version VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 📚 참고 문서

- [Shared Models](shared/models.py) - 모든 데이터 모델
- [LLM Clients](shared/llm_clients.py) - LLM 클라이언트 사용법
- [Database Schema](database_schema.dbml) - DB 구조

---

## 💡 팁

### 1. 두 파이프라인 병렬 실행
```bash
# Terminal 1: InBody 분석
python pipeline_inbody_analysis/main.py --user-id 1 --measurements-file sample_inbody_data.json &

# Terminal 2: 주간 계획 (InBody 분석 완료 후)
python pipeline_weekly_plan/main.py --user-id 1 --goals-file sample_user_goals.json --preferences-file sample_user_preferences.json
```

### 2. 배치 처리
```bash
# 여러 사용자 일괄 처리
for user_id in 1 2 3 4 5; do
  python pipeline_inbody_analysis/main.py --user-id $user_id --measurements-file user${user_id}_data.json
done
```

### 3. 결과 모니터링
```bash
# 실시간 로그 확인
tail -f outputs/weekly_plans/*.json
```

---

## 🎯 결론

**두 개의 독립적인 파이프라인으로 분리 완료!**

- ✅ **파이프라인 1**: InBody 분석 (독립 endpoint)
- ✅ **파이프라인 2**: 주간 계획 생성 (독립 endpoint)
- ✅ **공유 모듈**: LLM clients, Database, Models
- ✅ **Vector RAG**: InBody 분석 결과 활용

각 파이프라인은 독립적으로 실행 가능하며, FastAPI 등으로 쉽게 endpoint화 가능합니다!
