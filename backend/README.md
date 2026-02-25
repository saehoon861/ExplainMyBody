# ExplainMyBody Backend

FastAPI 기반 인바디 분석 및 건강 관리 백엔드 서버

## 프로젝트 구조

> **팀 담당 기준으로 재구성됨**: 각 팀원의 담당 영역(common, llm, ocr)으로 디렉토리를 분리하여 Merge Conflict를 최소화

```
backend/
├── main.py                      # FastAPI 엔트리포인트 (앱 생성 및 라우터 등록)
├── app_state.py                 # 중요 리소스(OCR 엔진 등) 전역 상태 관리 및 공유
├── database.py                  # 데이터베이스(PostgreSQL) 연결 및 세션 설정
├── exceptions.py                # 글로벌 예외 처리기 및 커스텀 에러 정의
├── pyproject.toml               # uv 기반 프로젝트 의존성 관리
├── .env.example                 # 로컬 개발용 환경변수 템플릿
│
├── models/                      # SQLAlchemy ORM 모델 (DB 테이블 정의)
│   ├── common.py                # 공통 Base 모델
│   ├── user.py                  # 사용자 정보
│   ├── health_record.py         # 인바디 측정 데이터 기록
│   ├── analysis_report.py       # AI 분석 결과 리포트
│   ├── user_detail.py           # 사용자 목표 및 신체 특이사항 (Preferences)
│   └── weekly_plan.py           # AI 생성 주간 운동/식단 계획
│
├── schemas/                     # Pydantic 모델 (입출력 검증 및 DTO)
│   ├── common.py                # User, HealthRecord 관련 스키마
│   ├── llm.py                   # 분석 리포트, 목표, 주간 계획 관련 스키마
│   ├── inbody.py                # 인바디 원본 데이터 검증
│   └── body_type.py             # 체형 분석 결과 데이터 구조
│
├── repositories/                # 데이터 액세스 계층 (CRUD 로직)
│   ├── common/                  # User, HealthRecord DB 접근
│   └── llm/                     # Analysis, Details, WeeklyPlan DB 접근
│
├── services/                    # 비즈니스 로직 계층
│   ├── common/
│   │   ├── auth_service.py      # 사용자 인증 및 권한 관리
│   │   └── health_service.py    # 인바디 데이터 관리 및 준비 로직
│   ├── llm/
│   │   ├── llm_service.py       # AI 기능 통합 서비스
│   │   ├── agent_graph.py       # LangGraph 기반 상태 분석 워크플로우
│   │   ├── weekly_plan_graph.py # LangGraph 기반 주간 계획 생성 워크플로우
│   │   ├── prompt_generator.py  # 동적 프롬프트 생성기
│   │   └── llm_clients.py       # LLM 모델(OpenAI, Claude 등) 인스턴스 관리
│   └── ocr/
│       ├── ocr_service.py       # PaddleOCR 기반 텍스트 추출 가공
│       ├── inbody_matcher.py    # 인바디 결과지 좌표 기반 데이터 매칭
│       └── body_type_service.py # 룰 기반 체형 분류 엔진
│
├── routers/                     # API 엔드포인트 계층 (Controller)
│   ├── common/
│   │   ├── auth.py              # 회원가입/로그인 (`/api/auth`)
│   │   └── users.py             # 사용자 관리 (`/api/users`)
│   ├── llm/
│   │   ├── analysis.py          # 신체 상태 분석 (`/api/analysis`)
│   │   ├── details.py           # 목표 및 선호도 (`/api/details`)
│   │   └── weekly_plans.py      # 주간 계획 생성/조회 (`/api/weekly-plans`)
│   └── ocr/
│       └── health_records.py    # 인바디 업로드 및 데이터 추출 (`/api/health-records`)
│
├── utils/                       # 전역 유틸리티 (인증 의존성 등)
└── uv.lock                      # uv 의존성 잠금 파일
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

### 시나리오 1: OCR 인바디 등록 → 인바디 신체 분석
```
1. 인바디 이미지 업로드 (프론트: InBodyAnalysis.jsx)
   POST /api/health-records/ocr/extract
   → PaddleOCR로 39개 신체 지표 추출, DB 저장 없이 JSON 반환

2. 사용자가 OCR 결과 확인·수정 후 저장
   POST /api/health-records/ocr/validate?user_id={id}
   → Rule-based 체형 분석 자동 실행 후 health_records 저장

3. 인바디 분석가 챗봇 진입 시 LLM1 분석 실행
   POST /api/analysis/{record_id}?user_id={id}
   → LangGraph로 상태 분석, inbody_analysis_reports 저장, thread_id 발급

4. 인바디 분석가와 후속 대화
   POST /api/analysis/{report_id}/chat
   → thread_id 기반 멀티턴 맥락 유지
```

### 시나리오 2: 주간 운동 계획 생성 및 조정
```
1. 운동 플래너 진입 조건 확인 (LLM1 분석 완료 여부)
   GET /api/analysis/record/{record_id}
   → 분석 리포트 없으면 null 반환, 플래너 잠금

2. 사용자가 목표·운동 선호도·특이사항 입력 후 계획 생성
   POST /api/weekly-plans/session?user_id={id}
   → LangGraph로 주간 운동·식단 계획 생성, weekly_plans 저장, plan_id + thread_id 발급

3. 운동 플래너와 후속 대화 (실시간 스트리밍)
   POST /api/weekly-plans/chat/stream?user_id={id}
   → SSE 스트리밍으로 토큰 단위 응답, 계획 조정(강도·식단·플랜 수정 등)
```

---

## 주요 API 엔드포인트

> **⚠️ 주의**: 이 섹션은 **프론트엔드(`frontend/src/pages`, `frontend/src/services`)가 실제로 호출하는 URL**만 기재합니다.
> 백엔드에 구현되어 있지만 프론트와 연결되지 않은 엔드포인트는 하단 [미사용 API](#-미사용-api-백엔드-구현-완료-프론트-미연결) 섹션을 참고하세요.

### 1. 🔐 인증 (`/api/auth`)

| Method | URL | 설명 | 호출 위치 |
| :--- | :--- | :--- | :--- |
| **POST** | `/api/auth/register` | 새 사용자 계정 생성. 이메일·비밀번호·신체 정보·목표를 받아 `users` 테이블에 저장하고 생성된 사용자 정보를 반환 | `authService.js` → `Signup.jsx` |
| **POST** | `/api/auth/login` | 이메일·비밀번호로 로그인. 매칭 성공 시 사용자 전체 정보(인바디 데이터 포함)를 반환하며, 클라이언트는 `localStorage`에 저장 | `authService.js` → `Login.jsx` |

### 2. 👤 사용자 (`/api/users`)

| Method | URL | 설명 | 호출 위치 |
| :--- | :--- | :--- | :--- |
| **PUT** | `/api/users/{user_id}/goal` | 사용자의 운동 목표(시작 체중, 목표 체중, 목표 타입, 세부 설명)를 수정하고 최신 사용자 정보를 반환 | `authService.js`, `Dashboard.jsx` |

### 3. 📝 인바디 OCR (`/api/health-records`)

| Method | URL | 설명 | 호출 위치 |
| :--- | :--- | :--- | :--- |
| **POST** | `/api/health-records/ocr/extract` | **[OCR Step 1]** 업로드된 인바디 이미지를 PaddleOCR로 분석해 39개 신체 지표를 JSON으로 추출. DB 저장 없이 원시 데이터만 반환 (프론트에서 사용자가 수정 가능) | `inbodyService.js`, `InBodyAnalysis.jsx` |
| **POST** | `/api/health-records/ocr/validate?user_id=` | **[OCR Step 2]** 사용자가 검토·수정한 인바디 데이터를 최종 저장. 저장 전에 Rule-based 체형 분석(`body_type1`, `body_type2`)을 자동 실행하고 결과를 `health_records` 테이블에 함께 저장 | `inbodyService.js`, `InBodyAnalysis.jsx` |
| **GET** | `/api/health-records/user/{user_id}?limit=` | 사용자의 인바디 기록 목록을 최신순으로 조회. `limit` 파라미터로 개수 제한 가능 (기본 20개) | `inbodyService.js`, `Dashboard.jsx`, `ChatbotSelector.jsx` |

### 4. 🤖 인바디 분석 챗봇(`/api/analysis`)

> **인바디 분석 전문가** 챗봇이 사용하는 엔드포인트입니다.
> LangGraph 기반 상태 분석 워크플로우(`agent_graph.py`)로 동작하며, `inbody-analyst` 챗봇과 연결됩니다.

| Method | URL | 설명 | 호출 위치 |
| :--- | :--- | :--- | :--- |
| **POST** | `/api/analysis/{record_id}?user_id=` | **[LLM1 최초 분석]** 지정한 건강 기록 ID를 기반으로 LLM이 인바디 상태 분석을 수행. 이전 인바디 기록과 비교 분석 포함. 결과를 `inbody_analysis_reports` 테이블에 저장하고 요약(`summary`) + 전체 분석(`content`) + `thread_id` 반환 | `ChatbotSelector.jsx` (분석 버튼), `Chatbot.jsx` (inbody-analyst 초기화) |
| **GET** | `/api/analysis/record/{record_id}` | 특정 건강 기록에 연결된 분석 리포트가 이미 존재하는지 확인. 운동 플래너 잠금 해제 조건 검사에 사용 (분석 미완료 시 null 반환) | `inbodyService.js`, `ChatbotSelector.jsx` |
| **POST** | `/api/analysis/{report_id}/chat` | **[LLM1 후속 대화]** 분석 리포트 ID와 `thread_id`를 기반으로 인바디 관련 후속 질문에 답변. LangGraph 멀티턴 맥락 유지 | `Chatbot.jsx` (inbody-analyst 대화) |

### 5. 🤖 주간 계획 작성 챗봇 (`/api/weekly-plans`)

> **운동 플래너 전문가** 챗봇이 사용하는 엔드포인트입니다.
> LangGraph 기반 주간 계획 생성 워크플로우(`weekly_plan_graph.py`)로 동작하며, `workout-planner` 챗봇과 연결됩니다.

| Method | URL | 설명 | 호출 위치 |
| :--- | :--- | :--- | :--- |
| **POST** | `/api/weekly-plans/session?user_id=` | **[LLM2 최초 계획 생성]** 사용자 목표(`goal`), 운동 선호도(`preferences`), 건강 특이사항(`health_specifics`), 인바디 기록 ID를 받아 맞춤 주간 운동·식단 계획을 생성. 결과를 `weekly_plans` 테이블에 저장하고 `plan_id` + `thread_id` + 계획 내용 반환 | `ChatbotSelector.jsx` (플랜 생성 버튼), `Chatbot.jsx` (workout-planner 초기화) |
| **POST** | `/api/weekly-plans/chat/stream?user_id=` | **[LLM2 후속 대화 - 스트리밍]** 운동 플랜 ID와 `thread_id`를 기반으로 계획 조정 요청(운동 강도, 식단, 플랜 수정 등)에 대해 **SSE(Server-Sent Events) 스트리밍**으로 토큰 단위 실시간 응답 | `Chatbot.jsx` (workout-planner 대화) |

---

## ⚠️ 미사용 API (백엔드 구현 완료, 프론트 미연결)

아래 엔드포인트는 백엔드에 구현되어 있으나 현재 프론트엔드에서 호출하지 않습니다.

| Method | URL | 비고 |
| :--- | :--- | :--- |
| **GET** | `/api/auth/me` | 현재 로그인 유저 조회 |
| **POST** | `/api/auth/logout` | 로그아웃 (현재는 클라이언트 측에서 localStorage 삭제로 처리) |
| **GET** | `/api/users/{user_id}` | 특정 유저 정보 조회 |
| **GET** | `/api/users/` | 전체 유저 목록 (관리자용) |
| **GET** | `/api/users/{user_id}/statistics` | 유저 통계 |
| **POST** | `/api/health-records/` | 인바디 수동 입력 (OCR 없이 직접 저장) |
| **GET** | `/api/health-records/{record_id}` | 건강 기록 단건 조회 |
| **GET** | `/api/health-records/user/{user_id}/latest` | 최신 기록 1개 조회 |
| **GET** | `/api/health-records/{record_id}/analysis/prepare` | LLM1 입력 데이터 가공 (내부 유틸) |
| **GET** | `/api/analysis/{report_id}` | 분석 리포트 단건 조회 |
| **GET** | `/api/analysis/user/{user_id}` | 유저별 리포트 목록 |
| **POST/GET/PATCH/DELETE** | `/api/goals/*` | 목표 생성·조회·수정·삭제 전체 |
| **GET/PATCH/DELETE** | `/api/weekly-plans/{plan_id}` 등 | 주간 계획 단건 CRUD |
