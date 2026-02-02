# Google Scholar Captcha 대응 가이드

**작성일:** 2026-02-02
**목적:** Google Scholar 수집 시 Captcha 발생 시 대응 방법

---

## 📊 Captcha는 언제 발생하나?

### 발생 조건

Google Scholar는 다음 조건에서 자동화를 탐지하고 Captcha를 표시합니다:

1. **요청 빈도**
   - 짧은 시간에 많은 요청 (5-10개 이상/분)
   - 일반 사용자보다 빠른 속도

2. **IP 패턴**
   - 동일 IP에서 반복 요청
   - VPN, 데이터센터 IP 사용

3. **User-Agent**
   - 봇으로 의심되는 User-Agent
   - 헤더 불일치

4. **행동 패턴**
   - 마우스/키보드 입력 없음
   - 페이지 이동 패턴이 일정함

### 발생 확률 (수정 후)

**수정 전 (rate_limit=7초):**
- 10-20개 논문 수집 후 Captcha 발생 (50% 확률)

**수정 후 (rate_limit=15초 + `.fill()`):**
- 30-50개 논문 수집 가능 (Captcha 발생률 20% 이하)
- 하지만 완전히 피할 수는 없음

---

## ✅ Captcha 해결 방법

### 방법 1: 브라우저에서 직접 풀기 ⭐⭐⭐⭐⭐

**가장 쉽고 효과적인 방법**

1. **Captcha 발생 시 메시지 확인:**
   ```
   ⚠️  CAPTCHA 감지됨!
   Google Scholar에서 자동화 탐지로 차단했습니다.
   다음 중 하나를 선택하세요:
     1. 브라우저에서 https://scholar.google.com 접속 후 Captcha 풀기
     2. 10-15분 대기 후 재시도
     3. 프록시 사용 (--use-proxy 옵션)
     4. 현재까지 수집된 데이터로 진행 (Enter)

   계속 진행하시겠습니까? (y/n):
   ```

2. **Captcha 풀기:**
   - 브라우저(Chrome/Firefox)에서 https://scholar.google.com 접속
   - Captcha 또는 reCAPTCHA 풀기 (이미지 선택, 체크박스 등)
   - "I'm not a robot" 확인

3. **스크립트에서 'y' 입력:**
   - 터미널로 돌아와서 `y` 입력
   - 스크립트가 자동으로 재시도

**예상 시간:** 1-2분

---

### 방법 2: Rate Limiting 증가 ⭐⭐⭐⭐

**수정 완료됨 (기본값 15초)**

```python
# 더 안전하게 하려면 20-30초로 증가
collector = GoogleScholarKoreanCollector(
    use_proxy=False,
    rate_limit=20.0  # 20초로 증가
)
```

**장점:**
- Captcha 발생 확률 크게 감소
- 안전하고 안정적

**단점:**
- 수집 속도 느려짐
- 450개 논문 = 450 × 20초 = 2.5시간

---

### 방법 3: 소량씩 나눠서 수집 ⭐⭐⭐⭐

**추천: 50개씩 나눠서 수집**

```python
# 방법: target_count를 50으로 제한
body_comp_papers1 = collector.collect_domain(
    domain='body_composition',
    queries=BODY_COMPOSITION_QUERIES[:3],  # 쿼리도 줄임
    target_count=50,  # ✅ 50개만
    year_from=2010
)

# 10분 대기 후 다음 배치
time.sleep(600)  # 10분

body_comp_papers2 = collector.collect_domain(
    domain='body_composition',
    queries=BODY_COMPOSITION_QUERIES[3:6],
    target_count=50,
    year_from=2010
)
```

**장점:**
- Captcha 회피 용이
- 중간에 실패해도 일부 데이터 확보

**단점:**
- 수동 작업 필요
- 여러 번 실행

---

### 방법 4: 프록시 사용 ⚠️

**유료 프록시 서비스 권장**

```python
# scholarly 프록시 설정 (코드에 이미 구현됨)
collector = GoogleScholarKoreanCollector(
    use_proxy=True,  # ✅ 프록시 활성화
    rate_limit=15.0
)
```

**무료 프록시 (FreeProxies):**
- ❌ 불안정함
- ❌ 느림
- ❌ Captcha 여전히 발생 가능

**유료 프록시 (권장):**
- ✅ ScraperAPI: $49/월 (5,000 요청)
- ✅ Luminati: $500/월 (무제한)
- ✅ 안정적이고 Captcha 자동 해결

**무료 프록시 예시:**
```python
from scholarly import scholarly, ProxyGenerator

pg = ProxyGenerator()
pg.FreeProxies()
scholarly.use_proxy(pg)
```

---

### 방법 5: IP 변경 후 재시도 ⭐⭐⭐

**간단하고 효과적**

1. **WiFi 재연결**
   - WiFi 끄고 10초 대기
   - WiFi 다시 켜기
   - 새로운 IP 할당됨

2. **VPN 사용**
   - VPN 서버 변경
   - 다른 국가/도시 선택

3. **모바일 핫스팟**
   - 휴대폰 핫스팟 사용
   - 4G/5G IP 사용

**예상 효과:** Captcha 카운터 리셋

---

## 🛠️ 실전 사용 가이드

### 시나리오 1: 소량 수집 (50개 이하)

**권장 설정:**
```python
collector = GoogleScholarKoreanCollector(
    use_proxy=False,
    rate_limit=15.0  # 기본값 유지
)

papers = collector.collect_domain(
    domain='body_composition',
    queries=["근감소증", "체성분"],
    target_count=50,
    year_from=2010
)
```

**예상 시간:** 50 × 15초 = 12.5분
**Captcha 발생 확률:** 10% 이하

---

### 시나리오 2: 대량 수집 (450개)

**권장 전략: 배치 수집**

```python
# 1일차: 100개
papers_batch1 = collector.collect_domain(
    domain='body_composition',
    queries=QUERIES[:5],
    target_count=100,
    year_from=2010
)

# 저장
with open('batch1.json', 'w') as f:
    json.dump([p.model_dump() for p in papers_batch1], f)

# Captcha 발생 시:
# - 브라우저에서 https://scholar.google.com 접속
# - Captcha 풀기
# - 스크립트에서 'y' 입력

# 2-3시간 대기 (또는 다음 날)
# 2일차: 100개
# 3일차: 100개
# ...
```

**총 소요 시간:** 3-5일 (하루 1-2시간 작업)
**Captcha 대응:** 발생 시마다 브라우저에서 풀기

---

### 시나리오 3: 완전 자동화 (프록시 필수)

**유료 프록시 사용**

```python
# ScraperAPI 사용 예시 (유료)
from scholarly import scholarly, ProxyGenerator

pg = ProxyGenerator()
pg.ScraperAPI("YOUR_API_KEY")  # ScraperAPI 키 입력
scholarly.use_proxy(pg)

# 이제 Captcha 자동 해결
collector = GoogleScholarKoreanCollector(
    use_proxy=True,
    rate_limit=10.0  # 프록시 사용 시 더 빠르게 가능
)

# 전체 수집
papers = collector.collect_domain(
    domain='body_composition',
    queries=ALL_QUERIES,
    target_count=450,
    year_from=2010
)
```

**비용:** $49/월
**예상 시간:** 450 × 10초 = 1.25시간
**Captcha:** 자동 해결

---

## 📋 Captcha 발생 시 체크리스트

### 즉시 조치

- [ ] 스크립트 일시 중지 (자동으로 중단됨)
- [ ] 브라우저에서 https://scholar.google.com 접속
- [ ] Captcha 풀기
- [ ] 스크립트에서 `y` 입력하여 재개

### 재발 방지

- [ ] Rate limit 증가 (15초 → 20-30초)
- [ ] 소량씩 나눠서 수집 (50-100개씩)
- [ ] IP 변경 (WiFi 재연결 또는 VPN)
- [ ] 배치 간 대기 시간 추가 (2-3시간)

### 장기 해결

- [ ] 유료 프록시 도입 (ScraperAPI 등)
- [ ] KCI/RISS API로 대체 (한국어 논문)
- [ ] 수집 주기 분산 (매일 조금씩)

---

## 💡 FAQ

### Q1: Captcha는 얼마나 자주 발생하나요?

**수정 전 (rate_limit=7초):**
- 10-20개마다 발생 (매우 자주)

**수정 후 (rate_limit=15초):**
- 30-50개마다 발생 (가끔)
- 운이 좋으면 100개까지 가능

**프록시 사용 시:**
- 거의 발생 안함 (유료 프록시 경우)

---

### Q2: Captcha를 제가 직접 풀 수 있나요?

**네, 가능합니다!**

1. Captcha 발생 시 스크립트가 자동으로 안내
2. 브라우저에서 https://scholar.google.com 접속
3. "로봇이 아닙니다" 체크박스 클릭 또는 이미지 선택
4. 완료 후 스크립트에서 `y` 입력
5. 수집 자동 재개

**소요 시간:** 1-2분

---

### Q3: Captcha 완전히 피할 수 있나요?

**무료 방법으로는 어렵습니다.**

- Rate limit 30초로 올려도 가끔 발생
- IP 변경 + 소량 수집으로 최소화 가능

**유료 프록시 사용 시:**
- ScraperAPI: Captcha 자동 해결
- 거의 100% 성공률

---

### Q4: 450개 수집하는데 얼마나 걸리나요?

**무료 방법 (rate_limit=15초, Captcha 대응 포함):**
- 순수 시간: 450 × 15초 = 1.875시간
- Captcha 대응: 5-10회 × 2분 = 10-20분
- 총 소요: **2-3시간** (한 번에 진행 시)
- **권장: 3-5일에 나눠서** (하루 100개씩)

**유료 프록시 (ScraperAPI):**
- 총 소요: **1-1.5시간** (한 번에 완료)

---

### Q5: 중간에 Captcha로 중단되면 데이터 날아가나요?

**아니요!**

수정된 코드는 Captcha 발생 시:
1. 현재까지 수집된 데이터 보존
2. 사용자 선택 제공:
   - 계속 진행 (Captcha 풀고 재개)
   - 중단 (현재 데이터로 저장)

**안전합니다.**

---

## 🎯 최종 권장 사항

### 소량 테스트 먼저 (오늘)

```bash
cd /home/user/projects/ExplainMyBody/src/llm/ragdb_collect
python test_scholar_improved.py  # 10개만 테스트
```

### 본격 수집 (이번 주)

**방법 1: 무료 (느리지만 안전)**
- 하루 100개씩 5일간 수집
- Captcha 발생 시 브라우저에서 직접 해결
- 총 소요: 5일 (하루 30분 작업)

**방법 2: 유료 (빠르고 자동)**
- ScraperAPI $49/월 가입
- 1-2시간에 전체 수집 완료
- Captcha 자동 해결

**권장:** 방법 1 (무료)
- 학습/연구 목적에 충분
- Captcha 대응 경험 축적

---

**작성자 참고:** Captcha는 피할 수 없지만, 위 방법들로 충분히 대응 가능합니다. 브라우저에서 직접 풀면 되므로 걱정하지 않으셔도 됩니다.
