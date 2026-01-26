# ExplainMyBody Backend

FastAPI 기반 인바디 분석 및 건강 관리 백엔드 서버

## 프로젝트 구조

```
backend/
│
├── main.py                      # FastAPI 앱 생성 + 라우터 등록
├── database.py                  # PostgreSQL 연결 설정
├── requirements.txt             # 패키지 목록
├── .env.example                 # 환경 변수 예시
│
├── models/                      # SQLAlchemy ORM 모델 (DB 테이블)
│   ├── __init__.py
│   ├── user.py                  # User 테이블
│   ├── health_record.py         # health_records 테이블
│   ├── analysis_report.py       # analysis_reports 테이블
│   └── user_goal.py             # user_goals 테이블
│
├── schemas/                     # Pydantic 모델 (Request/Response 검증)
│   ├── __init__.py
│   ├── user.py                  # UserCreate, UserResponse
│   ├── health_record.py
│   ├── analysis_report.py
│   └── user_goal.py
│
├── repositories/                # DB CRUD 로직
│   ├── __init__.py
│   ├── user_repository.py
│   ├── health_record_repository.py
│   ├── analysis_report_repository.py
│   └── user_goal_repository.py
│
├── services/                    # 비즈니스 로직
│   ├── __init__.py
│   ├── auth_service.py          # 로그인/회원가입
│   ├── ocr_service.py           # OCR 처리 (기존 코드 통합)
│   ├── body_type_service.py     # 체형 분류 (기존 코드 통합)
│   ├── llm_service.py           # LLM API 호출
│   └── health_service.py        # 건강 기록 관련 로직
│
├── routers/                     # API 엔드포인트 (Controller)
│   ├── __init__.py
│   ├── auth.py                  # /api/auth/*
│   ├── users.py                 # /api/users/*
│   ├── health_records.py        # /api/health-records/*
│   ├── analysis.py              # /api/analysis/*
│   └── goals.py                 # /api/goals/*
│
└── utils/                       # 유틸리티
    ├── __init__.py
    └── dependencies.py          # DB 세션, 인증 등
```

## 개발 환경

- **Python**: 3.11
- **OS**: Ubuntu 22.04 (Linux)
- **패키지 관리자**: uv (최상위 디렉토리에서 관리)
- **데이터베이스**: PostgreSQL

## 설치 및 실행

> **중요**: uv 가상환경은 **최상위 디렉토리(`/home/user/ExplainMyBody/`)** 에서 생성하고 관리합니다.
> 
> 자세한 설정 가이드는 [`../UV_QUICKSTART.md`](../UV_QUICKSTART.md)를 참고하세요.

### 0. uv 설치 (처음 한 번만)
```bash
# uv가 설치되어 있지 않은 경우
curl -LsSf https://astral.sh/uv/install.sh | sh
# 또는
pip install uv
```

### 1. 가상환경 생성 및 활성화 (최상위 디렉토리에서)
```bash
# 최상위 디렉토리로 이동
cd /home/user/ExplainMyBody

# uv로 Python 3.11 가상환경 생성
uv venv --python 3.11

# 가상환경 활성화
source .venv/bin/activate
```

### 2. 패키지 설치 (최상위 디렉토리에서)
```bash
# 최상위 디렉토리에서 실행
cd /home/user/ExplainMyBody

# pyproject.toml 기반으로 모든 의존성 설치
uv sync

# 개발 도구 포함 설치
uv sync --group dev
```

### 3. 환경 변수 설정
```bash
cd backend
cp .env.example .env
# .env 파일을 열어서 데이터베이스 연결 정보 등을 수정
```

### 4. 데이터베이스 준비
PostgreSQL이 설치되어 있어야 합니다.
```bash
# PostgreSQL에서 데이터베이스 생성
createdb explainmybody
```

### 5. 서버 실행
```bash
# backend 디렉토리에서 실행
cd backend

# 가상환경이 활성화된 상태에서
python main.py

# 또는 개발 모드로 실행 (자동 재시작)
uvicorn main:app --reload
```

서버가 실행되면 http://localhost:8000 에서 접근 가능합니다.

### 패키지 추가 방법
```bash
# 최상위 디렉토리로 이동
cd /home/user/ExplainMyBody

# 방법 1: 단일 패키지 추가 (자동으로 pyproject.toml 업데이트)
uv add <package-name>

# 개발 전용 패키지 추가
uv add --group dev <package-name>

# 방법 2: 여러 패키지 한 번에 추가 (추천)
# pyproject.toml 파일을 열어서 dependencies 리스트에 직접 추가
nano pyproject.toml  # 또는 code, vim 등

# 예시: LLM 패키지 여러 개 추가
# dependencies = [
#     ...
#     "openai>=1.0,<2.0",
#     "anthropic>=0.18,<1.0",
#     "langchain>=0.1,<1.0",
# ]

# 추가 후 동기화
uv sync

# 선택적 의존성 그룹 사용 (pyproject.toml에 정의)
# [dependency-groups]
# llm = ["openai>=1.0", "anthropic>=0.18"]

# 특정 그룹만 설치
uv sync --group llm
```

## API 문서

서버 실행 후 다음 URL에서 자동 생성된 API 문서를 확인할 수 있습니다:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc






## 개발 진행 상황

디렉토리 구조 및 파일 생성 완료
models/*, services/*, utils/*, database.py, main.py, requirements.txt, .env.example, .env 까지 확인 완료
각 파일별로 추후 수정이 필요한 부분은 #fixme 주석으로 표시해둠.


## 추가적인 진행이 필요한 부분

1. schemas/*, repositories/*, routers/* 파일들 확인 필요.
2. 각 기능별로 기능이 필요한 데이터 형식에 맞춰서 데이터를 전달하는지, 데이터를 잘 받아서 처리하는지 확인 필요.
    - 변수명 확인 필요
    - 데이터 형식 확인 필요
3. 각 기능별로 필요한 API 엔드포인트가 정말로 있는지 확인 필요.
4. 정의되어있는 엔드 포인트와 실제 코드의 엔드포인트가 일치하는지 확인 필요.




## 📊 데이터 흐름 예시

### 시나리오 1: OCR을 통한 인바디 등록 및 분석
```
1. 사용자가 인바디 이미지 업로드
   POST /api/health-records/ocr
   
2. OCR 서비스가 데이터 추출
   InBodyMatcher.extract_and_match()
   
3. 체형 분류 자동 실행
   BodyCompositionAnalyzer.analyze_full_pipeline()
   
4. 건강 기록 저장 (체형 정보 포함)
   HealthRecord 생성
   
5. 사용자가 분석 요청
   POST /api/analysis/{record_id}
   
6. LLM이 상태 분석
   LLMService.analyze_health_status()
   
7. 분석 리포트 저장 및 반환
   AnalysisReport 생성
```

### 시나리오 2: 목표 설정 및 주간 계획 생성
```
1. 사용자가 목표 생성
   POST /api/goals/
   body: { "goal_description": "3개월 내 체지방 5% 감량" }
   
2. 주간 계획 생성 요청
   POST /api/goals/{goal_id}/generate-plan
   
3. 최신 인바디 데이터 + 분석 결과 조회
   HealthRecordRepository.get_latest()
   AnalysisReportRepository.get_by_record_id()
   
4. LLM이 주간 계획 생성
   LLMService.generate_weekly_plan()
   
5. 목표에 계획 저장 및 반환
   UserGoal.weekly_plan 업데이트
```

## 🔧 추가 작업 필요 사항

### 1. LLM API 연결
- `services/llm_service.py`에 실제 LLM API 호출 로직 추가
- OpenAI, Anthropic 등의 API 키 설정
- 프롬프트 엔지니어링 최적화

### 2. 인증/보안
- JWT 토큰 기반 인증 구현
- 비밀번호 해싱 (bcrypt)
- API 엔드포인트 권한 검증

### 3. 프론트엔드 개발
- `frontend/` 디렉토리에 React/Vue 앱 생성
- 백엔드 API 연동
- UI/UX 디자인

### 4. 배포
- Docker 컨테이너화
- PostgreSQL 프로덕션 설정
- 환경별 설정 분리 (dev/staging/prod)

## 📝 참고사항

### Pydantic과 SQLAlchemy의 타입 불일치 방지
- **Pydantic 스키마**: API 요청/응답 검증
- **SQLAlchemy 모델**: 데이터베이스 테이블
- 두 계층을 분리하여 타입 안전성 확보

### JSONB 활용
- `health_records.measurements` 필드는 JSONB 타입
- 인바디 측정 항목이 추가/변경되어도 스키마 변경 불필요
- GIN 인덱스로 JSONB 내부 검색 가능

### 기존 코드와의 호환성
- OCR 및 체형 분류 코드는 그대로 사용
- `sys.path.append()`로 기존 모듈 임포트
- 추후 패키지 구조 정리 가능



## 주요 API 엔드포인트

### 인증 (`/api/auth/*`)
- `POST /api/auth/register`      : 회원가입 (이메일, 비밀번호 등)
- `POST /api/auth/login`         : 로그인 및 세션 유지
- `GET  /api/auth/me`            : 현재 로그인한 사용자 정보 조회

### 사용자 (`/api/users/*`)
- `GET  /api/users/{user_id}`    : 특정 사용자 정보 조회
- `GET  /api/users/`             : 전체 사용자 목록 (관리자 모드 필요)
- `GET  /api/users/{user_id}/statistics` : 사용자의 전체 기록 및 분석 통계 조회

### 건강 기록 (`/api/health-records/*`)
- `POST /api/health-records/`               : 건강 기록 직접 입력
- `POST /api/health-records/ocr`            : 인바디 이미지 업로드 및 OCR 자동 등록
- `GET  /api/health-records/{record_id}`    : 특정 건강 기록 상세 조회
- `GET  /api/health-records/user/{user_id}`  : 사용자의 건강 기록 목록 조회
- `GET  /api/health-records/user/{user_id}/latest` : 가장 최근 등록된 인바디 데이터 조회

### 분석 (`/api/analysis/*`)
- `POST /api/analysis/{record_id}`          : 인바디 데이터에 대한 AI(LLM) 종합 분석 실행
- `GET  /api/analysis/{report_id}`          : 특정 분석 리포트 내용 조회
- `GET  /api/analysis/record/{record_id}`   : 특정 운동 기록에 매칭된 분석 리포트 조회
- `GET  /api/analysis/user/{user_id}`       : 사용자가 지금까지 받은 모든 분석 리포트 목록 조회

### 목표 및 리포트 (`/api/goals/*`)
- `POST /api/goals/`                        : 새로운 건강 개선 목표 설정
- `POST /api/goals/{goal_id}/generate-plan` : 설정된 목표에 따른 AI 주간 맞춤 계획 생성
- `GET  /api/goals/{goal_id}`               : 특정 목표 정보 및 생성된 주간 계획 조회
- `GET  /api/goals/user/{user_id}`          : 사용자의 모든 과거/현재 목표 목록 조회
- `GET  /api/goals/user/{user_id}/active`   : 현재 진행 중인 활성 목표 조회
- `PATCH /api/goals/{goal_id}`              : 목표 내용 수정
- `POST /api/goals/{goal_id}/complete`      : 목표 달성 완료 처리
- `DELETE /api/goals/{goal_id}`             : 목표 데이터 삭제


## 기존 코드 통합

### OCR 서비스
- 위치: `services/ocr_service.py`
- 기존 코드: `../scr/ocr/ocr_test.py`의 `InBodyMatcher` 클래스 사용

### 체형 분류 서비스
- 위치: `services/body_type_service.py`
- 기존 코드: `../rule_based_bodytype/body_analysis/pipeline.py`의 `BodyCompositionAnalyzer` 사용

### LLM 서비스
- 위치: `services/llm_service.py`
- 현재는 템플릿 응답, 실제 LLM API 연결은 팀원이 추가 예정

## 개발 참고사항

- **데이터 타입 일치**: Pydantic 스키마를 사용하여 요청/응답 데이터 검증
- **JSONB 활용**: `health_records.measurements` 필드는 JSONB로 유연한 데이터 저장
- **자동 체형 분류**: 건강 기록 생성 시 자동으로 체형 분류 실행
- **LLM 통합**: `services/llm_service.py`에 실제 LLM API 호출 로직 추가 필요
