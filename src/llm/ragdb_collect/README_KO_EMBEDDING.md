# 한국어 요약 및 임베딩 Graph RAG 구축 가이드

## 빠른 시작

### 1. 사전 준비

```bash
# 의존성 설치
pip install -r requirements.txt

# Ollama 설치 (한국어 요약 생성용)
curl -fsSL https://ollama.ai/install.sh | sh

# Ollama 서버 실행 (별도 터미널)
ollama serve

# 한국어 요약 생성 모델 다운로드
ollama pull llama3.2    # 추천 (빠름, 3B)
ollama pull gemma2      # 고품질 (9B)

# OpenAI API 키 설정 (한국어 임베딩 생성용)
export OPENAI_API_KEY="sk-..."
```

### 2. 연결 테스트

```bash
# Ollama 연결 테스트
python test_ko_embedding.py llama3.2
```

### 3. Graph RAG 구축

```bash
# 전체 파이프라인 실행 (로컬 요약 + OpenAI 임베딩)
python build_graph_rag.py --ko-summary --ko-embedding

# 다른 Ollama 모델 사용
python build_graph_rag.py --ko-summary --ko-embedding --ollama-model=gemma2
```

## 상세 워크플로

### 단계별 실행

```bash
# 1단계: 기본 구축 (테스트용)
python build_graph_rag.py

# 2단계: 한국어 요약 생성
python build_graph_rag.py --ko-summary

# 3단계: 한국어 임베딩 추가 (최종)
python build_graph_rag.py --ko-summary --ko-embedding
```

### 출력 파일

```
outputs/
├── graph_rag_20260129.json           # 그래프 데이터 (노드 + 엣지)
├── graph_rag_neo4j_20260129.cypher   # Neo4j 임포트 스크립트
└── graph_rag_stats_20260129.json     # 통계 정보
```

## 임베딩 구조

### 영어 논문

```json
{
  "id": "pubmed_12345678",
  "chunk_text": "Resistance training increases skeletal muscle...",
  "lang": "en",
  "chunk_ko_summary": "저항성 운동은 골격근량을 증가시키며... (로컬 Ollama 생성)",
  "embedding_openai": [1536D 벡터],
  "embedding_ollama": [1024D 벡터],
  "embedding_ko_openai": [1536D 벡터]
}
```

**임베딩 사용처:**
- `embedding_openai` (1536D): 원본 영어 텍스트 → OpenAI 검색
- `embedding_ollama` (1024D): 원본 텍스트 → 로컬 검색
- `embedding_ko_openai` (1536D): 한국어 요약 → **한국어 쿼리 검색 (OpenAI)**

### 한국어 논문

```json
{
  "id": "kci_98765432",
  "chunk_text": "저항성 운동과 단백질 섭취가...",
  "lang": "ko",
  "chunk_ko_summary": null,
  "embedding_openai": [1536D 벡터],
  "embedding_ollama": [1024D 벡터],
  "embedding_ko_openai": null
}
```

## 검색 시나리오

### 시나리오 1: 한국어 쿼리 → 전체 논문 검색

```python
# 사용자 쿼리
query = "근비대에 효과적인 단백질 섭취량은?"

# OpenAI로 한국어 쿼리 임베딩 생성
query_emb = openai.embeddings.create(
    model="text-embedding-3-small",
    input=query
)

# 영어 논문: embedding_ko_openai와 유사도 계산
# 한국어 논문: embedding_openai와 유사도 계산

# → 모든 논문을 한국어로 검색 가능!
# → 동일한 OpenAI 벡터 공간에서 일관성 보장
```

### 시나리오 2: 영어 쿼리 → 영어 논문 검색

```python
query = "What is the optimal protein intake for muscle hypertrophy?"
query_emb = openai.embeddings.create(
    model="text-embedding-3-small",
    input=query
)

# embedding_openai와 유사도 계산
```

### 시나리오 3: 하이브리드 검색

```python
# 한국어 + 영어 쿼리 동시 검색
korean_results = search_with_ollama(ko_query)
english_results = search_with_openai(en_query)

# 결과 병합 및 리랭킹
```

## Ollama 요약 모델 선택

### 추천 모델 (요약 생성용)

| 모델 | 크기 | 속도 (GPU) | 한국어 성능 | 용도 |
|------|------|-----------|-------------|------|
| **llama3.2** | 3B | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | **추천 (일반)** |
| qwen2.5 | 7B | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 한국어 특화 |
| gemma2 | 9B | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 고품질 |

### 모델 설치

```bash
# 추천 (빠름, 일반 사용)
ollama pull llama3.2

# 한국어 특화
ollama pull qwen2.5

# 고품질
ollama pull gemma2
```

## 비용 및 성능

### 비용

| 구성 | Ollama (요약) | OpenAI (임베딩) | 총 비용 |
|------|--------------|-----------------|---------|
| 요약만 | $0 | $0 | $0 |
| 요약 + 임베딩 | $0 | $0.003-0.008 | $0.003-0.008 |

**로컬 Ollama 요약은 무료!**
**OpenAI 임베딩은 거의 무료!** (2500개 = $0.008)

### 처리 시간

- 한국어 요약 생성 (로컬 Ollama):
  - CPU: 논문당 5-10초 (1000개 = 1.5-3시간)
  - GPU: 논문당 1-2초 (1000개 = 17-33분)
- OpenAI 임베딩:
  - API 병렬 처리: 초당 50-100개 (1000개 = 10-20분)

### 저장 용량

- 논문당 추가 용량:
  - `chunk_ko_summary`: ~300 bytes
  - `embedding_ko_openai`: ~6KB (1536D × 4 bytes)
- 2000개 논문: ~12.6MB 추가

## 문제 해결

### Ollama 서버 연결 실패

```bash
# 오류
❌ Ollama 서버 연결 실패

# 해결
ollama serve  # 별도 터미널에서 실행
```

### 모델 미설치

```bash
# 오류
⚠️ 모델 'bge-m3' 미설치

# 해결
ollama pull bge-m3
ollama list  # 설치된 모델 확인
```

### OpenAI API 키 오류

```bash
# 오류
⚠️ OpenAI API 키 없음

# 해결
export OPENAI_API_KEY="sk-..."
```

### 임베딩 생성 느림 (CPU)

```bash
# CPU만 사용 시 매우 느림
# → GPU 사용 권장

# Ollama GPU 설정 확인
ollama ps
```

## 고급 사용법

### 커스텀 프롬프트

`build_graph_rag.py:130-145` 수정:

```python
def generate_korean_summary(self, english_abstract: str):
    response = self.openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{
            "role": "system",
            "content": "여기에 커스텀 프롬프트 작성"
        }],
        temperature=0.3,  # 낮을수록 일관성 높음
        max_tokens=300
    )
```

### 다른 Ollama 모델 사용

```bash
# multilingual-e5-large 사용
python build_graph_rag.py --ko-summary --ko-embedding --ollama-model=multilingual-e5-large

# 직접 지정
python build_graph_rag.py --ko-summary --ko-embedding --ollama-model=nomic-embed-text
```

### 배치 처리

```python
# build_graph_rag.py 수정
# 여러 논문을 한 번에 임베딩 생성 (속도 향상)

def generate_batch_embeddings(self, texts: List[str]):
    embeddings = []
    for text in texts:
        emb = ollama.embeddings(model=self.ollama_model, prompt=text)
        embeddings.append(emb['embedding'])
    return embeddings
```

## 검증

### 임베딩 품질 테스트

```python
# 유사한 논문이 가까운 거리에 있는지 확인
from sklearn.metrics.pairwise import cosine_similarity

# 예: "근비대" 관련 논문들의 임베딩
paper1_emb = [...]
paper2_emb = [...]

similarity = cosine_similarity([paper1_emb], [paper2_emb])[0][0]
print(f"유사도: {similarity:.4f}")  # 높을수록 유사
```

### 검색 정확도 테스트

```bash
# 테스트 쿼리로 검색 결과 확인
python test_search_quality.py
```

## 참고 자료

- [Ollama 공식 문서](https://ollama.ai/docs)
- [BGE-M3 모델 정보](https://huggingface.co/BAAI/bge-m3)
- [OpenAI Embeddings 가이드](https://platform.openai.com/docs/guides/embeddings)
- [KOREAN_SUMMARY_GUIDE.md](./KOREAN_SUMMARY_GUIDE.md) - 상세 가이드
