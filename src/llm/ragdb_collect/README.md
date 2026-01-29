# RAG 코퍼스 수집 파이프라인

ExplainMyBody를 위한 **4개 축 동등 분배** RAG 코퍼스 자동 수집 시스템

## 📊 수집 전략

### 4개 축 동등 분배 (총 3000개 목표)

| 축 | 도메인 | 목표 개수 | 소스 | 언어 |
|---|--------|----------|------|------|
| 1️⃣ | 단백질/근육 증가 | 800개 | PubMed | 영어 |
| 2️⃣ | 체지방 감량/다이어트 | 800개 | PubMed | 영어 |
| 3️⃣ | 한국형 식단/한식 | 600개 | PubMed + KCI | 영어 + 한국어 |
| 4️⃣ | 체형 분석/인바디 | 800개 | PubMed + KCI | 영어 + 한국어 |

### 왜 이 전략?

✅ **초록 중심**: Full-text PDF 대신 초록만 수집 (검색 효율성 ↑)
✅ **공식 가이드 포함**: WHO, ISSN 등 공식 문서 포함
✅ **한국 데이터 강화**: KNHANES, KCI 한국어 논문 포함
✅ **도메인 태깅**: Metadata에 `domain` 필드로 분류

## 🚀 빠른 시작

### 1. 의존성 설치

```bash
pip install requests pydantic
```

### 2. PubMed 논문 수집 (자동)

```bash
cd /home/user/projects/ExplainMyBody/llm/ragdb_collect

python main.py --email your_email@example.com
```

**선택: API Key 사용 (속도 향상)**

1. NCBI 계정 생성: https://www.ncbi.nlm.nih.gov/account/
2. API Key 발급: https://www.ncbi.nlm.nih.gov/account/settings/
3. 실행:

```bash
python main.py \
  --email your_email@example.com \
  --api-key YOUR_API_KEY
```

### 3. 결과 확인

```bash
ls outputs/

# 출력:
# ragdb_corpus_20240128_143022.json       # 전체 논문
# protein_hypertrophy_20240128_143022.json  # 도메인별 분할
# fat_loss_20240128_143022.json
# korean_diet_20240128_143022.json
# body_composition_20240128_143022.json
# stats_20240128_143022.json               # 통계
# kci_template.json                         # KCI 수동 수집 템플릿
```

## 📁 파일 구조

```
ragdb_collect/
├── config.py              # 검색어 설정 (4개 축별)
├── models.py              # 데이터 모델 (PaperMetadata)
├── pubmed_collector.py    # PubMed API 수집기
├── kci_collector.py       # KCI 수동 수집 가이드
├── main.py                # 메인 실행 파일
├── README.md              # 이 문서
└── outputs/               # 수집 결과
```

## 🔍 검색어 설정

### 1. 단백질/근육 증가 (`config.py`)

```python
PROTEIN_HYPERTROPHY_QUERIES = [
    "(resistance training) AND (protein intake) AND hypertrophy",
    "muscle protein synthesis AND leucine",
    "whey supplementation AND strength gain",
    # ... 총 10개
]
```

### 2. 체지방 감량/다이어트

```python
FAT_LOSS_QUERIES = [
    "calorie deficit AND fat loss AND body composition",
    "high protein diet AND weight loss AND lean mass",
    # ... 총 10개
]
```

### 3. 한국형 식단/한식

**영어 검색어 (PubMed)**:
```python
KOREAN_DIET_QUERIES_EN = [
    "Korean diet AND health outcomes",
    "kimchi AND fermented foods AND microbiome",
    # ... 총 6개
]
```

**한국어 검색어 (KCI - 수동 수집)**:
```python
KOREAN_DIET_QUERIES_KO = [
    "한식 식사패턴",
    "김치 섭취 건강",
    # ... 총 10개
]
```

### 4. 체형 분석/인바디

**영어 검색어**:
```python
BODY_COMPOSITION_QUERIES_EN = [
    "bioelectrical impedance analysis AND body composition",
    "skeletal muscle mass index AND sarcopenia",
    # ... 총 8개
]
```

**한국어 검색어 (KCI)**:
```python
BODY_COMPOSITION_QUERIES_KO = [
    "근감소증 한국인",
    "체성분 분석 인바디",
    # ... 총 6개
]
```

## 📄 출력 JSON 형식

### PaperMetadata 구조

```json
{
  "domain": "protein_hypertrophy",
  "language": "en",
  "title": "Effects of protein supplementation on muscle hypertrophy...",
  "abstract": "This systematic review examined the effects of...",
  "keywords": ["protein", "hypertrophy", "resistance training"],
  "source": "PubMed",
  "year": 2021,
  "pmid": "12345678",
  "doi": "10.1234/example",
  "authors": ["John Doe", "Jane Smith"],
  "journal": "Journal of Sports Nutrition"
}
```

### Metadata 필드 설명

| 필드 | 설명 | 예시 |
|------|------|------|
| `domain` | 분야 (4개 축) | `protein_hypertrophy`, `fat_loss`, `korean_diet`, `body_composition` |
| `language` | 언어 | `en`, `ko` |
| `title` | 논문 제목 | "Effects of protein..." |
| `abstract` | 초록 전문 | "This systematic review..." |
| `keywords` | 키워드 리스트 | `["protein", "hypertrophy"]` |
| `source` | 출처 | `PubMed`, `KCI` |
| `year` | 발행 연도 | `2021` |
| `pmid` | PubMed ID | `"12345678"` |
| `doi` | DOI | `"10.1234/example"` |
| `authors` | 저자 리스트 (최대 5명) | `["John Doe", ...]` |
| `journal` | 저널명 | `"Journal of Sports Nutrition"` |

## 🇰🇷 한국어 논문 수동 수집

### 왜 수동 수집?

- KCI는 공식 API가 제한적
- 초록 품질 확인 필요
- 목표: 영어 논문과 동등한 품질

### 수집 방법

#### 방법 1: KCI 웹사이트

1. https://www.kci.go.kr/ 접속
2. 검색창에 키워드 입력:
   - "한식 식사패턴"
   - "김치 섭취 건강"
   - "단백질 섭취 실태"
3. "초록" 있는 논문만 선택
4. Excel/CSV 다운로드
5. `kci_template.json` 형식으로 변환

#### 방법 2: KoreaScience

1. https://www.koreascience.or.kr/ 접속
2. 검색 후 초록 복사
3. JSON 파일 작성

#### 방법 3: RISS

1. http://www.riss.kr/ 접속
2. 검색 후 초록 복사
3. JSON 파일 작성

### 템플릿 사용

```bash
# 템플릿 자동 생성됨
cat outputs/kci_template.json
```

```json
[
  {
    "title": "논문 제목",
    "abstract": "초록 전문 (최소 100자 이상)",
    "keywords": ["키워드1", "키워드2"],
    "year": 2020,
    "authors": ["저자1", "저자2"],
    "journal": "학술지명"
  }
]
```

### 수동 수집 논문 추가

```python
from kci_collector import KCICollector
import json

# JSON 파일 로드
with open("my_korean_papers.json", "r", encoding="utf-8") as f:
    papers_data = json.load(f)

# PaperMetadata로 변환
kci = KCICollector()
papers = kci.parse_manual_json(papers_data, domain="korean_diet")

# 기존 수집 결과와 병합
with open("outputs/ragdb_corpus_XXXXXX.json", "r", encoding="utf-8") as f:
    existing = json.load(f)

existing.extend([p.model_dump() for p in papers])

# 저장
with open("outputs/ragdb_corpus_merged.json", "w", encoding="utf-8") as f:
    json.dump(existing, f, ensure_ascii=False, indent=2)
```

## ⚙️ 설정 커스터마이징

### 목표 개수 조정 (`config.py`)

```python
PROTEIN_HYPERTROPHY_TARGET = 800  # 기본값
FAT_LOSS_TARGET = 800
KOREAN_DIET_TARGET = 600
BODY_COMPOSITION_TARGET = 800
```

### 쿼리당 결과 수 조정

```python
PUBMED_RESULTS_PER_QUERY = 100  # 기본값 (최대 10,000)
```

### 이메일 및 API Key 설정

```python
PUBMED_EMAIL = "your_email@example.com"
PUBMED_API_KEY = "YOUR_API_KEY"  # 선택사항
```

## 📊 통계 예시

```json
{
  "total_collected": 2400,
  "by_domain": {
    "protein_hypertrophy": 800,
    "fat_loss": 800,
    "korean_diet": 300,
    "body_composition": 500
  },
  "by_language": {
    "en": 2400
  },
  "by_source": {
    "PubMed": 2400
  },
  "failed_count": 0
}
```

## 🚨 주의사항

### PubMed API Rate Limit

| 상태 | 제한 |
|------|------|
| API Key 없음 | 초당 3개 요청 |
| API Key 있음 | 초당 10개 요청 |

코드에서 자동으로 sleep 처리됨.

### 저작권

- 초록(Abstract)은 일반적으로 공개 사용 가능
- Full-text는 저작권 확인 필요
- 상업적 사용 시 라이선스 확인

### KCI 이용약관

- 웹 스크래핑 전 이용약관 확인
- 대량 수집 시 허가 필요할 수 있음
- 수동 수집 권장

## 🇰🇷 한국어 논문 자동 수집

**🔥 목표 600개 돌파! API를 사용하면 1800-2300개까지 완전 자동 수집 가능!**

### ⚡ 빠른 시작: API 사용 (추천, 1시간)

**한국 공식 API로 완전 자동 수집!**

```bash
# 1. KCI API 수집 (300-500개, 즉시 사용)
python kci_api_collector.py

# 2. RISS API 수집 (500-800개, 즉시 사용)
python riss_api_collector.py

# 3. ScienceON API 수집 (1000+개, 승인 후)
python scienceon_api_collector.py

# 4. 전체 병합
python merge_korean_corpus.py

# → 1800-2300개 한국어 논문 자동 수집! 🎉
```

**API 키 발급 가이드**: [KOREAN_API_GUIDE.md](./KOREAN_API_GUIDE.md) ⭐

### 🔧 추가 수집: 반자동/수동 방법 (선택)

```bash
# 1. Google Scholar 자동 수집 (200-300개)
python google_scholar_korean_collector.py

# 2. 정부 보고서 파싱 (80-130개)
python government_report_parser.py
# → outputs/government_reports_template.json 수정 후:
python government_report_parser.py --process

# 3. 학술지 CSV 파싱 (130-230개)
python society_csv_parser.py
# → 학회 사이트에서 CSV 다운로드 후:
python society_csv_parser.py --process [CSV파일]

# 4. 전체 병합
python merge_korean_corpus.py
```

### 📖 자세한 가이드

**한국어 논문 수집 방법별 가이드:**

- **[KOREAN_API_GUIDE.md](./KOREAN_API_GUIDE.md)** ⭐ **추천!** - 공식 API로 완전 자동 수집 (KCI, RISS, ScienceON)
- **[KOREAN_COLLECTION_GUIDE.md](./KOREAN_COLLECTION_GUIDE.md)** - Google Scholar, 정부 보고서, 학술지 CSV 수집

**예상 수집량 비교:**

| 방법 | 수집량 | 소요 시간 | 자동화 |
|------|--------|----------|--------|
| **API만** | 1800-2300개 | 1시간 | 🟢 완전 자동 |
| **API + 기타** | 2200-2960개 | 4-5시간 | 🟡 반자동 |
| **Google Scholar + 기타** | 560-960개 | 3-5시간 | 🟡 반자동 |

## 🔄 다음 단계

### 1. Chunking

```bash
# TODO: chunking 파이프라인 작성
python chunk_abstracts.py \
  --input outputs/ragdb_corpus_XXXXXX.json \
  --output outputs/ragdb_chunks.json
```

### 2. Embedding 생성

```bash
# TODO: embedding 파이프라인 작성
python create_embeddings.py \
  --input outputs/ragdb_chunks.json \
  --model text-embedding-3-small \
  --output outputs/ragdb_embeddings.json
```

### 3. DB 저장

```bash
# TODO: pgvector 저장 파이프라인 작성
python save_to_db.py \
  --input outputs/ragdb_embeddings.json
```

## 🛠 트러블슈팅

### "No results found"

- 검색어가 너무 구체적일 수 있음
- `config.py`에서 검색어 수정

### "Rate limit exceeded"

- API Key 사용 권장
- `PUBMED_RESULTS_PER_QUERY` 줄이기

### "XML parsing error"

- PubMed API 일시적 오류
- 재실행

## 📚 참고 자료

- PubMed API: https://www.ncbi.nlm.nih.gov/books/NBK25501/
- KCI: https://www.kci.go.kr/
- KoreaScience: https://www.koreascience.or.kr/
- ISSN Position Stand: https://www.sportsnutritionsociety.org/
- WHO Guidelines: https://www.who.int/publications/

## 🤝 기여

검색어 추가 제안:
1. `config.py` 수정
2. Pull Request

## 📝 라이선스

MIT License
