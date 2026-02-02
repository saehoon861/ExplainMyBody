# Graph RAG 통합 테스트 빠른 시작 가이드

**작성일:** 2026-02-02
**목적:** llm_test_sk에서 Graph RAG 통합 테스트 실행

---

## 🚀 빠른 시작 (3분)

### 1. 환경 변수 확인

```bash
cd /home/user/projects/ExplainMyBody

# .env 파일 확인
cat .env | grep -E "OPENAI_API_KEY|DATABASE_URL|NEO4J"
```

**필요한 환경 변수:**
```env
OPENAI_API_KEY=sk-...
DATABASE_URL=postgresql://sgkim:1234@localhost:5433/explainmybody
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=12341234
```

### 2. PostgreSQL & Neo4j 실행 확인

```bash
# PostgreSQL
psql -h localhost -p 5433 -U sgkim -d explainmybody -c "SELECT COUNT(*) FROM paper_nodes;"

# Neo4j
curl http://localhost:7474
```

### 3. 테스트 실행

```bash
cd /home/user/projects/ExplainMyBody/src/llm/llm_test_sk

# 기본 실행 (Graph RAG 포함)
python test_with_graph_rag.py
```

---

## 📋 실행 옵션

### 기본 실행

```bash
# default 샘플 데이터로 Graph RAG 전체 분석
python test_with_graph_rag.py
```

**예상 출력:**
```
=======================================================================
🧪 Graph RAG 통합 테스트 초기화
=======================================================================
  🔧 모델: gpt-4o-mini
  🔧 Graph RAG: ✅ Enabled
  🔧 Neo4j: ✅ Enabled

  ✅ Graph RAG Analyzer 초기화 완료
=======================================================================

📂 샘플 데이터 로드: sample_inbody_data.json
  ✅ InBodyData 객체 생성 완료

=======================================================================
📝 Graph RAG 전체 분석 테스트
=======================================================================

📊 1단계: 체형 정보 확인...
  - 1차 체형: 비만형
  - 2차 체형: 상체발달형

📚 2단계: Graph RAG 논문 검색...
  ✅ 검색된 논문: 10개

📝 3단계: LLM 분석 생성...
  ✅ 분석 완료

=======================================================================
✅ 분석 완료
=======================================================================

📊 분석 결과:
----------------------------------------------------------------------
[마크다운 분석 텍스트]

💾 결과 저장: test_result.json

=======================================================================
✅ 테스트 완료
=======================================================================
```

---

### 샘플 데이터 선택

```bash
# 운동선수형 (Gymnast) - 근육 많고 체지방 적음
python test_with_graph_rag.py --sample=gymnast

# 비만형 (Obese) - 체지방 과다
python test_with_graph_rag.py --sample=obese

# 마른 비만 (Skinny Fat) - 정상 체중이지만 근육 부족
python test_with_graph_rag.py --sample=skinnyfat

# 근육형 (Juggernaut) - 근육과 체지방 모두 많음
python test_with_graph_rag.py --sample=juggernaut
```

---

### Graph RAG 없이 실행

```bash
# 기본 프롬프트만 사용 (논문 검색 없음)
python test_with_graph_rag.py --no-rag
```

**사용 케이스:**
- Graph RAG DB가 없을 때
- 빠른 LLM 응답만 필요할 때
- 기본 프롬프트 품질 확인

---

### 논문 검색만 테스트

```bash
# 논문 검색 결과만 확인 (LLM 호출 없음)
python test_with_graph_rag.py --test-retrieval
```

**예상 출력:**
```
=======================================================================
📚 Graph RAG 논문 검색 테스트
=======================================================================

🔍 1단계: 개념 추출...
  ✅ 추출된 개념: body_composition, fat_loss, muscle_mass, obesity

🔍 2단계: 검색 쿼리 생성...
  ✅ 쿼리: 이 사용자는 비만형 체형으로, 체지방률이 높고...

🔍 3단계: 논문 검색 (Top 10)...
  ✅ 검색된 논문: 10개

📄 검색 결과 (Top 5):

1. Effects of resistance training on body composition in obesity
   출처: PubMed (2023)
   점수: Vector=0.856, Graph=0.724, Final=0.816
   초록: This study examined the effects of resistance training...

2. Sarcopenic obesity and metabolic syndrome
   출처: PubMed (2022)
   점수: Vector=0.842, Graph=0.698, Final=0.799
   초록: Sarcopenic obesity is characterized by...

[...]
```

---

### Neo4j 없이 실행 (Vector Search만)

```bash
# PostgreSQL만 사용 (Neo4j 그래프 탐색 제외)
python test_with_graph_rag.py --no-neo4j
```

**사용 케이스:**
- Neo4j가 실행되지 않을 때
- Vector Search만으로 충분할 때

---

### 결과 저장 파일명 지정

```bash
# 결과를 특정 파일명으로 저장
python test_with_graph_rag.py --output=result_gymnast.json
```

---

### 다른 모델 사용

```bash
# GPT-4o 사용 (더 정확하지만 비용 높음)
python test_with_graph_rag.py --model=gpt-4o

# GPT-3.5-turbo 사용 (빠르고 저렴)
python test_with_graph_rag.py --model=gpt-3.5-turbo
```

---

## 📊 테스트 시나리오

### 시나리오 1: 기본 전체 테스트

```bash
# 모든 샘플 데이터로 순차 테스트
python test_with_graph_rag.py --sample=gymnast --output=result_gymnast.json
python test_with_graph_rag.py --sample=obese --output=result_obese.json
python test_with_graph_rag.py --sample=skinnyfat --output=result_skinnyfat.json
python test_with_graph_rag.py --sample=juggernaut --output=result_juggernaut.json
```

### 시나리오 2: Graph RAG 효과 비교

```bash
# Graph RAG 있음
python test_with_graph_rag.py --sample=obese --output=result_with_rag.json

# Graph RAG 없음
python test_with_graph_rag.py --sample=obese --no-rag --output=result_no_rag.json

# 결과 비교
diff result_with_rag.json result_no_rag.json
```

### 시나리오 3: 논문 검색 품질 확인

```bash
# 각 체형별로 검색되는 논문 확인
python test_with_graph_rag.py --sample=gymnast --test-retrieval
python test_with_graph_rag.py --sample=obese --test-retrieval
python test_with_graph_rag.py --sample=skinnyfat --test-retrieval
```

---

## 🔧 문제 해결

### 오류: OPENAI_API_KEY 없음

```
❌ Error: The api_key client option must be set...
```

**해결:**
```bash
export OPENAI_API_KEY=sk-...
# 또는 .env 파일에 추가
```

---

### 오류: PostgreSQL 연결 실패

```
❌ could not connect to server...
```

**해결:**
```bash
# PostgreSQL 실행 확인
sudo systemctl start postgresql
# 또는
docker-compose up -d postgres
```

---

### 오류: Neo4j 연결 실패

```
⚠️ Neo4j 연결 실패: Failed to establish connection...
```

**해결:**
```bash
# Neo4j 실행 확인
docker-compose up -d neo4j

# 또는 Neo4j 없이 실행
python test_with_graph_rag.py --no-neo4j
```

---

### 오류: paper_nodes 테이블 없음

```
❌ relation "paper_nodes" does not exist
```

**해결:**
```bash
# Graph RAG DB 임포트 필요
cd /home/user/projects/ExplainMyBody/src/llm/ragdb_collect
python import_to_databases.py

# 또는 Graph RAG 없이 실행
cd /home/user/projects/ExplainMyBody/src/llm/llm_test_sk
python test_with_graph_rag.py --no-rag
```

---

### 오류: 샘플 파일 없음

```
❌ 샘플 파일 없음: .../sample_inbody_gymnast.json
```

**해결:**
```bash
# 샘플 파일 경로 확인
ls /home/user/projects/ExplainMyBody/src/llm/pipeline_inbody_analysis_rag/sample_*.json

# default 샘플 사용
python test_with_graph_rag.py --sample=default
```

---

## 📝 결과 파일 구조

**test_result.json:**
```json
{
  "analysis_text": "# 체성분 분석 결과\n\n## 1. 기본 체형 분류...",
  "record_id": 1,
  "analysis_id": 1,
  "model_version": "gpt-4o-mini",
  "graph_rag_used": true,
  "papers_retrieved": 10
}
```

---

## 🎯 다음 단계

### 1. LangGraph 에이전트 통합

```python
# llm_service.py의 LLMService 사용
from llm_service import LLMService

service = LLMService()

# Graph RAG는 백그라운드에서 자동 작동
result = await service.call_status_analysis_llm(input_data)
```

### 2. 휴먼 피드백 테스트

```python
# 분석 후 Q&A
thread_id = result["thread_id"]

# 사용자 질문
response = await service.chat_with_analysis(
    thread_id=thread_id,
    user_message="체지방을 줄이려면 어떻게 해야 하나요?"
)
```

### 3. 주간 계획 생성 테스트

```bash
# weekly_plan 테스트 파일 만들기 (TODO)
python test_weekly_plan_with_rag.py
```

---

## 📚 관련 문서

- **구조 설명:** README_STRUCTURE.md
- **Graph RAG 파이프라인:** ../pipeline_inbody_analysis_rag/README.md
- **LangGraph 공식 문서:** https://langchain-ai.github.io/langgraph/

---

**작성일:** 2026-02-02
**작성자:** Claude Code
