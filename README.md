# ExplainMyBody

인바디 이미지에서 신체 정보를 추출해서 상태를 분석하고, AI 기반으로 주간 운동 및 식단 계획을 만들어주는 도구

> **알파 버전**: 현재 MVP 단계로 핵심 기능 구현 완료. 기능 업그레이드 준비 중.


## 주요 기능 (Alpha 기준)

### 🔹 핵심기능

- **InBody OCR 파이프라인**
  - 인바디 이미지 업로드
  - 39개 주요 신체 지표 자동 추출 (성별, 나이, 키, 체중, BMI, 골격근량, 체지방량 등)
  - OCR 결과 사용자 검증 후 인바디 기록 저장

- **AI 분석 & 주간 계획 챗봇**
  - 인바디 기록 기반 신체 상태 분석 및 요약 챗봇
  - 인바디 기록 + 사용자 목표/선호도/건강 특이사항을 기반으로 맞춤 운동·식단 주간 계획 생성 챗봇  
  - (현재 싱글턴 구조, 멀티 유저 세션 관리 개선 예정)

### 🔹 부가기능

- 회원가입 (이메일 중복 체크)
- 기본적인 사용자 정보 설정
  - 목표 설정 / 수정
  - 운동 선호도 초기 설정
  - 건강 특이사항 초기 설정
- 과거 인바디 기록 조회
- 새로운 인바디 기록 추가
- 운동 가이드 영상 제공
- 로그아웃

## 기술 스택

- **Backend**: Python 3.11+, FastAPI, PostgreSQL
- **Frontend**: React, Vite
- **AI/LLM**: LangGraph 기반 워크플로우 (초기 구조 구성단계)
- **패키지 관리**: uv (백엔드), npm (프론트엔드)

## 설치 및 실행

### 사전 요구사항

- Python 3.11 이상
- Node.js & npm
- PostgreSQL
- uv (`curl -LsSf https://astral.sh/uv/install.sh | sh`)

### 1. 데이터베이스 설정
```bash
# PostgreSQL 시작
sudo service postgresql start

# 데이터베이스 생성
createdb explainmybody
```

### 2. 백엔드 실행
```bash
cd backend

# 환경변수 설정 (API 키 등)
cp .env.example .env
# .env 파일 열어서 필요한 값 입력
- `DATABASE_URL`: PostgreSQL 접속 주소
- `OPENAI_API_KEY`: LangGraph/LLM 사용을 위한 키
# 의존성 설치
uv sync

# 서버 실행
uv run uvicorn main:app --reload
```

→ 백엔드: http://localhost:8000

**백엔드 실행 상세 가이드**: [backend/BACKEND_QUICKSTART.md](./backend/BACKEND_QUICKSTART.md)

### 3. 프론트엔드 실행
```bash
cd frontend

# 의존성 설치
npm install

# 개발 서버 실행
npm run dev
```

→ 프론트엔드: http://localhost:5173 (기본 Vite 포트)

## 프로젝트 구조
```
ExplainMyBody/
├── backend/          # FastAPI 서버 (routers, services, models)
├── frontend/         # React 앱 (pages, components, services)
├── src/              # 공통 로직 모듈 (체형 분석 코어)
├── requirements/     # Python 의존성 명세
└── docs/             # 개발 문서
```
**백엔드 상세 가이드**: [backend/README.md](./backend/README.md)

## 알려진 제약사항 (알파 버전)

- 인증/보안 로직 미완성
  - 로그인 시 비밀번호 검증 미구현
  - 회원가입 시 이메일 중복 체크만 동작
- 대화 세션 임시 저장 (메모리에만 저장, DB 연동 예정)
- 챗봇 싱글턴 구현 (멀티 유저 세션 관리 개선 예정)

---

**질문/피드백**: Issues 탭에서 자유롭게 남겨주세요.