# 한국어 요약 및 임베딩 생성 가이드

## 개요

Graph RAG 구축 시 **영어 논문에 대해 로컬 Ollama로 한국어 요약을 생성하고, OpenAI로 임베딩을 생성**하는 기능입니다.

**핵심 변경사항:**
- 한국어 요약: ~~OpenAI GPT-4o-mini~~ → **로컬 Ollama (llama3.2, gemma2 등)**
- 한국어 임베딩: ~~로컬 Ollama~~ → **OpenAI text-embedding-3-small (1536D)**

### 왜 필요한가?

1. **개념 추출 향상**: 영어 논문도 한국어 키워드로 검색 가능
2. **일관된 검색**: 모든 논문을 한국어로 검색
3. **비용 효율**: 한국어 논문은 이미 한국어 → 영어 논문만 처리 (50% 비용 절감)

## 비용 분석

### 예상 논문 수
- 전체: 2000-5000개
- 영어 논문: ~50-60% (1000-2500개)
- 한국어 논문: ~40-50% (800-2500개)

### 한국어 요약 생성 (로컬 Ollama)
```
비용: $0 (로컬 실행)

처리 시간:
- CPU: 논문당 5-10초 → 1000개 = 1.4-2.8시간
- GPU: 논문당 1-2초 → 1000개 = 17-33분

추천 모델:
- llama3.2 (3B): 빠름, 품질 양호
- gemma2 (9B): 느림, 품질 우수
- qwen2.5 (7B): 중간, 한국어 특화
```

### 한국어 임베딩 생성 (OpenAI)
```
text-embedding-3-small: $0.02/1M tokens

논문당 평균:
- 한국어 요약: 150 tokens

영어 논문만 처리:
- 1000개: 150K tokens = $0.003
- 2500개: 375K tokens = $0.0075

예상 비용: $0.003 - $0.008 (거의 무료 수준)
```

### 총 비용 및 시간
- **총 비용**: $0.003 - $0.008 (임베딩만, 요약은 무료)
- **처리 시간**:
  - CPU: 1.5-3시간
  - GPU: 20-40분

## 사용 방법

### 1. 사전 준비

#### Ollama 설치 및 실행 (한국어 요약 생성용)

```bash
# Ollama 설치 (https://ollama.ai)
curl -fsSL https://ollama.ai/install.sh | sh

# Ollama 서버 실행
ollama serve

# 한국어 요약 생성 모델 다운로드
ollama pull llama3.2      # 추천 (빠름, 3B)
ollama pull gemma2        # 고품질 (느림, 9B)
ollama pull qwen2.5       # 한국어 특화 (7B)
```

#### OpenAI API 키 설정 (한국어 임베딩 생성용)

```bash
# 환경변수로 설정
export OPENAI_API_KEY="sk-..."

# 또는 .env 파일에 추가
echo "OPENAI_API_KEY=sk-..." >> .env
```

### 2. Graph RAG 구축 실행

```bash
# 기본 (요약/임베딩 없음)
python build_graph_rag.py

# 한국어 요약만 생성 (로컬 Ollama)
python build_graph_rag.py --ko-summary

# 한국어 임베딩만 생성 (요약 필요, OpenAI)
python build_graph_rag.py --ko-summary --ko-embedding

# 다른 Ollama 모델 사용
python build_graph_rag.py --ko-summary --ollama-model=gemma2
```

### 3. 출력 확인

```json
{
  "id": "pubmed_12345678",
  "chunk_text": "Resistance training combined with adequate protein intake...",
  "lang": "en",
  "chunk_ko_summary": "저항성 운동과 적절한 단백질 섭취를 결합하면 골격근량이 유의미하게 증가합니다. 12주간 1.6g/kg/일 섭취 시 대조군 대비 2.3kg 증가를 확인했습니다.",
  "embedding_ko_openai": [0.123, 0.456, 0.789, ...],
  "domain": "protein_hypertrophy",
  "source": "pubmed"
}
```

**임베딩 차원:**
- `embedding_openai`: 1536D (원본 영어 텍스트, OpenAI)
- `embedding_ollama`: 1024D (원본 텍스트, 로컬)
- `embedding_ko_openai`: 1536D (한국어 요약 전용, OpenAI)

## 저장 구조

### 영어 논문 (한국어 요약 + 임베딩)
```json
{
  "chunk_text": "원본 영어 초록",
  "lang": "en",
  "chunk_ko_summary": "로컬 Ollama 생성 한국어 요약",
  "embedding_openai": [1536D],
  "embedding_ollama": [1024D],
  "embedding_ko_openai": [1536D]
}
```

### 한국어 논문 (요약 불필요)
```json
{
  "chunk_text": "원본 한국어 초록",
  "lang": "ko",
  "chunk_ko_summary": null,
  "embedding_openai": [1536D],
  "embedding_ollama": [1024D],
  "embedding_ko_openai": null
}
```

## Ollama 요약 모델 추천

### 1. llama3.2 (추천, 기본값)
```bash
ollama pull llama3.2
```
- 크기: 3B
- 장점: 빠름, 품질 양호, 한국어 지원
- 속도: 매우 빠름 (GPU: 1-2초/논문)
- 용량: ~2GB
- 추천: **일반적인 사용**

### 2. gemma2
```bash
ollama pull gemma2
```
- 크기: 9B
- 장점: 고품질, 학술 논문 요약에 강함
- 속도: 중간 (GPU: 3-5초/논문)
- 용량: ~5GB
- 추천: **품질 중시**

### 3. qwen2.5
```bash
ollama pull qwen2.5
```
- 크기: 7B
- 장점: 한국어 특화, 중국어/한국어 성능 우수
- 속도: 중간 (GPU: 2-3초/논문)
- 용량: ~4GB
- 추천: **한국어 특화**

### 모델 선택 가이드
| 우선순위 | 모델 | 속도 | 품질 | 용량 | 용도 |
|---------|------|------|------|------|------|
| **1순위** | llama3.2 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 2GB | 일반 사용 |
| 2순위 | qwen2.5 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 4GB | 한국어 특화 |
| 3순위 | gemma2 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 5GB | 품질 중시 |

## 프롬프트 전략

현재 사용 중인 프롬프트:
```
당신은 의학/운동과학 논문 요약 전문가입니다.
영어 논문 초록을 읽고 핵심 내용을 2-3문장의 한국어로 요약하세요.
다음 정보를 반드시 포함하세요:
1. 주요 연구 목적
2. 핵심 결과 (숫자/수치 포함)
3. 임상적 의의

체성분, 근육, 영양, 운동 관련 키워드를 정확히 번역하세요.
```

### 프롬프트 최적화 팁

1. **도메인별 프롬프트**: 논문 도메인에 따라 프롬프트 조정
2. **키워드 강조**: 개념 키워드를 요약에 반드시 포함하도록 지시
3. **길이 제한**: 150 tokens 정도로 제한 (비용 절감)

## 개념 추출 & 검색 향상

### 1. 개념 추출 향상

한국어 요약 생성 시 **개념 추출이 2배 향상**됩니다:

```python
# 요약 없이 (영어만 검색)
extract_mentioned_concepts(english_abstract)
→ 영어 개념만 매칭 (muscle hypertrophy, protein intake...)

# 요약 포함 (영어 + 한국어 검색)
extract_mentioned_concepts(english_abstract, ko_summary)
→ 영어 + 한국어 개념 매칭 (근비대, 단백질 섭취...)
```

### 2. 한국어 임베딩의 장점

**OpenAI text-embedding-3-small 사용 시:**

1. **고품질**: 최신 임베딩 모델, 다국어 성능 우수
2. **높은 차원**: 1536D (로컬 Ollama 1024D보다 풍부한 표현)
3. **일관성**: 원본 영어 임베딩과 동일한 모델 사용
4. **한국어 특화 검색**: 한국어 쿼리로 영어 논문도 검색 가능
5. **비용 효율**: 논문 2500개 임베딩 = $0.008 (매우 저렴)

**사용 시나리오:**
```python
# 사용자 쿼리: "근비대에 효과적인 단백질 섭취량"
query_embedding = openai.embeddings.create(
    model="text-embedding-3-small",
    input="근비대에 효과적인 단백질 섭취량"
)

# 검색: embedding_ko_openai와 유사도 계산
# → 영어 논문도 한국어 요약으로 매칭 가능!
# → 원본 영어 임베딩(embedding_openai)과 동일한 벡터 공간
```

## 장점 vs 단점

### 한국어 요약 생성 (--ko-summary, 로컬 Ollama)

#### 장점
1. **비용 0원**: 로컬 실행, API 비용 없음
2. **개념 추출 향상**: 한국어 키워드 매칭 가능
3. **일관된 검색**: 모든 논문을 한국어로 검색
4. **원본 보존**: chunk_text에 원본 유지 → 정확도 보장
5. **프라이버시**: 데이터 외부 전송 없음
6. **무제한**: 요약 생성 횟수 제한 없음

#### 단점
1. **초기 처리 시간**:
   - CPU: 1000개 = 1.5-3시간
   - GPU: 1000개 = 17-33분
2. **로컬 설치**: Ollama 서버 설치 및 실행 필요
3. **GPU 권장**: CPU만 사용 시 매우 느림
4. **품질 변동**: 모델에 따라 요약 품질 차이 발생

### 한국어 임베딩 생성 (--ko-embedding, OpenAI)

#### 장점
1. **고품질**: 최신 OpenAI 임베딩 모델 (1536D)
2. **일관성**: 원본 영어 임베딩과 동일 모델/차원
3. **빠른 속도**: API 병렬 처리 가능
4. **한국어 특화**: 한국어 쿼리로 영어 논문 검색 가능
5. **비용 효율**: 2500개 = $0.008 (거의 무료)

#### 단점
1. **요약 필요**: --ko-summary와 함께 사용해야 함
2. **API 키 필요**: OpenAI API 키 필요
3. **저장 용량 증가**: 1536D 벡터 추가 저장 (논문당 ~6KB)
4. **외부 의존성**: OpenAI API 서버 의존

## 대안: 요약 없이 사용

한국어 요약 없이도 Graph RAG는 정상 작동합니다:

```bash
# 기본 실행 (요약 없음)
python build_graph_rag.py
```

**이 경우:**
- 영어 논문: 영어 개념만 추출
- 한국어 논문: 한국어 개념만 추출
- 비용 0원
- 처리 시간 빠름 (5-10분)

**추천:**
1. 먼저 요약 없이 구축해서 결과 확인
2. 개념 추출이 부족하면 --ko-summary 활성화

## 코드 수정 방법

### 1. 프롬프트 커스터마이징

`build_graph_rag.py:130-145` 수정:

```python
def generate_korean_summary(self, english_abstract: str) -> Optional[str]:
    response = self.openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "여기에 커스텀 프롬프트 작성"
            },
            {
                "role": "user",
                "content": f"논문 초록:\n{english_abstract}\n\n한국어 요약:"
            }
        ],
        temperature=0.3,  # 낮을수록 일관성 높음
        max_tokens=300    # 늘리면 긴 요약 생성
    )
```

### 2. 모델 변경

```python
model="gpt-4o-mini"  # 기본 (저렴, 빠름)
model="gpt-4o"       # 품질 향상 (3배 비용)
```

### 3. Rate Limit 조정

```python
time.sleep(0.5)  # 기본 (2 req/sec)
time.sleep(1.0)  # 안전 (1 req/sec)
time.sleep(0.2)  # 빠름 (5 req/sec, 위험)
```

## 문제 해결

### OpenAI API 키 오류
```bash
⚠️ OpenAI API 키 없음. 한국어 요약 생성 비활성화
```
→ `export OPENAI_API_KEY="sk-..."` 실행

### Rate Limit 초과
```
Rate limit reached for gpt-4o-mini
```
→ `time.sleep(1.0)`으로 증가

### 요약 품질 낮음
- 프롬프트 수정
- `temperature=0.1`로 낮춤 (더 일관적)
- 모델을 `gpt-4o`로 변경

## 통계 확인

```bash
python build_graph_rag.py --ko-summary --ko-embedding
```

출력:
```
✅ OpenAI 클라이언트 초기화 완료
✅ Ollama 클라이언트 초기화 완료 (모델: bge-m3)
✅ 스키마 로드 완료: 50개 개념

🔨 그래프 구축 시작...
   📝 영어 논문에 대해 한국어 요약 생성 활성화
   🧮 한국어 임베딩 생성 활성화 (모델: bge-m3)
  처리: 100/2345개 (한국어 요약: 52개)
  ...

✅ 그래프 구축 완료!
   - 논문 노드: 2345개
     • 영어: 1200개
     • 한국어: 1145개
     • 한국어 요약 생성: 1200개
     • 한국어 임베딩 생성: 1200개
   - 개념 발견: 48개
   - MENTIONS 관계: 5678개
```

## 결론

**추천 워크플로:**

### 옵션 1: 기본 (빠르게 테스트)
```bash
python build_graph_rag.py
```
- 비용: $0
- 시간: 5-10분
- 용도: 빠른 프로토타입, 테스트

### 옵션 2: 한국어 요약만 (로컬 Ollama)
```bash
# Ollama 서버 실행 (별도 터미널)
ollama serve

# Graph RAG 구축
python build_graph_rag.py --ko-summary
```
- 비용: $0 (로컬 실행)
- 시간:
  - CPU: 1.5-3시간
  - GPU: 20-40분
- 용도: 개념 추출 향상, 한국어 검색 활성화

### 옵션 3: 요약 + 임베딩 (최적, 추천)
```bash
# Ollama 서버 실행 (별도 터미널)
ollama serve

# OpenAI API 키 설정
export OPENAI_API_KEY="sk-..."

# Graph RAG 구축
python build_graph_rag.py --ko-summary --ko-embedding
```
- 비용: $0.003-0.008 (임베딩만, 요약은 무료)
- 시간:
  - CPU: 1.5-3시간
  - GPU: 20-40분
- 용도: **프로덕션 환경, 한국어 특화 검색**
- 장점:
  - 한국어 쿼리로 영어 논문 검색 가능
  - 로컬 요약 → 비용 0원, 무제한
  - OpenAI 임베딩 → 고품질, 거의 무료
  - 개념 추출 2배 향상
  - 일관된 검색 경험

### 비교표

| 옵션 | 요약 | 임베딩 | 비용 | 시간 (GPU) | 검색 성능 |
|------|------|--------|------|-----------|-----------|
| 기본 | ❌ | ❌ | $0 | 5분 | ⭐⭐ |
| 요약만 | ✅ (로컬) | ❌ | $0 | 30분 | ⭐⭐⭐⭐ |
| **요약+임베딩** | ✅ (로컬) | ✅ (OpenAI) | $0.008 | 30분 | ⭐⭐⭐⭐⭐ |

**최종 추천**: 옵션 3 (요약 + 임베딩)
- 한국어 사용자를 위한 최적의 검색 경험
- 비용 거의 무료 ($0.008)
- 요약은 로컬 무료, 임베딩만 OpenAI
- 프로덕션 환경에 적합
