# 한국어 논문 API 자동 수집 가이드

**완전 자동화!** 한국 공식 API를 사용하여 한국어 논문을 자동으로 대량 수집합니다.

## 🎯 왜 API를 사용하나요?

| 방법 | 장점 | 단점 |
|------|------|------|
| **Google Scholar** | 다양한 출처 | 느림, Rate limit |
| **PDF 파싱** | 공식 문서 | 수동 다운로드 |
| **CSV 파싱** | 대량 수집 | 수동 다운로드 |
| **🔥 API 사용** | **완전 자동, 빠름, 안정적** | API 키 발급 필요 |

## 📊 한국어 논문 API 3종 비교

### 1. KCI OpenAPI ⭐⭐⭐

**한국학술지인용색인 (Korean Citation Index)**

| 항목 | 내용 |
|------|------|
| **제공기관** | 한국연구재단 |
| **데이터** | KCI 등재 학술지 논문 |
| **특징** | 국내 최고 품질, 심사 완료 논문만 |
| **API 키 발급** | [공공데이터포털](https://www.data.go.kr/data/3049042/openapi.do) |
| **발급 시간** | 즉시 (회원가입 후) |
| **비용** | 무료 |
| **예상 수집** | 300-500개 |

**장점**:
- ✅ 품질 보장 (KCI 등재지만)
- ✅ 즉시 발급
- ✅ 공공 API (안정적)

**단점**:
- ⚠️ 등재지 논문만 (범위 제한)
- ⚠️ Rate limit 있음

### 2. RISS OpenAPI ⭐⭐⭐⭐

**학술연구정보서비스 (Research Information Sharing Service)**

| 항목 | 내용 |
|------|------|
| **제공기관** | 한국교육학술정보원(KERIS) |
| **데이터** | 학위논문 + 국내외 학술지 |
| **특징** | 학위논문 포함, 가장 접근성 좋음 |
| **API 키 발급** | [공공데이터포털](https://www.data.go.kr/data/3046254/openapi.do) 또는 [RISS](https://www.riss.kr/openAPI/OpenApiMain.do) |
| **발급 시간** | 즉시 |
| **비용** | 무료 |
| **예상 수집** | 500-800개 |

**장점**:
- ✅ 학위논문 포함 (독특한 데이터)
- ✅ 가장 사용자 친화적
- ✅ 초록 제공 많음

**단점**:
- ⚠️ 일부 논문은 초록 없음

### 3. ScienceON API Gateway ⭐⭐⭐⭐⭐

**KISTI 과학기술 지식인프라**

| 항목 | 내용 |
|------|------|
| **제공기관** | 한국과학기술정보연구원(KISTI) |
| **데이터** | **1억 3780만 건 논문** (2026-01-19) |
| **특징** | 최대 규모, 과학기술 논문 강력 |
| **API 키 발급** | [ScienceON API Gateway](https://scienceon.kisti.re.kr/apigateway/) |
| **발급 시간** | 1-2일 (승인 필요) |
| **비용** | 무료 |
| **예상 수집** | 1000+ 개 |

**장점**:
- ✅ **압도적 데이터량** (1억 건+)
- ✅ 과학기술 논문 강력
- ✅ OAuth 2.0 (전문적)
- ✅ 검색 성능 우수

**단점**:
- ⚠️ 승인 1-2일 소요
- ⚠️ OAuth 설정 필요

## 🚀 빠른 시작 (3가지 방법)

### 방법 1: KCI API (즉시 사용 가능) ⚡

**1단계: API 키 발급 (5분)**

```
1. https://www.data.go.kr/ 접속
2. 회원가입 (소셜 로그인 가능)
3. 검색: "KCI 논문정보서비스"
4. 활용신청 클릭 → 즉시 승인
5. API 키 복사
```

**2단계: 수집 실행**

```bash
cd /home/user/projects/ExplainMyBody/llm/ragdb_collect

python kci_api_collector.py
# API 키 입력 → 자동 수집 시작
```

**예상 결과**: 300-500개 한국어 논문 (10-20분)

### 방법 2: RISS API (학위논문 포함) 📚

**1단계: API 키 발급 (5분)**

```
옵션 A (추천):
1. https://www.data.go.kr/ 접속
2. 검색: "RISS 학술연구정보"
3. 활용신청 → 즉시 승인

옵션 B:
1. https://www.riss.kr/openAPI/OpenApiMain.do
2. API 키 신청
```

**2단계: 수집 실행**

```bash
python riss_api_collector.py
# API 키 입력
# 학위논문 포함 여부 선택 (y/n)
```

**예상 결과**: 500-800개 한국어 논문 (15-30분)

### 방법 3: ScienceON API (최대 규모) 🚀

**1단계: API 키 발급 (1-2일)**

```
1. https://scienceon.kisti.re.kr/apigateway/ 접속
2. 회원가입
3. API 사용 신청
4. 관리자 승인 대기 (1-2일)
5. Client ID, Client Secret 발급
```

**2단계: 수집 실행**

```bash
python scienceon_api_collector.py
# Client ID 입력
# Client Secret 입력
```

**예상 결과**: 1000+ 개 한국어 논문 (20-40분)

## 📦 통합 워크플로우 (추천)

**3개 API를 모두 사용하여 최대 수집!**

### 1단계: 즉시 수집 (1시간)

```bash
# KCI (즉시 사용 가능)
python kci_api_collector.py

# RISS (즉시 사용 가능)
python riss_api_collector.py

# → 800-1300개 수집 완료
```

### 2단계: ScienceON 추가 (1-2일 후)

```bash
# ScienceON (승인 후)
python scienceon_api_collector.py

# → 추가 1000개 수집
```

### 3단계: 전체 병합

```bash
python merge_korean_corpus.py

# 자동 처리:
# - PubMed 영어 논문 (2400개)
# - KCI 한국어 (300-500개)
# - RISS 한국어 (500-800개)
# - ScienceON 한국어 (1000+개)
# - Google Scholar 한국어 (200-300개, 선택)
# ──────────────────────────────────
# 총 4400-5000개 논문! 🎉
```

## 🔑 API 키 발급 상세 가이드

### KCI API 키 발급

1. **공공데이터포털 접속**: https://www.data.go.kr/
2. **회원가입** (이미 가입되어 있다면 로그인)
3. **검색창에 입력**: "한국연구재단 KCI 논문정보서비스"
4. **활용신청 클릭**
   - 활용목적: "학술 연구 및 데이터 분석"
   - 활용기간: 1년
5. **즉시 승인** (자동)
6. **마이페이지 → 오픈API → 일반 인증키(Encoding)** 복사

### RISS API 키 발급

**방법 A: 공공데이터포털 (추천)**

1. https://www.data.go.kr/
2. 검색: "한국교육학술정보원 학술연구정보"
3. 활용신청 → 즉시 승인
4. API 키 복사

**방법 B: RISS 직접**

1. https://www.riss.kr/openAPI/OpenApiMain.do
2. API 키 신청서 작성
3. 승인 (몇 시간~1일)
4. API 키 발급

### ScienceON API 키 발급

1. **ScienceON API Gateway 접속**: https://scienceon.kisti.re.kr/apigateway/
2. **회원가입** (KISTI 통합 회원가입)
3. **API 사용 신청**
   - 로그인 후 "API 사용 신청" 메뉴
   - 용도: "학술 연구 및 RAG 시스템 구축"
   - 예상 사용량: "월 10,000건"
4. **관리자 승인 대기** (1-2일)
5. **승인 알림 메일 수신**
6. **Client ID, Client Secret 확인**
   - 마이페이지 → API 관리

## 💻 사용 예시

### KCI API

```bash
$ python kci_api_collector.py

API 키를 입력하세요: YOUR_KCI_API_KEY

🔍 KCI 검색: '한식 식사패턴' (최대 50개)
  📊 총 234개 논문 발견
  ✅ 1/1 페이지: 50개 수집 (총 50개)
✅ KCI 검색 완료: 50개 수집

...

📊 수집 완료
총 수집: 520개
  - 한국 식단: 280개
  - 체형 분석: 240개
```

### RISS API

```bash
$ python riss_api_collector.py

API 키를 입력하세요: YOUR_RISS_API_KEY

학위논문도 포함할까요? (y/n, 기본: n): y

🔍 RISS 검색: '한식 건강' (최대 60개)
  📊 총 1,245개 논문 발견
  ✅ 1/1 페이지: 60개 수집 (총 60개)

...

📊 수집 완료
총 수집: 680개
  - 한국 식단: 350개
  - 체형 분석: 330개
```

### ScienceON API

```bash
$ python scienceon_api_collector.py

Client ID를 입력하세요: YOUR_CLIENT_ID
Client Secret을 입력하세요: YOUR_CLIENT_SECRET

🔑 액세스 토큰 발급 중...
✅ 액세스 토큰 발급 완료

🔍 ScienceON 검색: '한식 영양' (최대 60개)
  📊 총 3,456개 논문 발견
  ✅ 1/1 페이지: 60개 수집 (총 60개)

...

📊 수집 완료
총 수집: 1,200개
  - 한국 식단: 600개
  - 체형 분석: 600개
```

## ⚙️ 커스터마이징

### 검색어 추가

각 스크립트의 `main()` 함수에서 검색어 리스트를 수정할 수 있습니다:

```python
# kci_api_collector.py, riss_api_collector.py, scienceon_api_collector.py

KOREAN_DIET_QUERIES = [
    "한식 식사패턴",
    "김치 섭취",
    "여기에 추가 검색어",  # 새로운 검색어 추가
]
```

### 목표 개수 조정

```python
korean_diet_papers = collector.collect_domain(
    domain='korean_diet',
    queries=KOREAN_DIET_QUERIES,
    target_count=500,  # 300 → 500으로 늘리기
    start_year=2010
)
```

### 연도 범위 조정

```python
target_count=300,
start_year=2015,  # 2010 → 2015로 변경 (최신 논문만)
```

## 📊 예상 수집량 비교

| API | 즉시 사용 | 예상 수집 | 소요 시간 | 품질 |
|-----|----------|-----------|----------|------|
| KCI | ✅ | 300-500개 | 10-20분 | ⭐⭐⭐⭐⭐ |
| RISS | ✅ | 500-800개 | 15-30분 | ⭐⭐⭐⭐ |
| ScienceON | ❌ (1-2일) | 1000+개 | 20-40분 | ⭐⭐⭐⭐⭐ |
| **3개 통합** | - | **1800-2300개** | **45-90분** | **⭐⭐⭐⭐⭐** |

**기타 방법 추가 시**:
- Google Scholar: +200-300개 (1-2시간)
- 정부 보고서: +80-130개 (30-60분)
- 학술지 CSV: +130-230개 (30-60분)

**총 잠재 수집량**: **2210-2960개 한국어 논문!**

## 🚨 주의사항

### Rate Limiting

각 API는 Rate Limit이 있습니다:

| API | 제한 | 대응 |
|-----|------|------|
| KCI | 초당 1-2개 | 코드에서 자동 대기 |
| RISS | 초당 1-2개 | 코드에서 자동 대기 |
| ScienceON | 초당 2-5개 | OAuth 토큰 자동 관리 |

### API 키 보안

- ❌ API 키를 Git에 커밋하지 마세요
- ✅ 환경 변수 사용 권장:

```bash
export KCI_API_KEY="your_key_here"
export RISS_API_KEY="your_key_here"
export SCIENCEON_CLIENT_ID="your_id_here"
export SCIENCEON_CLIENT_SECRET="your_secret_here"
```

스크립트 수정:
```python
import os

api_key = os.getenv('KCI_API_KEY') or input("API 키를 입력하세요: ")
```

### 초록 없는 논문

일부 논문은 초록이 없을 수 있습니다. 스크립트는 자동으로:
- 초록 100자 미만 논문 제외
- 중복 논문 제거

## 🔧 트러블슈팅

### "API 요청 실패 (status: 401)"

**원인**: API 키가 잘못되었거나 만료됨

**해결**:
1. API 키 재확인
2. 공공데이터포털에서 키 상태 확인
3. 필요시 재발급

### "토큰 발급 실패" (ScienceON)

**원인**: Client ID/Secret 오류

**해결**:
1. 공백 없이 정확히 복사
2. 승인 상태 확인 (마이페이지)
3. 1-2일 후 재시도

### "총 0개 논문 발견"

**원인**: 검색어가 너무 구체적이거나 잘못됨

**해결**:
1. 검색어 단순화 ("한식 식사패턴" → "한식")
2. 연도 범위 확대 (2015 → 2010)
3. 다른 검색어 시도

### "초록이 너무 짧음"

**원인**: 초록 길이 필터 (100자)

**해결** (필요시):
```python
# 각 스크립트의 _parse_XXX_item() 함수에서:
if len(abstract) < 50:  # 100 → 50으로 줄이기
    return None
```

## 📚 참고 자료

### API 문서
- [KCI OpenAPI 가이드](https://www.data.go.kr/data/3049042/openapi.do)
- [RISS OpenAPI 가이드](https://www.data.go.kr/data/3046254/openapi.do)
- [ScienceON API Gateway](https://scienceon.kisti.re.kr/apigateway/)
- [공공데이터포털](https://www.data.go.kr/)

### 관련 문서
- [한국어 논문 자동 수집 가이드](./KOREAN_COLLECTION_GUIDE.md)
- [RAG 코퍼스 수집 전체 가이드](./README.md)
- [빠른 시작 가이드](./QUICKSTART.md)

## 🎯 최종 목표 달성 전략

### 전략 A: 즉시 시작 (API만)

```bash
# Day 1 (1시간)
python kci_api_collector.py        # 300-500개
python riss_api_collector.py       # 500-800개
python merge_korean_corpus.py

# → 즉시 800-1300개 한국어 논문 확보! ✅
```

### 전략 B: 최대 수집 (API + 기타)

```bash
# Day 1 (4시간)
python kci_api_collector.py        # 300-500개
python riss_api_collector.py       # 500-800개
python google_scholar_korean_collector.py  # 200-300개
# 정부 보고서, 학술지 CSV 추가 수집...

# Day 3 (ScienceON 승인 후, 1시간)
python scienceon_api_collector.py  # 1000+개

# 병합
python merge_korean_corpus.py

# → 총 2200-2960개 한국어 논문! 🎉🎉🎉
```

## ✅ 체크리스트

**API 키 발급**:
- [ ] KCI API 키 발급 (즉시)
- [ ] RISS API 키 발급 (즉시)
- [ ] ScienceON API 신청 (1-2일 대기)

**수집 실행**:
- [ ] `kci_api_collector.py` 실행
- [ ] `riss_api_collector.py` 실행
- [ ] (선택) `google_scholar_korean_collector.py` 실행
- [ ] (승인 후) `scienceon_api_collector.py` 실행

**병합 및 검증**:
- [ ] `merge_korean_corpus.py` 실행
- [ ] 통계 확인 (목표 600개 이상)
- [ ] 최종 코퍼스 검증

## 📞 도움말

문제가 발생하면:
1. 이 가이드의 트러블슈팅 섹션 확인
2. API 제공 기관 문의
3. GitHub Issue 생성

**성공을 기원합니다!** 🚀
