# ExplainMyBody Backend

FastAPI 기반 인바디 분석 및 건강 관리 백엔드 서버

## 프로젝트 구조

> **팀 담당 기준으로 재구성됨**: 각 팀원의 담당 영역(common, llm, ocr)으로 디렉토리를 분리하여 Merge Conflict를 최소화

```
backend/
│
├── main.py                      # FastAPI 앱 생성 + 라우터 등록
├── app_state.py                 # 애플리케이션 상태 관리
├── database.py                  # PostgreSQL 연결 설정
├── requirements.txt             # 패키지 목록
├── .env.example                 # 환경 변수 예시
├── .python-version              # Python 버전 명시
│
├── models/                      # SQLAlchemy ORM 모델 (DB 테이블)  *DB설계 수정필요
│   ├── __init__.py
│   ├── user.py                  # User 테이블
│   ├── health_record.py         # health_records 테이블
│   ├── analysis_report.py       # analysis_reports 테이블
│   └── user_goal.py             # user_goals 테이블
│
├── schemas/                     # Pydantic 모델 (팀별 분리)
│   ├── __init__.py
│   ├── README.md                # 스키마 구조 및 팀 담당 가이드
│   ├── common.py                # 공통 스키마 (User, HealthRecord)
│   ├── llm.py                   # LLM 팀 전담 (AnalysisReport, UserGoal, LLM 입출력)
│   ├── inbody.py                # OCR 팀 전담 (InBody 데이터 검증)
│   └── body_type.py             # OCR 팀 전담 (체형 분석)
│
├── repositories/                # DB CRUD 로직 (팀별 분리)
│   ├── __init__.py
│   ├── common/
│   │   ├── user_repository.py
│   │   └── health_record_repository.py
│   └── llm/
│       ├── analysis_report_repository.py
│       └── user_goal_repository.py
│
├── services/                    # 비즈니스 로직 (팀별 분리)
│   ├── __init__.py
│   ├── common/
│   │   ├── auth_service.py      # 로그인/회원가입
│   │   └── health_service.py    # 건강 기록 관련 로직
│   ├── llm/
│   │   └── llm_service.py       # LLM API 호출 (상태 분석, 주간 계획 생성)
│   └── ocr/
│       ├── ocr_service.py       # OCR 처리
│       ├── inbody_matcher.py    # InBody 데이터 추출 및 매칭
│       └── body_type_service.py # 체형 분류
│
├── routers/                     # API 엔드포인트 (팀별 분리)
│   ├── __init__.py
│   ├── common/
│   │   ├── auth.py              # /api/auth/*
│   │   └── users.py             # /api/users/*
│   ├── llm/
│   │   ├── analysis.py          # /api/analysis/*
│   │   └── goals.py             # /api/goals/*
│   └── ocr/
│       └── health_records.py    # /api/health-records/*
│
├── utils/                       # 유틸리티
│   ├── __init__.py
│   └── dependencies.py          # DB 세션, 인증 등
│
└── migrations/                  # 데이터베이스 마이그레이션
    └── 001_update_health_records_body_types.sql
```

## 🚀 빠른 시작 (Quickstart)

백엔드 서버 설치 및 실행 방법은 **[BACKEND_QUICKSTART.md](./BACKEND_QUICKSTART.md)**를 참고하세요.

---

## 팀 담당 기준 디렉토리 구조

백엔드는 **팀원별 담당 영역**에 따라 `common`, `llm`, `ocr` 세 가지 카테고리로 구성되어 있습니다.

### 📂 디렉토리 분류 기준

#### `common/` - 공통 영역
- **담당**: 양 팀 공통 사용
- **포함 내용**: 
  - 사용자 인증 (로그인, 회원가입)
  - 사용자 정보 관리
  - 건강 기록 기본 CRUD
- **파일 예시**:
  - `services/common/auth_service.py`
  - `routers/common/auth.py`
  - `repositories/common/user_repository.py`
  - `schemas/common.py`

#### `llm/` - LLM 팀 전담
- **담당**: LLM 기능 개발 팀원
- **포함 내용**:
  - AI 상태 분석 (LLM1)
  - 주간 계획 생성 (LLM2)
  - 분석 리포트 및 목표 관리
- **파일 예시**:
  - `services/llm/llm_service.py`
  - `routers/llm/analysis.py`
  - `repositories/llm/analysis_report_repository.py`
  - `schemas/llm.py`

#### `ocr/` - OCR 팀 전담
- **담당**: OCR 및 체형 분석 개발 팀원
- **포함 내용**:
  - 인바디 이미지 OCR 처리
  - 인바디 데이터 추출 및 매칭
  - 체형 분류 (Rule-based)
- **파일 예시**:
  - `services/ocr/ocr_service.py`
  - `services/ocr/body_type_service.py`
  - `routers/ocr/health_records.py`
  - `schemas/inbody.py`

### 🎯 협업 규칙 (Merge Conflict 방지)
1. **OCR 팀원**: `ocr/` 디렉토리 및 OCR 관련 스키마 작업
2. **LLM 팀원**: `llm/` 디렉토리 및 LLM 관련 스키마 작업
3. **공통 영역**: `common/`, `models/` 수정 시 팀원 간 사전 협의 필수

---


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

### 1. 🔐 인증 (`routers/common/auth.py`)
- **담당**: 공통 (Common)
- **Service**: `AuthService` (`services/common/auth_service.py`)

| Method | URL | 설명 | Service / Repository | 결과 / DB 작업 |
| :--- | :--- | :--- | :--- | :--- |
| **POST** | `/api/auth/register` | 회원가입 | `AuthService.register`<br>→ `UserRepository` | **DB 생성**: `users` 테이블에 새 사용자 추가 |
| **POST** | `/api/auth/login` | 로그인 | `AuthService.login`<br>→ `UserRepository` | **조회**: 이메일로 사용자 찾고 정보 반환 |
| **GET** | `/api/auth/me` | 현재 유저 조회 | `AuthService.get_current_user`<br>→ `UserRepository` | **조회**: `user_id`로 사용자 정보 반환 |
| **POST** | `/api/auth/logout` | 로그아웃 | `AuthService.logout` | **없음**: 클라이언트 측 로그아웃 처리용 |

### 2. 👤 사용자 (`routers/common/users.py`)
- **담당**: 공통 (Common)
- **Repo**: `UserRepository` (`repositories/common/user_repository.py`)

| Method | URL | 설명 | Repository | 결과 / DB 작업 |
| :--- | :--- | :--- | :--- | :--- |
| **GET** | `/api/users/{user_id}` | 특정 유저 조회 | `UserRepository.get_by_id` | **조회**: 해당 ID의 사용자 정보 반환 |
| **GET** | `/api/users/` | 전체 유저 목록 | `UserRepository.get_all` | **조회**: 모든 사용자 목록 반환 (관리자용) |
| **GET** | `/api/users/{user_id}/statistics` | 유저 통계 | `UserRepository`<br>`HealthRecordRepository`<br>`AnalysisReportRepository` | **조회**: 총 건강 기록 수, 총 리포트 수 집계하여 반환 |

### 3. 📝 건강 기록 (`routers/ocr/health_records.py`)
- **담당**: OCR 팀
- **Service**: `HealthService`, `OCRService`, `BodyTypeService`

| Method | URL | 설명 | Service / Repository | 결과 / DB 작업 |
| :--- | :--- | :--- | :--- | :--- |
| **POST** | `/api/health-records/ocr/extract` | **Step 1: OCR 추출** | `OCRService.extract_inbody_data` | **처리**: 이미지에서 텍스트 추출<br>**DB 변화 없음**: 원시 데이터 반환 (프론트 검증용) |
| **POST** | `/api/health-records/ocr/validate` | **Step 2: 검증 및 저장** | `BodyTypeService.get_full_analysis`<br>`HealthService`<br>→ `HealthRecordRepository` | **처리**: 체형 분석 실행<br>**DB 생성**: `health_records`에 인바디+체형결과 저장 |
| **POST** | `/api/health-records/` | 수동 입력 | `HealthService`<br>→ `HealthRecordRepository` | **DB 생성**: 직접 입력한 데이터 저장 |
| **GET** | `/api/health-records/{record_id}` | 기록 상세 조회 | `HealthRecordRepository.get_by_id` | **조회**: 특정 건강 기록 반환 |
| **GET** | `/api/health-records/user/{user_id}` | 유저 기록 목록 | `HealthRecordRepository.get_by_user` | **조회**: 해당 유저의 모든 기록 반환 |
| **GET** | `/api/health-records/{record_id}/analysis/prepare` | **LLM1 입력 준비** | `HealthService.prepare_status_analysis` | **처리**: LLM 분석에 필요한 포맷으로 데이터 가공하여 반환 |

### 4. 🧠 분석 (`routers/llm/analysis.py`)
- **담당**: LLM 팀
- **Service**: `HealthService` (`services/llm` 폴더 내부 로직 활용)

| Method | URL | 설명 | Service / Repository | 결과 / DB 작업 |
| :--- | :--- | :--- | :--- | :--- |
| **POST** | `/api/analysis/{record_id}` | **상태 분석 실행** | `HealthService.analyze_health_record`<br>→ `LLMService`<br>→ `AnalysisReportRepository` | **처리**: LLM 호출하여 건강 상태 분석<br>**DB 생성**: `analysis_reports`에 분석 결과 저장 |
| **GET** | `/api/analysis/{report_id}` | 리포트 조회 | `AnalysisReportRepository.get_by_id` | **조회**: 특정 리포트 내용 반환 |
| **GET** | `/api/analysis/record/{record_id}` | 기록별 리포트 | `AnalysisReportRepository` | **조회**: 특정 건강 기록에 연결된 리포트 반환 |
| **GET** | `/api/analysis/user/{user_id}` | 유저 리포트 목록 | `AnalysisReportRepository` | **조회**: 유저의 모든 리포트 반환 |

### 5. 🎯 목표 (`routers/llm/goals.py`)
- **담당**: LLM 팀
- **Repo**: `UserGoalRepository` (`repositories/llm/user_goal_repository.py`)

| Method | URL | 설명 | Service / Repository | 결과 / DB 작업 |
| :--- | :--- | :--- | :--- | :--- |
| **POST** | `/api/goals/` | 목표 생성 | `UserGoalRepository.create` | **DB 생성**: 새로운 목표 저장 |
| **POST** | `/api/goals/plan/prepare` | **LLM2 입력 준비** | `HealthService.prepare_goal_plan` | **처리**: 주간 계획 생성을 위한 LLM 입력 데이터 가공 반환 |
| **GET** | `/api/goals/user/{user_id}/active` | 활성 목표 조회 | `UserGoalRepository.get_active_goals` | **조회**: 현재 진행 중인 목표 반환 |
| **PATCH** | `/api/goals/{goal_id}` | 목표 수정 | `UserGoalRepository.update` | **DB 수정**: 목표 내용 업데이트 |
| **POST** | `/api/goals/{goal_id}/complete` | 목표 완료 | `UserGoalRepository.update` | **DB 수정**: `ended_at`을 현재 시간으로 설정 (완료 처리) |


## 기존 코드 통합

### OCR 서비스
- **위치**: `services/ocr/ocr_service.py`
- **InBody 데이터 추출**: `services/ocr/inbody_matcher.py` (기존 `../scr/ocr/ocr_test.py`의 `InBodyMatcher` 클래스 통합)
- **기능**: 인바디 이미지에서 텍스트 추출 및 데이터 매칭

### 체형 분류 서비스
- **위치**: `services/ocr/body_type_service.py`
- **기존 코드**: `../rule_based_bodytype/body_analysis/pipeline.py`의 `BodyCompositionAnalyzer` 통합
- **기능**: Rule-based 체형 분석 (Stage 2, Stage 3)

### LLM 서비스
- **위치**: `services/llm/llm_service.py`
- **기능**: 
  - LLM1: 인바디 데이터 기반 상태 분석
  - LLM2: 목표 기반 주간 계획 생성
- **참고**: 실제 LLM API 연동 코드 포함 (OpenAI/Anthropic 등)

## 개발 참고사항

- **데이터 타입 일치**: Pydantic 스키마를 사용하여 요청/응답 데이터 검증
- **JSONB 활용**: `health_records.measurements` 필드는 JSONB로 유연한 데이터 저장
- **자동 체형 분류**: 건강 기록 생성 시 자동으로 체형 분류 실행
- **LLM 통합**: `services/llm_service.py`에 실제 LLM API 호출 로직 추가 필요
