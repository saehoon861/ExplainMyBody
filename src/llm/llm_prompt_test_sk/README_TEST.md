# 사용자 프로필 기반 프롬프트 테스트 가이드

## 🧪 테스트 종류

### 1. 프롬프트 검증 (LLM 호출 없음)
**파일:** `test_user_profile_prompt.py`

프롬프트가 올바르게 생성되는지 확인 (비용 없음)

```bash
cd src/llm/llm_prompt_test_sk
python test_user_profile_prompt.py
```

**출력:**
- 생성된 프롬프트 확인
- 전략 텍스트 포함 여부 확인
- 다양한 프로필별 프롬프트 비교

---

### 2. 실제 LLM 호출 테스트 (GPT-4o-mini)
**파일:** `test_llm_call.py`

실제 OpenAI API를 호출하여 응답 확인 (비용 발생)

#### 사전 준비

```bash
# OpenAI API 키 설정
export OPENAI_API_KEY='your-api-key-here'

# 또는 .env 파일에 추가
echo "OPENAI_API_KEY=your-api-key-here" >> .env
```

#### 실행 방법

**A. 빠른 테스트 (SAMPLE_USER만)**

```bash
python test_llm_call.py --quick
```

**B. 전체 테스트 (모든 프로필)**

```bash
python test_llm_call.py
```

대화형으로 진행되며 각 단계에서 확인을 요청합니다.

---

## 📊 출력 결과

### 프롬프트 검증 (`test_user_profile_prompt.py`)

```
🧪 사용자 프로필 기반 프롬프트 생성 테스트
================================================================================

📋 프로필: SAMPLE_USER (기본)
체형: 마른비만형 / 상체비만형
장소: 홈트

🎯 Prompt 1: 주간 목표 요약
--------------------------------------------------------------------------------

[User Prompt - 전략 섹션만 발췌]

[전체 체형 전략]
- 목표: 체지방 줄이면서 근육 늘리기 동시에
- 식단: 단백질 많이, 밥은 현미/고구마 같은 좋은 탄수화물로
- 운동: 근력운동이 메인, 유산소는 보조로만
...
```

### 실제 LLM 호출 (`test_llm_call.py`)

```
🤖 LLM 호출 테스트: SAMPLE_USER
================================================================================
체형: 마른비만형 / 상체비만형
장소: 홈트

🎯 Prompt 1: 주간 목표 요약 (3가지 핵심 전략)
--------------------------------------------------------------------------------

[LLM 호출 중...]

[LLM 응답]
🎯 주간 목표 (한 줄 요약)
이번 주는 집에서 할 수 있는 근력 운동으로 근육량을 늘리고,
체지방을 줄이기 위한 식단 조절에 집중합니다.

💪 핵심 전략 1:
맨몸 근력 운동 (푸쉬업, 스쿼트, 플랭크)을 매일 진행하여
전신 근육을 자극하고 기초대사량을 높입니다.

🔥 핵심 전략 2:
...

사용 토큰: 856

--------------------------------------------------------------------------------
📅 Prompt 2: 주간 계획 세부사항
...
```

**결과 파일:**
- `output/llm_result_SAMPLE_USER.json`
- `output/llm_result_홈트_마른비만.json`
- 등등

---

## 💰 예상 비용

### GPT-4o-mini 가격 (2026년 기준)

- Input: $0.15 / 1M tokens
- Output: $0.60 / 1M tokens

### 예상 사용량 (1회 테스트)

| 항목 | 토큰 | 비용 |
|------|------|------|
| Prompt 1 (요약) | ~1,500 | ~$0.001 |
| Prompt 2 (세부) | ~2,500 | ~$0.002 |
| **합계** | **~4,000** | **~$0.003** |

**전체 프로필 테스트 (5개):** 약 $0.015 (20원)

---

## 🔍 테스트 시나리오

### 시나리오 1: 홈트 + 마른비만형

```python
profile = {
    "body_type1": "마른비만형",
    "body_type2": "상체비만형",
    "workout_place": "홈트",
    "preferred_sport": None
}
```

**예상 전략:**
- 근력운동 메인, 유산소 보조
- 맨몸 운동 (푸쉬업, 스쿼트, 플랭크)
- 상체 지방 감소 + 하체 근력 강화

### 시나리오 2: 헬스장 + 표준형

```python
profile = {
    "body_type1": "표준형",
    "body_type2": "표준형",
    "workout_place": "헬스장",
    "preferred_sport": None
}
```

**예상 전략:**
- 균형잡힌 상하체 운동
- 머신 활용 (벤치프레스, 스쿼트, 랫풀다운)
- 체지방 감소 + 근육 증가

### 시나리오 3: 스포츠 (축구)

```python
profile = {
    "body_type1": "근육형",
    "body_type2": "상체발달형",
    "workout_place": "스포츠",
    "preferred_sport": "축구"
}
```

**예상 전략:**
- 축구 주 2-3회 + 하체 보완 운동
- 하체 강화 (스쿼트, 런지)
- 발목/무릎 부상 주의

---

## 🐛 트러블슈팅

### 1. API 키 오류

```
❌ OPENAI_API_KEY 환경변수가 설정되지 않았습니다.
```

**해결:**
```bash
export OPENAI_API_KEY='sk-...'
```

### 2. 모듈 임포트 오류

```
ModuleNotFoundError: No module named 'openai'
```

**해결:**
```bash
pip install openai
```

### 3. Pydantic 검증 오류

```
ValidationError: 1 validation error for GoalPlanInput
```

**해결:**
- `schemas.py`의 필드가 `SAMPLE_GOAL`과 일치하는지 확인
- 필수 필드를 `Optional`로 변경

### 4. 응답이 너무 길거나 짧음

**해결:**
`test_llm_call.py`에서 `max_tokens` 조정:

```python
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[...],
    temperature=0.7,
    max_tokens=2000  # 이 값 조정
)
```

---

## 📝 체크리스트

테스트 실행 전:

- [ ] OpenAI API 키 설정됨
- [ ] `sample_data.py`에 테스트할 프로필 추가됨
- [ ] `SAMPLE_GOAL` 데이터 확인
- [ ] 인터넷 연결 확인

테스트 실행 후:

- [ ] 프롬프트에 전략 텍스트 포함 확인
- [ ] LLM 응답이 전략을 반영하는지 확인
- [ ] 결과 파일 저장 확인 (`output/`)
- [ ] 토큰 사용량 확인

---

## 🚀 다음 단계

1. **프롬프트 최적화**
   - LLM 응답이 전략을 잘 반영하는지 확인
   - 필요시 system prompt 수정

2. **추가 프로필 테스트**
   - 다양한 체형/장소 조합 테스트
   - 엣지 케이스 확인

3. **실제 파이프라인 통합**
   - `weekly_plan_graph_rag.py` 업데이트
   - DB 연동 준비
   - API 엔드포인트 통합

---

**작성일:** 2026-02-03
