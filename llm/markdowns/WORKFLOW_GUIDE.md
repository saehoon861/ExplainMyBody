# InBody 분석 워크플로우 가이드

## 개요

새로운 워크플로우는 다음 단계로 진행됩니다:

```
회원가입/로그인
    ↓
OCR 데이터 추출 (시뮬레이션)
    ↓
사용자 데이터 확인
    ↓
Stage 분석 (rule_based_bodytype)
    ↓
데이터 병합
    ↓
health_records 저장 (DB)
    ↓
LLM 분석 리포트 생성
    ↓
완료
```

---

## 데이터베이스 구조 (PostgreSQL)

### PostgreSQL + pgvector 사용
- **JSONB**: 유연한 측정 데이터 저장 및 빠른 검색
- **pgvector**: 향후 임베딩 기반 유사 리포트 검색
- **GIN 인덱스**: JSONB 필드 검색 최적화

📖 **PostgreSQL 설치 가이드**: [POSTGRESQL_SETUP.md](POSTGRESQL_SETUP.md)

### 1. users (사용자)
```sql
- id: 사용자 고유 ID
- username: 사용자명
- email: 이메일 (고유)
- created_at: 가입 일시
```

### 2. health_records (건강 기록)
```sql
- id: 기록 ID
- user_id: 사용자 ID
- source: 데이터 출처 (inbody_ocr, manual 등)
- measured_at: 측정 일시
- measurements: JSON 데이터 (전체 InBody 데이터 + Stage 분석 결과)
- created_at: 생성 일시
```

**measurements JSON 구조:**
```json
{
  "성별": "남성",
  "나이": 28,
  "신장": 175.0,
  "체중": 72.5,
  "BMI": 23.7,
  "체지방률": 21.0,
  "골격근량": 35.6,
  "무기질": 3.5,
  "체수분": 45.2,
  "단백질": 12.8,
  "체지방": 15.2,
  "복부지방률": 0.85,
  "내장지방레벨": 8,
  "기초대사량": 1680,
  "비만도": 105.2,
  "적정체중": 68.9,
  "권장섭취열량": 2400,
  "체중조절": -3.6,
  "지방조절": -5.2,
  "근육조절": 1.6,
  "근육_부위별등급": {
    "왼팔": "표준",
    "오른팔": "표준",
    "복부": "표준",
    "왼다리": "표준이상",
    "오른다리": "표준이상"
  },
  "체지방_부위별등급": {
    "왼팔": "표준",
    "오른팔": "표준",
    "복부": "표준이상",
    "왼다리": "표준",
    "오른다리": "표준"
  },
  "stage2_근육보정체형": "근육형",
  "stage3_상하체밸런스": "하체발달형"
}
```

### 3. analysis_reports (분석 리포트)
```sql
- id: 리포트 ID
- user_id: 사용자 ID
- record_id: health_record ID
- llm_output: LLM 생성 리포트 (텍스트)
- model_version: 사용한 LLM 모델
- generated_at: 생성 일시
```

### 4. user_goals (사용자 목표)
```sql
- id: 목표 ID
- user_id: 사용자 ID
- goal_type: 목표 유형 (다이어트, 근성장 등)
- started_at: 시작 일시
- ended_at: 종료 일시
```

---

## 사전 준비

### PostgreSQL 설치 및 설정

1. **PostgreSQL 설치**: [POSTGRESQL_SETUP.md](POSTGRESQL_SETUP.md) 참고
2. **.env 파일 설정**:
   ```bash
   DATABASE_URL=postgresql://postgres:postgres@localhost:5432/explainmybody
   ```
3. **연결 테스트**:
   ```bash
   python -c "from database import Database; db = Database(); print('OK' if db.test_connection() else 'FAIL')"
   ```

---

## 사용 방법

### 1. 기본 실행

```bash
python main_workflow.py \
  --username "홍길동" \
  --email "hong@example.com" \
  --profile-id 1 \
  --model gpt-4o-mini
```

### 2. Claude 모델 사용

```bash
python main_workflow.py \
  --username "김철수" \
  --email "kim@example.com" \
  --profile-id 2 \
  --model claude-3-5-sonnet-20241022
```

### 3. Ollama (로컬) 사용

```bash
# 먼저 Ollama 서버 실행
ollama serve

# 워크플로우 실행
python main_workflow.py \
  --username "이영희" \
  --email "lee@example.com" \
  --profile-id 3 \
  --model qwen3:14b
```

### 4. 사용자 목록 확인

```bash
python main_workflow.py --list-users
```

### 5. 프로필 목록 확인

```bash
python main_workflow.py --list-profiles
```

---

## 주요 기능

### 🆕 자동 회원가입/로그인
- 이메일이 이미 존재하면 로그인
- 없으면 자동으로 회원가입

### 📊 전체 measurements 활용
- 기존 규칙 기반 분석 대신 measurements의 모든 데이터를 LLM에 제공
- InBody의 모든 측정 값 + Stage 분석 결과 통합

### 🧮 rule_based_bodytype 알고리즘
- Stage 2: 근육 보정 체형 분석
- Stage 3: 상하체 밸런스 분석

### 💾 PostgreSQL 데이터베이스
- **JSONB**: 유연한 측정 데이터 저장 및 빠른 검색
- **pgvector 준비**: 향후 유사 리포트 검색
- **GIN 인덱스**: JSONB 필드 검색 최적화
- 시계열 데이터 관리 가능

---

## 파일 구조

```
llm/
├── main_workflow.py              # 메인 실행 파일
├── workflow.py                   # 워크플로우 로직
├── database.py                   # 데이터베이스 관리
├── prompt_generator_measurements.py  # measurements 기반 프롬프트
├── claude_client.py              # Claude API 클라이언트
├── openai_client.py              # OpenAI API 클라이언트
├── ollama_client.py              # Ollama 클라이언트
├── sample_profiles.json          # 샘플 프로필 데이터
├── .env                          # PostgreSQL 연결 정보
├── POSTGRESQL_SETUP.md           # PostgreSQL 설정 가이드
├── outputs/                      # 리포트 출력 폴더
└── rule_based_bodytype/          # 규칙 기반 분석 알고리즘
    └── body_analysis/
        ├── pipeline.py           # 분석 파이프라인
        ├── stages.py             # Stage 분석
        ├── models.py             # 데이터 모델
        └── ...
```

---

## 출력 결과

### 터미널 출력
```
✅ 데이터베이스 연결: explainmybody.db
🤖 LLM: OpenAI (gpt-4o-mini)
✅ API 연결 성공
🎉 회원가입 완료: 홍길동 (hong@example.com)

📊 선택된 프로필: 이영희 (20대 여성, 표준 체형)
============================================================
InBody 분석 워크플로우 시작 (User ID: 1)
============================================================
📸 1단계: OCR 데이터 추출...
  ✓ OCR 데이터 추출 완료: 여자, 28세
✅ 2단계: 사용자 데이터 확인...
  (시뮬레이션: 사용자가 데이터를 확인했다고 가정)
  ✓ 사용자 확인 완료
🧮 3단계: Stage 분석 계산...
  ✓ Stage 2: 표준형
  ✓ Stage 3: 표준형
🔄 4단계: 데이터 병합...
  ✓ 데이터 병합 완료
💾 5단계: health_records 저장...
  ✓ health_record 저장 완료 (ID: 1)
🤖 6단계: LLM 분석 리포트 생성...
  - LLM 호출 중...
  ✓ LLM 응답 생성 완료 (1523 글자)
  ✓ 분석 리포트 저장 완료 (ID: 1)
============================================================
✨ 워크플로우 완료!
  - Record ID: 1
  - Report ID: 1
============================================================

📋 LLM 분석 리포트
[리포트 내용 출력...]

💾 리포트 저장 완료: outputs/report_1_20260123_120000.txt

✨ 모든 작업이 완료되었습니다!
  - User ID: 1
  - Health Record ID: 1
  - Analysis Report ID: 1
```

### 파일 출력
- `outputs/report_[ID]_[timestamp].txt`: LLM 분석 리포트 텍스트 파일

---

## 워크플로우 클래스 구조

### InBodyAnalysisWorkflow
전체 워크플로우를 관리하는 메인 클래스

**주요 메서드:**
- `extract_ocr_data()`: OCR 데이터 추출 (1단계)
- `get_user_confirmation()`: 사용자 확인 (2단계)
- `calculate_stages()`: Stage 계산 (3단계)
- `merge_data()`: 데이터 병합 (4단계)
- `save_health_record()`: DB 저장 (5단계)
- `generate_llm_report()`: LLM 리포트 생성 (6단계)
- `run_full_workflow()`: 전체 워크플로우 실행

### UserAuthManager
사용자 인증 관리

**주요 메서드:**
- `register_or_login()`: 회원가입 또는 로그인

---

## 기존 파이프라인과의 차이점

| 구분 | 기존 (run_pipeline_*.py) | 새 워크플로우 (main_workflow.py) |
|------|-------------------------|--------------------------------|
| **규칙 분석** | rulebase.py (전체 분석) | rule_based_bodytype (Stage 2, 3만) |
| **데이터 저장** | 파일 (JSON/MD) | PostgreSQL (JSONB + pgvector) |
| **프롬프트** | 규칙 분석 결과 | measurements 전체 데이터 |
| **사용자 관리** | 없음 | 회원가입/로그인 시스템 |
| **데이터 구조** | 분석 결과만 | OCR + Stage 분석 + 모든 측정값 |

---

## 다음 단계 (향후 구현)

1. **FastAPI 백엔드**
   - REST API 엔드포인트
   - 실제 OCR 통합
   - 사용자 인증 (JWT)

2. **Frontend**
   - OCR 데이터 확인/수정 UI
   - 리포트 뷰어
   - 사용자 대시보드

3. **추가 기능**
   - 시계열 분석 (측정 기록 비교)
   - 목표 설정 및 추적
   - 리포트 PDF 내보내기

---

## 문제 해결

### PostgreSQL 연결 문제
```bash
# PostgreSQL 서비스 확인
sudo systemctl status postgresql

# 서비스 시작
sudo systemctl start postgresql

# 연결 테스트
psql -U postgres -d explainmybody -c "SELECT 1;"
```

자세한 문제 해결: [POSTGRESQL_SETUP.md](POSTGRESQL_SETUP.md)

### API 키 확인
```bash
# .env 파일 확인
cat .env

# 필요한 키
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
```

### Ollama 연결 오류
```bash
# Ollama 서버 시작
ollama serve

# 다른 터미널에서 확인
curl http://localhost:11434/api/tags
```

---

## 참고 자료

- [README.md](README.md) - 프로젝트 개요
- [USAGE.md](USAGE.md) - 기존 파이프라인 사용법
- [Database Schema](#데이터베이스-구조) - DB 구조 상세
