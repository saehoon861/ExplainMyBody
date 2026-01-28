# ExplainMyBody LLM 프로젝트

InBody 데이터 기반 체형 분석 및 LLM 추천 생성 시스템

---

## 🚀 빠른 시작

### 1. 의존성 설치
```bash
pip install -r requirements.txt
```

### 2. PostgreSQL 설정
```bash
# Docker 사용 (권장)
docker run -d \
  --name explainmybody-postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_DB=explainmybody \
  -p 5432:5432 \
  pgvector/pgvector:pg16

# .env 파일 확인
# DATABASE_URL=postgresql://postgres:postgres@localhost:5432/explainmybody
```

📖 **자세한 PostgreSQL 설정**: [POSTGRESQL_SETUP.md](POSTGRESQL_SETUP.md)

### 3. 워크플로우 실행
```bash
python main_workflow.py \
  --username "홍길동" \
  --email "hong@example.com" \
  --profile-id 1 \
  --model gpt-4o-mini
```

📖 **자세한 사용법**: [WORKFLOW_GUIDE.md](WORKFLOW_GUIDE.md)

---

## 📁 프로젝트 구조

### 🎯 신규 워크플로우 (메인)

| 파일 | 설명 |
|------|------|
| `main_workflow.py` ⭐ | 통합 워크플로우 실행 파일 |
| `workflow.py` | 6단계 워크플로우 로직 |
| `database.py` | PostgreSQL 데이터베이스 관리 |
| `prompt_generator_measurements.py` | measurements 기반 프롬프트 생성 |

**워크플로우:**
```
회원가입/로그인 → OCR 추출 → 사용자 확인 → Stage 계산 →
데이터 병합 → DB 저장 → LLM 리포트 생성 → 완료
```

---

### 🔧 기존 파이프라인 (레거시)

| 파일 | 설명 | 사용 모델 |
|------|------|-----------|
| `run_pipeline.py` | 통합 파이프라인 | Ollama / Claude / OpenAI |
| `run_pipeline_claude.py` | Claude API 전용 | Claude (Anthropic) |
| `run_pipeline_gpt.py` | OpenAI API 전용 | GPT (OpenAI) |

---

### 🤖 LLM 클라이언트

| 파일 | LLM API |
|------|---------|
| `ollama_client.py` | Ollama (로컬 모델) |
| `claude_client.py` | Anthropic Claude API |
| `openai_client.py` | OpenAI GPT API |

**환경변수 설정 (`.env`):**
```bash
ANTHROPIC_API_KEY=your_claude_api_key
OPENAI_API_KEY=your_openai_api_key
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/explainmybody
```

---

### 📝 프롬프트 생성기

| 파일 | 대상 모델 | 특징 |
|------|----------|------|
| `prompt_generator_measurements.py` ⭐ | All | measurements 전체 데이터 활용 |
| `prompt_generator_claude.py` | Claude | Claude 최적화 (레거시) |
| `prompt_generator_gpt.py` | GPT | GPT 최적화 (레거시) |

---

### 🧮 규칙 기반 분석

| 폴더/파일 | 설명 |
|----------|------|
| `rule_based_bodytype/` ⭐ | 신규 Stage 분석 알고리즘 |
| `rulebase.py` | 레거시 규칙 기반 분석 |
| `rulebase_wrapper.py` | rulebase.py 래퍼 |
| `models.py` | Pydantic 데이터 모델 |

---

### 📊 데이터 및 문서

| 파일/폴더 | 내용 |
|----------|------|
| `sample_profiles.json` | 테스트용 InBody 프로필 (10개) |
| `outputs/` | LLM 출력 결과 저장 폴더 |
| `README.md` | 이 파일 |
| `WORKFLOW_GUIDE.md` | 워크플로우 사용 가이드 |
| `POSTGRESQL_SETUP.md` | PostgreSQL 설정 가이드 |

---

## 🆕 신규 워크플로우 주요 기능

### ✅ PostgreSQL + pgvector
- **JSONB**: 유연한 측정 데이터 저장 및 빠른 검색
- **pgvector 지원**: 향후 임베딩 기반 유사 리포트 검색
- **GIN 인덱스**: JSONB 필드 검색 최적화

### ✅ 전체 measurements 활용
- InBody 모든 측정값 (체중, BMI, 체지방률, 골격근량, 무기질, 체수분 등)
- 부위별 근육/지방 등급
- Stage 2, 3 분석 결과

### ✅ rule_based_bodytype 알고리즘
- **Stage 2**: 근육보정체형 (표준형, 근육형, 비만형 등)
- **Stage 3**: 상하체밸런스 (표준형, 상체발달형, 하체발달형 등)

### ✅ 회원 관리 시스템
- 이메일 기반 자동 회원가입/로그인
- 사용자별 건강 기록 관리
- 분석 리포트 이력 추적

---

## 🗄️ 데이터베이스 스키마

### users (사용자)
```sql
id, username, email, created_at
```

### health_records (건강 기록)
```sql
id, user_id, source, measured_at,
measurements (JSONB), created_at
```

### analysis_reports (분석 리포트)
```sql
id, user_id, record_id,
llm_output (TEXT), model_version, generated_at
```

### user_goals (사용자 목표)
```sql
id, user_id, goal_type, started_at, ended_at
```

---

## 📖 사용 예시

### 신규 워크플로우
```bash
# 1. 프로필 목록 확인
python main_workflow.py --list-profiles

# 2. 워크플로우 실행
python main_workflow.py \
  --username "김철수" \
  --email "kim@example.com" \
  --profile-id 2 \
  --model claude-3-5-sonnet-20241022

# 3. 등록된 사용자 확인
python main_workflow.py --list-users
```

### 레거시 파이프라인
```bash
# Ollama (로컬)
python run_pipeline.py --model qwen3:14b --profile-id 1

# Claude API
python run_pipeline_claude.py --model claude-3-5-sonnet-20241022 --all

# OpenAI API
python run_pipeline_gpt.py --model gpt-4o-mini --profile-id 1
```

---

## 🔄 워크플로우 비교

| 구분 | 레거시 (run_pipeline_*.py) | 신규 (main_workflow.py) |
|------|---------------------------|-------------------------|
| **규칙 분석** | rulebase.py (전체) | rule_based_bodytype (Stage 2, 3) |
| **데이터 저장** | 파일 (JSON/MD) | PostgreSQL (JSONB + pgvector) |
| **프롬프트** | 규칙 분석 결과 | measurements 전체 데이터 |
| **사용자 관리** | 없음 | 회원가입/로그인 |
| **데이터 구조** | 분석 결과만 | OCR + Stage + 모든 측정값 |
| **확장성** | 제한적 | 시계열 분석, 유사도 검색 가능 |

---

## 🛠️ 의존성

```
anthropic>=0.76.0       # Claude API
numpy>=2.4.1            # 수치 계산
openai>=2.15.0          # OpenAI API
psycopg2-binary>=2.9.9  # PostgreSQL 드라이버
pydantic>=2.12.5        # 데이터 검증
pydantic-settings>=2.12.0
python-dotenv>=1.2.1    # 환경변수 관리
requests>=2.32.5        # HTTP 요청
```

---

## 🔧 문제 해결

### PostgreSQL 연결 오류
```bash
# 서비스 확인
sudo systemctl status postgresql

# Docker 사용 시
docker start explainmybody-postgres
docker logs explainmybody-postgres
```

### API 키 오류
```bash
# .env 파일 확인
cat .env

# 필요한 키
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
DATABASE_URL=postgresql://...
```

### Ollama 연결 오류
```bash
# Ollama 서버 시작
ollama serve

# 확인
curl http://localhost:11434/api/tags
```

---

## 📚 문서

- **[ONBOARDING.md](ONBOARDING.md)** ⭐ - 신규 개발자 온보딩 가이드
- [WORKFLOW_GUIDE.md](WORKFLOW_GUIDE.md) - 워크플로우 상세 가이드
- [POSTGRESQL_SETUP.md](POSTGRESQL_SETUP.md) - PostgreSQL 설정 가이드
- [Anthropic Claude API](https://docs.anthropic.com/)
- [OpenAI API](https://platform.openai.com/docs/)
- [pgvector](https://github.com/pgvector/pgvector)

---

## 🎯 프로젝트 목표

InBody 검사 결과지를 기반으로:
1. **규칙 기반 분석**: BMI, 체지방률, 근육량 분석 및 체형 분류
2. **LLM 추천 생성**: 개인 맞춤형 운동/식단 추천
3. **데이터 관리**: PostgreSQL 기반 사용자 건강 기록 관리
4. **향후 확장**: pgvector를 활용한 유사 리포트 검색 및 추천

---

## 📁 outputs 폴더 구조

```
outputs/
├── report_1_20260123_120000.txt       # 신규 워크플로우 리포트
├── report_2_20260123_120530.txt
└── ...
```

**신규 워크플로우 출력:**
- 사용자별 분석 리포트 (텍스트 파일)
- 데이터베이스에도 저장됨

**레거시 파이프라인 출력:**
- JSON: `이영희_20260122_143020.json`
- Markdown: `이영희_20260122_143020_recommendations.md`

---

## 🚀 다음 단계

1. **FastAPI 백엔드**: REST API 엔드포인트 구현
2. **Frontend**: OCR 데이터 확인/수정 UI
3. **pgvector 활용**: 유사 리포트 검색 기능
4. **시계열 분석**: 측정 기록 비교 및 추세 분석
5. **목표 추적**: 사용자 목표 설정 및 달성률 추적

---

## 📧 Contact

프로젝트 관련 문의 또는 기여는 이슈를 통해 남겨주세요.
