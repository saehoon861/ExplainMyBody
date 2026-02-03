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
├── models/                      # SQLAlchemy ORM 모델 (DB 테이블)
│   ├── __init__.py
│   ├── user.py                  # users 테이블
│   ├── health_record.py         # health_records 테이블
│   ├── analysis_report.py       # inbody_analysis_reports 테이블 (구 analysis_reports)
│   ├── user_detail.py           # user_details 테이블 (구 user_goals, 사용자 세부 목표)
│   ├── weekly_plan.py           # weekly_plans 테이블 (주간 계획)
│   ├── llm_interaction.py       # llm_interactions 테이블 (LLM 출력 결과)
│   ├── human_feedback.py        # human_feedbacks 테이블 (사용자 피드백)
│   └── user_goal.py             # user_goals 테이블 (Legacy, UserDetail로 대체됨)
│
├── schemas/                     # Pydantic 모델 (팀별 분리)
│   ├── __init__.py
│   ├── README.md                # 스키마 구조 및 팀 담당 가이드
│   ├── common.py                # 공통 스키마 (User, HealthRecord)
│   ├── llm.py                   # LLM 팀 전담 (InbodyAnalysisReport, UserDetail, WeeklyPlan)
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
│       ├── user_detail_repository.py  # UserDetail 관리
│       ├── llm_interaction_repository.py
│       ├── human_feedback_repository.py
│       ├── weekly_plan_repository.py  # WeeklyPlan 관리
│       └── user_goal_repository.py    # Legacy
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
│   │   └── goals.py             # /api/goals/* (UserDetail 사용)
│   └── ocr/
│       └── health_records.py    # /api/health-records/*
│
├── utils/                       # 유틸리티
│   ├── __init__.py
│   └── dependencies.py          # DB 세션, 인증 등
│
└── migrations/                  # 데이터베이스 마이그레이션
```

## 🚀 빠른 시작 (Quickstart)

백엔드 서버 설치 및 실행 방법은 **[BACKEND_QUICKSTART.md](./BACKEND_QUICKSTART.md)**를 참고하세요.

---

## 🗄️ 데이터베이스 구조 (Relationship)

주요 모델 간의 관계는 다음과 같습니다.

- **User (1) : (N) HealthRecord**
    - 한 명의 사용자는 여러 개의 건강 기록(인바디 측정 결과)을 가집니다.
- **User (1) : (N) InbodyAnalysisReport**
    - 한 명의 사용자는 여러 개의 분석 리포트를 가집니다.
- **HealthRecord (1) : (N) InbodyAnalysisReport**
    - 하나의 건강 기록에 대해 여러 분석(버전별, 재분석 등)이 존재할 수 있습니다.
- **User (1) : (N) UserDetail**
    - 사용자는 여러 목표/상세 정보를 가질 수 있습니다 (현재 활성화된 목표는 하나).
- **User (1) : (N) WeeklyPlan**
    - 한 명의 사용자는 여러 개의 주간 계획표를 생성할 수 있습니다.
- **User (1) : (N) LLMInteraction**
    - 한 명의 사용자는 여러 개의 LLM 상호작용 기록을 가집니다.
- **LLMInteraction (1) : (N) HumanFeedback**
    - 하나의 LLM 출력 결과에 대해 여러 개의 사용자 피드백이 존재할 수 있습니다.

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
  - AI 상태 분석 (InbodyAnalysisReport)
  - 목표 및 상세 설정 (UserDetail)
  - 주간 계획 생성 (WeeklyPlan)
- **파일 예시**:
  - `services/llm/llm_service.py`
  - `routers/llm/analysis.py`
  - `routers/llm/goals.py`
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
   InbodyAnalysisReport 생성
```

### 시나리오 2: 목표 설정 및 주간 계획 생성
```
1. 사용자가 목표/상세정보 생성 (UserDetail)
   POST /api/goals/
   body: { "goal_type": "다이어트", "goal_description": "3개월 내 5kg 감량" }
   
2. 주간 계획 생성 요청
   POST /api/goals/plan/prepare
   
3. 최신 인바디 데이터 + 분석 결과 + 사용자 목표 조회
   HealthRecordRepository.get_latest()
   AnalysisReportRepository.get_by_record_id()
   UserDetailRepository.create() (또는 조회)
   
4. LLM이 주간 계획 생성 (WeeklyPlan)
   LLMService.generate_weekly_plan()
   
5. 주간 계획 저장
   WeeklyPlan 생성
```

---

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
| **PUT** | `/api/users/{user_id}/goal` | 목표/체중 수정 | `UserDetailRepository.update` | **수정**: 목표 상세 내용 및 시작/목표 체중 업데이트 |

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
| **GET** | `/api/health-records/user/{user_id}/latest` | 최신 기록 조회 | `HealthRecordRepository.get_latest` | **조회**: 사용자의 가장 최신 건강 기록 반환 |
| **GET** | `/api/health-records/{record_id}/analysis/prepare` | **LLM1 입력 준비** | `HealthService.prepare_status_analysis` | **처리**: LLM 분석에 필요한 포맷으로 데이터 가공하여 반환 |

### 4. 🧠 분석 (`routers/llm/analysis.py`)
- **담당**: LLM 팀
- **Service**: `HealthService`, `LLMService`
- **Repo**: `AnalysisReportRepository` (Target: `InbodyAnalysisReport` Table)

| Method | URL | 설명 | Service / Repository | 결과 / DB 작업 |
| :--- | :--- | :--- | :--- | :--- |
| **POST** | `/api/analysis/{record_id}` | **상태 분석 실행** | `HealthService.analyze_health_record`<br>→ `LLMService`<br>→ `AnalysisReportRepository` | **처리**: LLM 호출하여 건강 상태 분석<br>**DB 생성**: `inbody_analysis_reports`에 분석 결과 저장 |
| **GET** | `/api/analysis/{report_id}` | 리포트 조회 | `AnalysisReportRepository.get_by_id` | **조회**: 특정 리포트 내용 반환 |
| **GET** | `/api/analysis/record/{record_id}` | 기록별 리포트 | `AnalysisReportRepository` | **조회**: 특정 건강 기록에 연결된 리포트 반환 |
| **GET** | `/api/analysis/user/{user_id}` | 유저 리포트 목록 | `AnalysisReportRepository` | **조회**: 유저의 모든 리포트 반환 |

### 5. 🎯 목표 (`routers/llm/goals.py`)
- **담당**: LLM 팀
- **Repo**: `UserDetailRepository` (Target: `UserDetail` Table), `AnalysisReportRepository`

> **Note**: 엔드포인트는 `/api/goals`를 유지하지만, 내부적으로 `UserDetail` 테이블을 사용하여 사용자의 목표 및 상세 정보를 관리합니다.

| Method | URL | 설명 | Service / Repository | 결과 / DB 작업 |
| :--- | :--- | :--- | :--- | :--- |
| **POST** | `/api/goals/` | 목표/상세 생성 | `UserDetailRepository.create` | **DB 생성**: 새로운 `UserDetail` 저장 |
| **POST** | `/api/goals/plan/prepare` | **LLM2 입력 준비** | `HealthService.prepare_goal_plan` | **처리**: 주간 계획 생성을 위한 LLM 입력 데이터 가공 반환<br>(HealthRecord + AnalysisReport + UserDetail 조합) |
| **GET** | `/api/goals/user/{user_id}/active` | 활성 목표 조회 | `UserDetailRepository.get_active_details` | **조회**: 현재 진행 중인 목표 반환 |
| **GET** | `/api/goals/user/{user_id}` | 전체 목표 조회 | `UserDetailRepository.get_all_details` | **조회**: 사용자의 모든 목표 히스토리 반환 |
| **PATCH** | `/api/goals/{goal_id}` | 목표 수정 | `UserDetailRepository.update` | **DB 수정**: 목표 내용 업데이트 |
| **DELETE** | `/api/goals/{goal_id}` | 목표 삭제 | `UserDetailRepository.delete` | **DB 삭제**: 목표 삭제 |
| **POST** | `/api/goals/{goal_id}/complete` | 목표 완료 | `UserDetailRepository.update` | **DB 수정**: `ended_at`을 현재 시간으로 설정 |

### 6. 📅 주간 계획 (`routers/llm/weekly_plans.py`)
- **담당**: LLM 팀
- **Repo**: `WeeklyPlanRepository` (Target: `WeeklyPlan` Table)

| Method | URL | 설명 | Service / Repository | 결과 / DB 작업 |
| :--- | :--- | :--- | :--- | :--- |
| **POST** | `/api/weekly-plans/` | 주간 계획 생성 | `WeeklyPlanRepository.create` | **DB 생성**: 새로운 주간 계획 저장 |
| **GET** | `/api/weekly-plans/{plan_id}` | 특정 계획 조회 | `WeeklyPlanRepository.get_by_id` | **조회**: 특정 주간 계획 반환 |
| **GET** | `/api/weekly-plans/user/{user_id}` | 사용자별 목록 조회 | `WeeklyPlanRepository.get_by_user` | **조회**: 사용자의 모든 주간 계획 반환 |
| **GET** | `/api/weekly-plans/user/{user_id}/week/{week_number}` | 특정 주차 조회 | `WeeklyPlanRepository.get_by_week` | **조회**: 특정 주차의 계획 반환 |
| **PATCH** | `/api/weekly-plans/{plan_id}` | 계획 수정 | `WeeklyPlanRepository.update` | **DB 수정**: 계획 내용 업데이트 |
| **DELETE** | `/api/weekly-plans/{plan_id}` | 계획 삭제 | `WeeklyPlanRepository.delete` | **DB 삭제**: 계획 삭제 |
