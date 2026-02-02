# llm_test_sk 디렉토리 구조 설명

**목적:** LLM 서비스 테스트 및 개발 환경
**모델:** gpt-4o-mini (기본)
**프레임워크:** LangGraph (에이전트 기반)

---

## 📁 파일 구조

```
llm_test_sk/
├── __init__.py                  # 패키지 초기화
│
├── llm_clients.py              # LLM 클라이언트 (OpenAI)
├── llm_service.py              # LLM 서비스 (메인 서비스 로직)
│
├── agent_graph.py              # 건강 분석 LangGraph 에이전트
├── weekly_plan_graph.py        # 주간 계획 LangGraph 에이전트
│
├── prompt_generator.py         # 프롬프트 생성 함수
├── parse_utils.py              # 파싱 유틸리티
│
└── test_with_graph_rag.py     # Graph RAG 통합 테스트 (생성 예정)
```

---

## 🔧 주요 컴포넌트

### 1. llm_clients.py

**역할:** LLM API 호출 클라이언트

```python
class BaseLLMClient(ABC):
    """LLM 클라이언트 추상 클래스"""
    @abstractmethod
    def generate_chat(self, system_prompt: str, user_prompt: str) -> str

    @abstractmethod
    def generate_chat_with_history(self, system_prompt: str, messages: List[Tuple[str, str]]) -> str

    @abstractmethod
    def create_embedding(self, text: str) -> List[float]


class OpenAIClient(BaseLLMClient):
    """OpenAI API 클라이언트"""

    def __init__(self, model: str = "gpt-4o-mini"):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = model

    # 구현...
```

**기능:**
- ✅ 단일 턴 채팅 생성
- ✅ 대화 이력 포함 채팅
- ✅ 텍스트 임베딩 생성 (text-embedding-3-small)

**사용 예:**
```python
from llm_clients import create_llm_client

client = create_llm_client("gpt-4o-mini")
response = client.generate_chat(
    system_prompt="당신은 체성분 분석가입니다.",
    user_prompt="BMI 25는 비만인가요?"
)
```

---

### 2. llm_service.py

**역할:** LLM 서비스 메인 로직 (LangGraph 에이전트 통합)

```python
class LLMService:
    """LLM API 호출 서비스"""

    def __init__(self):
        self.model_version = "gpt-4o-mini"
        self.llm_client = create_llm_client(self.model_version)
        self.analysis_agent = create_analysis_agent(self.llm_client)
        self.weekly_plan_agent = create_weekly_plan_agent(self.llm_client)
```

**주요 메서드:**

#### LLM1: 건강 상태 분석
```python
async def call_status_analysis_llm(
    self,
    input_data: StatusAnalysisInput
) -> Dict[str, Any]:
    """
    건강 상태 분석 수행

    Returns:
        {
            "analysis_text": str,
            "embedding": {...},
            "thread_id": str
        }
    """
```

#### LLM1 Q&A
```python
async def chat_with_analysis(
    self,
    thread_id: str,
    user_message: str
) -> str:
    """휴먼 피드백 처리 (기존 스레드 이어서)"""
```

#### LLM2: 주간 계획 생성
```python
async def call_goal_plan_llm(
    self,
    input_data: GoalPlanInput
) -> str:
    """주간 계획서 생성"""
```

#### LLM2 Q&A
```python
async def chat_with_plan(
    self,
    thread_id: str,
    user_message: str
) -> str:
    """주간 계획 수정 및 질의응답"""
```

---

### 3. agent_graph.py

**역할:** LangGraph 기반 건강 분석 에이전트

**특징:**
- StateGraph 사용
- 메모리 체크포인팅 (대화 이력 저장)
- 휴먼 피드백 지원

**구조:**
```
[초기 분석] → [분석 완료]
     ↓             ↓
[휴먼 피드백] ← [대화 진행]
```

---

### 4. weekly_plan_graph.py

**역할:** LangGraph 기반 주간 계획 에이전트

**구조:**
```
[계획 생성] → [계획 완료]
     ↓             ↓
[휴먼 피드백] ← [수정/질의응답]
```

---

### 5. prompt_generator.py

**역할:** 인바디 분석 및 주간 계획 프롬프트 생성

#### 주요 함수

##### create_inbody_analysis_prompt()
```python
def create_inbody_analysis_prompt(
    measurements: InBodyMeasurements,
    body_type1: Optional[str] = None,
    body_type2: Optional[str] = None
) -> Tuple[str, str]:
    """
    인바디 분석용 프롬프트 생성

    Returns:
        (system_prompt, user_prompt)
    """
```

**System Prompt 구조:**
```
- 분석 목표: 객관적 현황 파악 (운동/식단 계획은 제외)
- 분석 항목:
  1. 기본 체형 분류 및 종합 평가
  2. 체성분 상세 분석 (체지방/근육량/영양)
  3. 부위별 불균형 분석
  4. 대사 및 건강 지표
  5. 규칙 기반 분석 결과 해석

- 출력 형식: 마크다운
- 어조: 전문적이면서 이해하기 쉽게
```

##### create_weekly_plan_prompt()
```python
def create_weekly_plan_prompt(
    measurements: InBodyMeasurements,
    user_goal_type: Optional[str],
    user_goal_description: Optional[str],
    status_analysis: Optional[str] = None
) -> Tuple[str, str]:
    """
    주간 계획용 프롬프트 생성

    Returns:
        (system_prompt, user_prompt)
    """
```

---

### 6. parse_utils.py

**역할:** LLM 출력 파싱 유틸리티

**주요 함수:**
```python
def parse_analysis_sections(text: str) -> Dict[str, str]:
    """분석 텍스트를 섹션별로 파싱"""

def extract_key_metrics(text: str) -> Dict[str, Any]:
    """주요 지표 추출"""
```

---

## 🔗 Graph RAG 통합 방법

### 기존 Graph RAG 파이프라인

**위치:** `/home/user/projects/ExplainMyBody/src/llm/pipeline_inbody_analysis_rag/`

```
pipeline_inbody_analysis_rag/
├── analyzer.py                 # InBodyAnalyzerGraphRAG 클래스
├── prompt_generator.py         # Graph RAG용 프롬프트 생성
├── main.py                     # 실행 파일
└── embedder.py                 # 임베딩 생성
```

### Graph RAG 작동 방식

```
1. 체형 분류 확인
   ↓
2. 개념 추출 (concept extraction)
   - BMI → "obesity", "body_composition"
   - 골격근량 → "muscle_mass", "sarcopenia"
   ↓
3. 하이브리드 검색 (Hybrid Search)
   - Vector Search: 임베딩 유사도 (70%)
   - Graph Search: Neo4j 그래프 탐색 (30%)
   ↓
4. 논문 컨텍스트 생성
   - 관련 논문 TOP 10
   - 제목, 출처, 연도, 초록
   ↓
5. LLM 프롬프트에 논문 포함
   - System: 전문 분석가 역할
   - User: InBody 데이터 + 논문 컨텍스트
   ↓
6. GPT-4o-mini로 분석 생성
```

---

## 🧪 테스트 파일 사용 방법

### test_with_graph_rag.py (생성 예정)

**목적:**
- Graph RAG 통합 테스트
- gpt-4o-mini 사용
- 단독 실행 가능

**실행 방법:**
```bash
cd /home/user/projects/ExplainMyBody/src/llm/llm_test_sk

# 기본 실행 (Graph RAG 포함)
python test_with_graph_rag.py

# Graph RAG 없이 실행
python test_with_graph_rag.py --no-rag

# 샘플 데이터 선택
python test_with_graph_rag.py --sample=gymnast
python test_with_graph_rag.py --sample=obese
python test_with_graph_rag.py --sample=skinnyfat
```

**예상 출력:**
```
=============================================================
InBody 분석 시작 (Graph RAG 통합 테스트)
=============================================================
  🔧 모델: gpt-4o-mini
  🔧 Graph RAG: ✅ Enabled

📊 1단계: 체형 정보 확인...
  - 1차 체형: 비만형
  - 2차 체형: 상체발달형

📚 2단계: Graph RAG 논문 검색...
  ✅ 검색된 논문: 10개
  - Vector Search: 7개
  - Graph Search: 3개

📝 3단계: LLM 분석 생성...
  ✅ 분석 완료 (응답 길이: 2,458자)

=============================================================
분석 결과:
=============================================================

[마크다운 분석 텍스트]

=============================================================
```

---

## 📊 데이터 흐름

### LLM1: 건강 상태 분석

```
InBody 측정 데이터
    ↓
[체형 분류]
    ↓
[Graph RAG 논문 검색] (선택)
    ↓
[프롬프트 생성]
    ↓
[LangGraph 에이전트]
    ↓
[GPT-4o-mini 호출]
    ↓
분석 결과 + 임베딩
```

### LLM2: 주간 계획 생성

```
사용자 목표 + InBody 데이터 + LLM1 분석 결과
    ↓
[Graph RAG 논문 검색] (선택)
    ↓
[프롬프트 생성]
    ↓
[LangGraph 에이전트]
    ↓
[GPT-4o-mini 호출]
    ↓
주간 계획서
```

---

## 🔑 환경 변수 설정

`.env` 파일 필요:
```env
# OpenAI
OPENAI_API_KEY=sk-...

# PostgreSQL (Graph RAG용)
DATABASE_URL=postgresql://sgkim:1234@localhost:5433/explainmybody

# Neo4j (Graph RAG용)
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=12341234
```

---

## 🚀 빠른 시작

### 1. 의존성 설치

```bash
pip install openai python-dotenv langgraph langchain langchain-openai
pip install psycopg2-binary neo4j  # Graph RAG용
```

### 2. 환경 변수 설정

```bash
cd /home/user/projects/ExplainMyBody
cp .env.example .env
# .env 파일 편집하여 API 키 입력
```

### 3. 테스트 실행

```bash
cd src/llm/llm_test_sk
python test_with_graph_rag.py
```

---

## 📚 참고 자료

### 관련 문서
- LangGraph: https://langchain-ai.github.io/langgraph/
- OpenAI API: https://platform.openai.com/docs

### 관련 파일
- Backend 스키마: `backend/schemas/inbody.py`
- Graph RAG 파이프라인: `src/llm/pipeline_inbody_analysis_rag/`
- 샘플 데이터: `src/llm/pipeline_inbody_analysis_rag/sample_inbody_*.json`

---

**작성일:** 2026-02-02
**작성자:** Claude Code
