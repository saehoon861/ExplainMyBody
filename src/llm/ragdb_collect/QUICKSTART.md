# 🚀 빠른 시작 가이드

## 1분 안에 시작하기

### Step 1: 의존성 설치

```bash
cd /home/user/projects/ExplainMyBody/llm/ragdb_collect
pip install -r requirements.txt
```

### Step 2: 수집 실행

```bash
python main.py --email your_email@example.com
```

**예상 소요 시간**: 약 30-60분 (API Key 없이)

### Step 3: 결과 확인

```bash
ls outputs/

# 예시:
# ragdb_corpus_20240128_143022.json       - 전체 2400개 논문
# protein_hypertrophy_20240128_143022.json - 800개
# fat_loss_20240128_143022.json           - 800개
# korean_diet_20240128_143022.json        - 300개 (영어만)
# body_composition_20240128_143022.json   - 500개 (영어만)
# stats_20240128_143022.json              - 통계
```

## ⚡ 빠른 수집 (API Key 사용)

### 1. NCBI API Key 발급 (5분)

1. https://www.ncbi.nlm.nih.gov/account/ 회원가입
2. Settings → API Key Management
3. Create an API Key
4. 복사

### 2. 수집 실행 (10배 빠름)

```bash
python main.py \
  --email your_email@example.com \
  --api-key YOUR_API_KEY_HERE
```

**예상 소요 시간**: 약 10-15분 (API Key 사용)

## 📊 수집 예상 결과

| 도메인 | 목표 | 예상 실제 수집 |
|--------|------|---------------|
| 단백질/근육 | 800개 | ~700-800개 |
| 체지방 감량 | 800개 | ~700-800개 |
| 한국 식단 (영어) | 300개 | ~200-300개 |
| 체형/인바디 (영어) | 500개 | ~400-500개 |
| **총합** | **2400개** | **~2000-2400개** |

## 🇰🇷 한국어 논문 추가 (선택)

### 목표

- 한국 식단: 추가 300개
- 체형/인바디: 추가 300개

### 방법

1. `outputs/kci_template.json` 열기
2. KCI/RISS에서 검색
3. 초록 복사하여 JSON 작성
4. 병합:

```python
from kci_collector import KCICollector
import json

# 수동 수집 논문 로드
with open("my_korean_papers.json", "r") as f:
    korean_papers = json.load(f)

# 변환
kci = KCICollector()
papers = kci.parse_manual_json(korean_papers, domain="korean_diet")

# 기존 결과와 병합
with open("outputs/ragdb_corpus_XXXXXX.json", "r") as f:
    existing = json.load(f)

existing.extend([p.model_dump() for p in papers])

# 저장
with open("outputs/ragdb_corpus_final.json", "w") as f:
    json.dump(existing, f, ensure_ascii=False, indent=2)
```

## 🎯 최종 목표

```
단백질/근육: 800개 ✅
체지방 감량: 800개 ✅
한국 식단: 600개 (영어 300 + 한국어 300)
체형/인바디: 800개 (영어 500 + 한국어 300)
═══════════════════════════════════════
총 3000개 코퍼스 완성! 🎉
```

## ❓ 문제 해결

### "No module named 'pydantic'"

```bash
pip install pydantic requests
```

### "Rate limit exceeded"

API Key를 사용하거나 `config.py`에서 `PUBMED_RESULTS_PER_QUERY`를 50으로 줄이세요.

### "Empty results"

정상입니다. 일부 검색어는 결과가 적을 수 있습니다.

## 📞 도움말

자세한 내용은 `README.md` 참고
