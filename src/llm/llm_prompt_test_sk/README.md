# LLM Prompt 테스트 환경

backend의 LLM RAG 로직을 로컬에서 샘플 데이터로 테스트하는 독립 환경입니다.

## 📁 파일 구조

```
src/llm/llm_prompt_test_sk/
├── __init__.py
├── README.md                    # 이 파일
├── sample_data.py               # 샘플 InBody 데이터
├── schemas.py                   # LLM 입력 스키마
├── schemas_inbody.py            # InBody 데이터 스키마
├── llm_clients.py               # OpenAI 클라이언트
├── rag_retriever.py             # RAG 검색 (pgvector)
├── prompt_generator_rag.py      # 프롬프트 생성기
├── agent_graph_rag.py           # InBody 분석 에이전트
├── weekly_plan_graph_rag.py     # 주간 계획 에이전트
├── test_inbody_analysis.py      # InBody 분석 테스트
└── test_weekly_plan.py          # 주간 계획 테스트
```

## 🚀 사용 방법

### 1. 환경 설정

`.env` 파일에 다음 환경변수 설정:

```bash
OPENAI_API_KEY=your_openai_api_key
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
```

### 2. 테스트 실행

#### InBody 분석 테스트 (LLM1 + RAG)

```bash
cd /home/user/projects/ExplainMyBody/src/llm/llm_prompt_test_sk
python test_inbody_analysis.py
```

**출력 예시:**
- 샘플 InBody 데이터 출력
- RAG 논문 검색 수행
- LLM 건강 상태 분석 결과
- Embedding 생성 확인

#### 주간 계획 생성 테스트 (LLM2 + RAG)

```bash
cd /home/user/projects/ExplainMyBody/src/llm/llm_prompt_test_sk
python test_weekly_plan.py
```

**출력 예시:**
- 사용자 목표 및 선호 정보 출력
- RAG 논문 검색 수행
- 이전 분석 결과 포함
- LLM 주간 운동/식단 계획 생성

### 3. 샘플 데이터 수정

`sample_data.py`를 열어서 테스트용 데이터를 자유롭게 수정:

- `SAMPLE_MEASUREMENTS`: InBody 측정값
- `SAMPLE_USER`: 사용자 정보
- `SAMPLE_GOAL`: 목표 설정
- `SAMPLE_ANALYSIS_RESULT`: 이전 분석 결과 (LLM1 출력)

## 🧪 테스트 시나리오

### InBody 분석 (LLM1)

1. **입력**: 샘플 InBody 측정 데이터
2. **RAG**: 체성분 특징 기반 논문 검색
3. **프롬프트**: 건강 상태 분석 프롬프트 생성
4. **LLM 호출**: OpenAI GPT-4o-mini로 분석
5. **출력**: 건강 상태 분석 결과 + Embedding

### 주간 계획 (LLM2)

1. **입력**: 사용자 목표 + InBody 데이터 + 이전 분석 결과
2. **RAG**: 목표 타입 기반 논문 검색
3. **프롬프트**: 주간 계획 생성 프롬프트 (이전 분석 포함)
4. **LLM 호출**: OpenAI GPT-4o-mini로 계획 생성
5. **출력**: 주간 운동/식단 계획

## 📊 RAG 동작 방식

### InBody 분석 RAG

**검색 쿼리 생성 로직:**
- 성별, 연령
- BMI 상태 (저체중/과체중)
- 체지방률 (높음/정상)
- 근육 조절 필요량
- 내장지방 레벨

**예시 쿼리:** `"남성 28세 과체중 비만 관리 체지방 감소"`

### 주간 계획 RAG

**검색 쿼리 생성 로직:**
- 주요 목표 (체중 감량, 근육 증가 등)
- 선호 운동 종류
- 체성분 상태 기반 키워드

**예시 쿼리:** `"체중 감량 웨이트 트레이닝 유산소 체지방 감소"`

## 🔧 커스터마이징

### RAG 비활성화

```python
# test_inbody_analysis.py 또는 test_weekly_plan.py
analysis_agent = create_analysis_agent_with_rag(llm_client, use_rag=False)
```

### 모델 변경

```python
llm_client = create_llm_client("gpt-4")  # GPT-4 사용
```

### 검색 결과 개수 조정

`rag_retriever.py` 수정:
```python
papers = rag_retriever.retrieve_relevant_papers(
    query=query,
    top_k=10,  # 기본 5 → 10으로 증가
    lang="ko"
)
```

## ⚠️ 주의사항

1. **OpenAI API 키 필요**: `.env`에 `OPENAI_API_KEY` 설정 필수
2. **PostgreSQL 연결 필요**: RAG 검색을 위해 `DATABASE_URL` 설정 필수
3. **독립 환경**: 이 폴더는 backend 코드와 완전히 독립적으로 동작
4. **기존 코드 영향 없음**: 다른 코드 수정 없이 테스트 가능

## 🎯 활용 방법

- **프롬프트 최적화**: 프롬프트 수정 후 즉시 테스트
- **RAG 성능 테스트**: 논문 검색 품질 확인
- **샘플 데이터 검증**: 다양한 InBody 케이스 테스트
- **LLM 응답 비교**: 모델별 출력 품질 비교

## 📝 문제 해결

### RAG 검색 실패

```
❌ RAG 검색 실패: ...
```

→ `DATABASE_URL` 확인 및 PostgreSQL 연결 확인

### OpenAI API 에러

```
❌ OpenAI API error: ...
```

→ `OPENAI_API_KEY` 확인 및 API 크레딧 확인

### Import 에러

```
ModuleNotFoundError: No module named 'langgraph'
```

→ 필요한 패키지 설치:
```bash
pip install langgraph openai python-dotenv sqlalchemy psycopg2-binary pydantic
```

---

**개발자**: SK
**최종 수정**: 2026-02-03
