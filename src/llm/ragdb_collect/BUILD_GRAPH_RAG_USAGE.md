# Graph RAG 구축 실행 가이드

`build_graph_rag.py` 실행 방법과 옵션을 안내합니다.

---

## 📋 실행 명령어

### 1️⃣ 기본 실행 (빠름, 1~3분) ⚡

```bash
python build_graph_rag.py
```

**수행 작업:**
- ✅ 개념 추출만 수행
- ❌ 한국어 요약 생성 없음
- ❌ 임베딩 생성 없음

**소요 시간:** 약 1~3분 (5000개 논문 기준)

---

### 2️⃣ 한국어 요약 추가 (느림, 40분~3시간) 🌙

```bash
python build_graph_rag.py --ko-summary
```

**수행 작업:**
- ✅ 영어 논문 → 한국어 요약 생성 (Ollama 사용)
- ✅ 개념 추출
- ❌ 임베딩 생성 없음

**요구사항:**
- Ollama 서버가 실행 중이어야 함

```bash
# 별도 터미널에서 Ollama 서버 실행
ollama serve
```

**소요 시간:** 약 40분~3시간 (영어 논문 수와 모델에 따라)

---

### 3️⃣ 한국어 임베딩 추가 (중간, 10~15분) 📊

```bash
python build_graph_rag.py --ko-embedding
```

**수행 작업:**
- ✅ OpenAI API로 한국어 임베딩 생성
- ✅ 개념 추출
- ❌ 한국어 요약 생성 없음

**요구사항:**
- 환경변수 `OPENAI_API_KEY` 필요

```bash
export OPENAI_API_KEY="sk-your-api-key-here"
```

또는 `.env` 파일에 추가:
```bash
echo "OPENAI_API_KEY=sk-your-api-key-here" >> .env
```

**소요 시간:** 약 10~15분 (API rate limit에 따라)

---

### 4️⃣ 풀 옵션 (매우 느림, 50분~3시간) 🔥

```bash
python build_graph_rag.py --ko-summary --ko-embedding
```

**수행 작업:**
- ✅ 한국어 요약 생성 (Ollama)
- ✅ 한국어 임베딩 생성 (OpenAI)
- ✅ 개념 추출
- ✅ 가장 완전한 Graph RAG 구축

**요구사항:**
- Ollama 서버 실행 중
- `OPENAI_API_KEY` 설정됨

**소요 시간:** 약 50분~3시간

**권장:** 밤에 돌려놓고 자기 🌙

---

### 5️⃣ Ollama 모델 지정

```bash
python build_graph_rag.py --ko-summary --ollama-model=qwen3:14b
```

**기본 모델:** `bge-m3`

**사용 가능한 모델:**
- `llama3.2`
- `gemma2`
- `qwen3:14b`
- `exaone3.5:7.8b`
- 기타 Ollama에서 지원하는 모든 모델

**모델 다운로드:**
```bash
ollama pull qwen3:14b
```

---

## 📁 필요한 파일

### 실행 전 확인

#### 1. 병합된 코퍼스 파일
```bash
ls outputs/ragdb_final_corpus_*.json
```

없으면:
```bash
python merge_korean_corpus.py
```

#### 2. Graph RAG 스키마 파일
```bash
ls graph_rag_schema.json
```

이 파일은 개념 정의와 관계를 담고 있어야 합니다.

---

## 📤 출력 파일

실행 후 `outputs/` 폴더에 다음 파일들이 생성됩니다:

```
outputs/
├── graph_rag_20260129_123456.json              # Graph RAG JSON 데이터
├── graph_rag_neo4j_20260129_123456.cypher      # Neo4j 임포트용 Cypher 스크립트
└── graph_rag_stats_20260129_123456.json        # 통계 정보
```

### 파일 설명

#### `graph_rag_*.json`
- Graph RAG의 노드와 엣지를 JSON 형식으로 저장
- 논문 노드, 개념 노드, MENTIONS 관계 포함
- 한국어 요약/임베딩 포함 (옵션 활성화 시)

#### `graph_rag_neo4j_*.cypher`
- Neo4j 데이터베이스에 직접 임포트 가능한 Cypher 스크립트
- CREATE 문으로 노드와 관계 생성

#### `graph_rag_stats_*.json`
- 그래프 통계 정보
- 논문 수, 개념 수, 관계 수
- 도메인별/언어별 분포

---

## 💡 권장 실행 순서

### 처음 실행하는 경우

```bash
# 1단계: 빠른 테스트 (1~3분)
python build_graph_rag.py

# 2단계: 결과 확인
cat outputs/graph_rag_stats_*.json

# 3단계: 만족하면 풀 옵션 실행 (시간 여유 있을 때)
python build_graph_rag.py --ko-summary --ko-embedding
```

### 반복 실행하는 경우

```bash
# 옵션에 따라 선택
python build_graph_rag.py                        # 빠른 업데이트
python build_graph_rag.py --ko-summary           # 요약 추가
python build_graph_rag.py --ko-embedding         # 임베딩 추가
python build_graph_rag.py --ko-summary --ko-embedding  # 전체
```

---

## ⚠️ 주의사항

### Ollama 사용 시

#### 1. Ollama 서버 실행
```bash
# 별도 터미널에서
ollama serve
```

#### 2. 모델 다운로드 확인
```bash
ollama list
```

#### 3. 필요한 모델 다운로드
```bash
ollama pull bge-m3          # 기본 모델
ollama pull qwen3:14b       # 또는 다른 모델
```

#### 4. Ollama 서버 연결 실패 시
```bash
# Ollama가 실행 중인지 확인
ps aux | grep ollama

# 포트 확인 (기본: 11434)
lsof -i :11434

# 재시작
killall ollama
ollama serve
```

---

### OpenAI API 사용 시

#### 1. API 키 설정
```bash
# 환경변수로 설정
export OPENAI_API_KEY="sk-your-api-key-here"

# 또는 .env 파일에 추가
echo "OPENAI_API_KEY=sk-your-api-key-here" >> .env
```

#### 2. API 키 확인
```bash
echo $OPENAI_API_KEY
```

#### 3. API 사용량 확인
- OpenAI 대시보드에서 사용량 모니터링
- Rate limit 초과 시 대기 시간 증가
- `text-embedding-3-small` 모델 사용 (저렴함)

---

## 📊 예상 소요 시간

### 5000개 논문 기준

| 실행 모드 | 작업 내용 | 소요 시간 |
|----------|----------|---------|
| **기본** | 개념 추출만 | 1~3분 ⚡ |
| **임베딩** | 개념 추출 + 임베딩 | 10~15분 📊 |
| **요약** | 개념 추출 + 요약 | 40분~3시간 🌙 |
| **풀 옵션** | 개념 추출 + 요약 + 임베딩 | 50분~3시간 🔥 |

### 영향 요소

- **논문 수**: 논문이 많을수록 시간 증가
- **영어 논문 비율**: 영어 논문이 많을수록 요약 시간 증가
- **Ollama 모델**: 큰 모델일수록 느림
- **CPU/GPU 성능**: 하드웨어 성능에 비례
- **OpenAI API Rate Limit**: API 제한에 따라 대기 시간 발생

---

## 🐛 문제 해결

### 1. "코퍼스 파일이 없습니다"

```bash
# 먼저 코퍼스 병합 실행
python merge_korean_corpus.py
```

### 2. "스키마 파일이 없습니다"

```bash
# graph_rag_schema.json 파일 확인
ls graph_rag_schema.json

# 없으면 GRAPH_RAG_GUIDE.md 참고하여 생성
```

### 3. "Ollama 연결 실패"

```bash
# Ollama 서버 실행
ollama serve

# 다른 터미널에서 스크립트 실행
python build_graph_rag.py --ko-summary
```

### 4. "OpenAI API 키 없음"

```bash
# 환경변수 설정
export OPENAI_API_KEY="sk-your-key"

# 또는 스크립트에 전달
OPENAI_API_KEY="sk-your-key" python build_graph_rag.py --ko-embedding
```

### 5. 실행 중 멈춤

- **Ollama 요약 생성 중 멈춤**:
  - Ollama 서버 로그 확인
  - 모델 메모리 부족 가능성 (더 작은 모델 사용)
  
- **OpenAI API 호출 중 멈춤**:
  - Rate limit 대기 중 (정상)
  - API 키 만료 확인
  - 네트워크 연결 확인

---

## 📈 성능 최적화

### 빠른 실행
```bash
# 1. 기본 모드로 먼저 실행
python build_graph_rag.py

# 2. 작은 Ollama 모델 사용
python build_graph_rag.py --ko-summary --ollama-model=llama3.2:1b
```

### 정확도 우선
```bash
# 큰 모델 사용
python build_graph_rag.py --ko-summary --ollama-model=qwen3:14b
```

### 비용 절감
```bash
# OpenAI 임베딩 제외 (Ollama만 사용)
python build_graph_rag.py --ko-summary
```

---

## 🔄 업데이트 시나리오

### 새 논문 추가 후
```bash
# 1. 코퍼스 병합
python merge_korean_corpus.py

# 2. Graph RAG 재구축
python build_graph_rag.py --ko-summary --ko-embedding
```

### 스키마 변경 후
```bash
# graph_rag_schema.json 수정 후
python build_graph_rag.py
```

---

## 📚 관련 문서

- **Graph RAG 상세 가이드**: `GRAPH_RAG_GUIDE.md`
- **코퍼스 병합 가이드**: `merge_korean_corpus.py` 주석 참고
- **스키마 정의**: `graph_rag_schema.json`

---

## 🧬 새로운 Graph RAG 기능

### Concept 타입 분류
이제 모든 Concept는 다음 타입으로 분류됩니다:
- **Outcome**: 목표/결과 (예: 근비대, 체지방 감소)
- **Intervention**: 처방/운동 (예: 저항성 운동, 단백질 섭취)
- **Biomarker**: 생체지표 (예: 근육량, 체지방률)
- **Disease**: 질병/증상 (예: 근감소증)
- **Measurement**: 측정 방법 (예: InBody, DEXA)

### Concept 간 관계
도메인 지식 기반으로 자동 생성되는 관계:
```
(resistance_training:Intervention)-[:INCREASES]->(muscle_hypertrophy:Outcome)
(protein_intake:Intervention)-[:SUPPORTS]->(skeletal_muscle_mass:Biomarker)
(calorie_deficit:Intervention)-[:REDUCES]->(body_fat_percentage:Biomarker)
```

### Plan 노드 (운동 처방)
운동 처방 노드 스키마:
- `training_volume`: 주당 총 세트 수
- `intensity`: 강도 (70-85% 1RM, RPE 7-9)
- `frequency`: 주당 운동 빈도
- `recovery`: 세트 간 휴식 시간
- `duration_weeks`: 프로그램 기간
- `exercises`: 운동 종류 리스트
- `progression`: 점진적 과부하 방식

---

## 💬 피드백

문제 발생 시:
1. 에러 메시지 전체 복사
2. 실행 명령어 기록
3. 환경 정보 (Python 버전, OS 등)
4. 이슈 제기

---

**마지막 업데이트**: 2026-01-29
**작성자**: AI Assistant
