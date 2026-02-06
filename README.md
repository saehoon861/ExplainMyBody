# LangGraph LLM1 수정 파일 및 세부 내용입니다


수정파일 목록 :
 backend/services/llm/agent_graph.py
 backend/models/analysis_report.py
 backend/repositories/llm/analysis_report_repository.py
 backend/database.py
 backend/services/llm/llm_service.py
 backend/schemas/llm.py
 backend/routers/llm/analysis.py



1. 파일: backend/services/llm/agent_graph.py
  
  적용된 수정사항 확인:
  - ✅ Lines 15-21: Custom reducer (keep_existing)
  - ✅ Lines 25-33: AnalysisState with custom reducers
  - ✅ Lines 56-61: AI 메시지 체크 (재실행 방지)
  - ✅ Lines 108-128: format_measurements() 함수
  - ✅ Lines 130-176: InBody 데이터 프롬프트 추가
  - ✅ Lines 241-291: route_qa human 메시지 읽기 수정
  - ✅ Line 340: interrupt_after에서 initial_analysis 제외
  - ✅ Lines 187, 199, 210, 223, 231: 모든 qa_nodes에 계획 제시 방지 경고



2. models/analysis_report.py (Line 22 추가)

  위치: /home/user/projects/ExplainMyBody/backend/models/analysis_report.py
  수정 내용:
  # Line 22 (새로 추가)


  thread_id = Column(String(255), nullable=True)  # LangGraph 대화 스레드 ID
  - analysis_type 다음에 추가
  - generated_at 앞에 위치

  ---



3. repositories/llm/analysis_report_repository.py (Line 24 추가)


  위치: /home/user/projects/ExplainMyBody/backend/repositories/llm/analysis_report_repo
  sitory.py
  수정 내용:
  # create() 메서드 내부 (Line 18-27)


  db_report = InbodyAnalysisReport(
      user_id=user_id,
      record_id=report_data.record_id,
      llm_output=report_data.llm_output,
      model_version=report_data.model_version,
      analysis_type=report_data.analysis_type,
      thread_id=report_data.thread_id,                  # ← 추가
      embedding_1536=report_data.embedding_1536,
      embedding_1024=report_data.embedding_1024
  )



  ---
4. database.py (Line 73-89 추가)


  위치: /home/user/projects/ExplainMyBody/backend/database.py
  수정 내용:

  # init_db() 함수 끝부분 (Line 73-89)
  # thread_id 컬럼 추가 (기존 DB에 컬럼이 없는 경우)


  try:
      from sqlalchemy import text
      with engine.connect() as conn:
          # 컬럼 존재 여부 확인
          result = conn.execute(text("""
              SELECT column_name
              FROM information_schema.columns
              WHERE table_name='inbody_analysis_reports' AND column_name='thread_id'
          """))
          if result.fetchone() is None:
              # thread_id 컬럼 추가
              conn.execute(text("ALTER TABLE inbody_analysis_reports ADD COLUMN
  thread_id VARCHAR(255)"))
              conn.commit()
              print("✅ thread_id 컬럼 추가 완료")
  except Exception as e:
      print(f"⚠️  thread_id 컬럼 추가 실패 (이미 존재하거나 오류): {e}")



5. 수정 파일 및 내용

 services/llm/llm_service.py (Line 135-148)

  수정 위치: call_status_analysis_llm 메서드

  변경 전:
  # 3. 결과 추출
  analysis_text = initial_state['messages'][-1].content
  embedding = initial_state.get("embedding")

  변경 후:
  # 3. 결과 추출
  # 🔧 수정: initial_analysis 결과만 추출 (qa_general로 넘어간 경우 방지)
  # - messages[0]: human (InBody 데이터)
  # - messages[1]: ai (initial_analysis 결과) ← 이것만 필요
  # - messages[2]: ai (qa_general 응답) ← 있으면 안 됨
  messages = initial_state['messages']
  if len(messages) >= 2:
      # 항상 두 번째 메시지(initial_analysis 결과)를 사용
      analysis_text = messages[1].content
  else:
      # 예외 상황: 메시지가 부족하면 마지막 메시지 사용
      analysis_text = messages[-1].content

  embedding = initial_state.get("embedding")



6. 수정 파일 및 내용

  schemas/llm.py (Line 243)

  변경 전:
  class AnalysisChatRequest(BaseModel):
      """분석/계획에 대한 대화 요청 (Human Feedback)"""
      report_id: int  # 필수
      message: str
      thread_id: Optional[str] = None

  변경 후:
  class AnalysisChatRequest(BaseModel):
      """분석/계획에 대한 대화 요청 (Human Feedback)"""
      report_id: Optional[int] = None  # URL path에 이미 있으므로 Optional
      message: str
      thread_id: Optional[str] = None


7. 수정 파일

  routers/llm/analysis.py (Line 122)

  변경 전:
  return {"response": response_text}

  변경 후:
  return {"reply": response_text, "thread_id": chat_request.thread_id}





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