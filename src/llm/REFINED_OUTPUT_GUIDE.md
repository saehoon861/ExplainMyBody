# 2차 LLM 정제 출력 (Refined Output) 가이드

## 개요

기존 LLM 출력 결과물(전문적이고 상세한 분석)을 **2차 LLM 호출**을 통해 일반 사용자가 이해하기 쉽게 요약하고 정제하는 기능입니다.

## 적용 파이프라인

### 1. InBody 분석 파이프라인
- **위치**: `pipeline_inbody_analysis/`
- **파일**: `analyzer.py`, `main.py`
- **DB 테이블**: `inbody_analysis_reports`
- **DB 컬럼**: `refined_output` (Text, nullable)

### 2. InBody 멀티 분석 파이프라인
- **위치**: `pipeline_inbody_analysis_multi/`
- **파일**: `analyzer.py`, `main.py`
- **DB 테이블**: `inbody_analysis_reports`
- **DB 컬럼**: `refined_output` (Text, nullable)

### 3. 주간 계획 파이프라인
- **위치**: `pipeline_weekly_plan/`
- **파일**: `planner.py`, `main.py`
- **DB 테이블**: `weekly_plans`
- **DB 컬럼**: `refined_output` (Text, nullable)

## 데이터 흐름

### InBody 분석 파이프라인

```
1. 측정 데이터 입력
    ↓
2. health_records 테이블에 저장
    ↓
3. 1차 LLM 호출 (전문 분석)
    ↓
4. inbody_analysis_reports 테이블에 저장
    - llm_output: 전문 분석 리포트
    ↓
5. 2차 LLM 호출 (사용자 친화적 요약)
    - System Prompt: 의료 리포트 편집자 역할
    - User Prompt: 1차 분석 결과
    ↓
6. refined_output 컬럼 업데이트
    - refined_output: 사용자 친화적 요약
    ↓
7. TXT 파일 저장
    - 1차 분석 + 2차 요약 모두 포함
```

### 주간 계획 파이프라인

```
1. 사용자 목표 및 선호도 입력
    ↓
2. RAG 검색 (과거 유사 케이스)
    ↓
3. 1차 LLM 호출 (주간 계획 생성)
    ↓
4. weekly_plans 테이블에 저장
    - plan_data (JSONB): 전체 계획 데이터
    - llm_raw_output: LLM 원본 출력
    ↓
5. 2차 LLM 호출 (사용자 친화적 요약)
    - System Prompt: 헬스케어 플래너 역할
    - User Prompt: 1차 계획 결과
    ↓
6. refined_output 컬럼 업데이트
    - refined_output: 사용자 친화적 요약
    ↓
7. TXT 파일 저장
    - 1차 계획 + 2차 요약 모두 포함
```

## DB 스키마 변경

### inbody_analysis_reports 테이블

```sql
ALTER TABLE inbody_analysis_reports
ADD COLUMN refined_output TEXT;
```

**컬럼 설명**:
- `llm_output` (Text, NOT NULL): 1차 LLM 전문 분석 리포트
- `refined_output` (Text, NULL): 2차 LLM 사용자 친화적 요약

### weekly_plans 테이블

```sql
ALTER TABLE weekly_plans
ADD COLUMN refined_output TEXT;
```

**컬럼 설명**:
- `plan_data` (JSONB, NOT NULL): 전체 계획 데이터 (구조화)
- `refined_output` (Text, NULL): 2차 LLM 사용자 친화적 요약

## 2차 LLM 프롬프트

### InBody 분석용 정제 프롬프트

```
System Prompt:
당신은 의료 리포트 편집자입니다.
주어진 인바디 분석 리포트를 일반 사용자가 이해하기 쉽게 요약하고 정제해주세요.

목표:
- 전문 용어를 쉬운 말로 풀어쓰기
- 핵심 내용만 간결하게 요약
- 실천 가능한 조언 중심으로 재구성
- 긍정적이고 동기부여가 되는 톤

출력 형식:
### 📊 현재 상태 한눈에 보기
(체형, 체지방, 근육량 핵심 3줄 요약)

### 💪 개선이 필요한 부분
(우선순위 1-3가지, 각 1-2문장)

### 🎯 실천 가이드
(구체적이고 실천 가능한 방향 3-5가지)

### ✅ 현재 잘하고 있는 부분
(긍정적 피드백 2-3가지)

User Prompt:
다음 인바디 분석 리포트를 사용자 친화적으로 요약해주세요:

{1차 LLM 분석 결과}
```

### 주간 계획용 정제 프롬프트

```
System Prompt:
당신은 헬스케어 플래너입니다.
주어진 주간 운동 및 식단 계획을 일반 사용자가 실천하기 쉽게 요약하고 정제해주세요.

목표:
- 핵심 목표와 우선순위를 명확히
- 요일별 계획을 간결하게 정리
- 실천 팁과 주의사항 강조
- 동기부여가 되는 톤

출력 형식:
### 🎯 이번 주 목표
(이번 주 달성할 핵심 목표 2-3줄)

### 📅 주간 계획 요약
**월-수**: (운동 + 식단 핵심만)
**목-금**: (운동 + 식단 핵심만)
**주말**: (운동 + 식단 핵심만)

### 💡 실천 팁
(성공을 위한 구체적 팁 3-5가지)

### ⚠️ 주의사항
(주의할 점 2-3가지)

### 💪 응원 메시지
(긍정적 마무리 1-2문장)

User Prompt:
다음 주간 계획을 사용자 친화적으로 요약해주세요:

{1차 LLM 계획 결과}
```

## Database 메서드

### 추가된 메서드

#### `update_analysis_refined_output(report_id, refined_output)`
- **위치**: `shared/database.py`
- **목적**: InBody 분석 리포트에 2차 정제 출력 업데이트
- **파라미터**:
  - `report_id` (int): 분석 리포트 ID
  - `refined_output` (str): 정제된 요약 텍스트
- **반환**: `bool` (성공 여부)

#### `update_weekly_plan_refined_output(plan_id, refined_output)`
- **위치**: `shared/database.py`
- **목적**: 주간 계획에 2차 정제 출력 업데이트
- **파라미터**:
  - `plan_id` (int): 계획 ID
  - `refined_output` (str): 정제된 요약 텍스트
- **반환**: `bool` (성공 여부)

## Response 모델 변경

### InBodyAnalysisResponse

```python
class InBodyAnalysisResponse(BaseModel):
    success: bool
    record_id: Optional[int] = None
    analysis_id: Optional[int] = None
    analysis_text: Optional[str] = None
    refined_text: Optional[str] = None  # ← 추가
    error: Optional[str] = None
```

### WeeklyPlanResponse

```python
class WeeklyPlanResponse(BaseModel):
    success: bool
    plan_id: Optional[int] = None
    weekly_plan: Optional[WeeklyPlan] = None
    refined_text: Optional[str] = None  # ← 추가
    error: Optional[str] = None
```

## TXT 파일 출력 형식

### InBody 분석 결과 (예시)

```
============================================================
InBody 분석 결과
============================================================

Record ID: 123
Analysis ID: 456

------------------------------------------------------------

[콘솔 출력 메시지]

============================================================
📋 LLM 분석 리포트
============================================================

[1차 LLM 전문 분석 내용 - 상세하고 전문적]

============================================================
📱 사용자 친화적 요약
============================================================

### 📊 현재 상태 한눈에 보기
[핵심 3줄 요약]

### 💪 개선이 필요한 부분
[우선순위 개선 과제]

### 🎯 실천 가이드
[실천 가능한 조언]

### ✅ 현재 잘하고 있는 부분
[긍정적 피드백]
```

### 주간 계획 결과 (예시)

```
================================================================================
주간 운동/식단 계획
================================================================================

Plan ID: 789
주차: 1
기간: 2024-01-01 ~ 2024-01-07

--------------------------------------------------------------------------------

[1차 LLM 주간 계획 내용 - 상세한 요일별 계획]

================================================================================
📱 사용자 친화적 요약
================================================================================

### 🎯 이번 주 목표
[핵심 목표 2-3줄]

### 📅 주간 계획 요약
**월-수**: [운동 + 식단 핵심]
**목-금**: [운동 + 식단 핵심]
**주말**: [운동 + 식단 핵심]

### 💡 실천 팁
[구체적 팁 3-5가지]

### ⚠️ 주의사항
[주의할 점 2-3가지]

### 💪 응원 메시지
[긍정적 마무리]
```

## 실행 예시

### InBody 분석

```bash
python pipeline_inbody_analysis/main.py \
  --user-id 1 \
  --measurements-file pipeline_inbody_analysis/sample_inbody_data.json \
  --model gpt-4o-mini \
  --output-file outputs/inbody_result.txt
```

**출력**:
```
============================================================
InBody 분석 시작 (User ID: 1)
============================================================

📊 1단계: 체형 정보 확인...
  ✓ Body Type 1: 근육부족형
  ✓ Body Type 2: 복부비만형

💾 2단계: 측정 데이터 저장...
  ✓ Record ID: 123

🤖 3단계: LLM 분석 생성...
  - LLM 호출 중...
  ✓ 분석 완료 (2345 글자)

💾 4단계: 분석 결과 저장...
  ✓ Analysis ID: 456

✨ 5단계: 사용자 친화적 요약 생성...
  - 2차 LLM 호출 중...
  ✓ 요약 완료 (789 글자)

💾 6단계: 정제된 요약 저장...
  ✓ Refined output 업데이트 완료

============================================================
✨ InBody 분석 완료!
============================================================
```

### 주간 계획

```bash
python pipeline_weekly_plan/main.py \
  --user-id 1 \
  --goals-file pipeline_weekly_plan/sample_user_goals.json \
  --preferences-file pipeline_weekly_plan/sample_user_preferences.json \
  --model gpt-4o-mini \
  --output-file outputs/weekly_plan.txt
```

**출력**:
```
============================================================
주간 계획 생성 시작
============================================================

...

💾 주간 계획 저장...
  ✓ DB 저장 완료 (Plan ID: 789)

✨ 사용자 친화적 요약 생성...
  - 2차 LLM 호출 중...
  ✓ 요약 완료 (654 글자)
  - 정제된 요약 저장 중...
  ✓ Refined output 업데이트 완료
```

## 비용 및 성능

### LLM 호출 횟수

| 파이프라인 | 기존 | 변경 후 |
|-----------|------|---------|
| InBody 분석 (단일) | 1회 | 2회 (+100%) |
| InBody 분석 (멀티) | 3회 | 4회 (+33%) |
| 주간 계획 | 1회 | 2회 (+100%) |

### 예상 비용 증가

- **GPT-4o-mini** 사용 시: 약 2배 (단일), 1.33배 (멀티)
- **Claude Sonnet** 사용 시: 약 2배 (단일), 1.33배 (멀티)

### 처리 시간 증가

- **평균 +5-10초** (2차 LLM 호출 및 DB 업데이트)

## 임베딩 생성

**중요**: `refined_output`은 **임베딩을 생성하지 않습니다.**

- **임베딩 대상**: `llm_output` (1차 전문 분석)만 사용
- **이유**:
  - RAG 검색은 전문적이고 상세한 분석이 더 유용
  - 요약본은 사용자 가독성 목적이므로 검색에 부적합
  - 임베딩 비용 절감

## 장점

### 사용자 경험
- ✅ 전문 분석 + 쉬운 요약 **모두 제공**
- ✅ 일반 사용자도 즉시 이해 가능
- ✅ 실천 가능한 조언 중심
- ✅ 동기부여 효과

### 기술적 장점
- ✅ 기존 데이터 보존 (`llm_output`은 그대로)
- ✅ 독립적인 컬럼 (`refined_output` nullable)
- ✅ 임베딩은 전문 분석으로 (품질 유지)
- ✅ TXT 파일에 모두 포함 (비교 가능)

### 운영 장점
- ✅ 2차 프롬프트만 수정하면 요약 스타일 변경 가능
- ✅ 필요 시 2차 호출 비활성화 가능 (DB 업데이트만 스킵)
- ✅ A/B 테스트 가능 (1차 vs 2차)

## 제한사항

### 비용
- ❌ LLM 호출 비용 2배 증가 (단일 파이프라인)
- ❌ 처리 시간 증가

### 정확성
- ⚠️ 2차 요약이 1차 분석의 일부 정보 누락 가능
- ⚠️ 과도한 단순화로 전문성 손실 가능

### 해결 방안
- **비용**: 2차 LLM에 더 저렴한 모델 사용 (haiku 등)
- **정확성**: 프롬프트 개선 ("핵심 정보 유지" 강조)

## 향후 개선 방향

### 1. 모델 분리
```python
# 1차: 전문 분석 (고품질 모델)
analysis_text = claude_client.generate_chat(...)

# 2차: 요약 (저렴한 모델)
refined_text = haiku_client.generate_chat(...)
```

### 2. 캐싱
- 동일한 분석 결과는 2차 요약 캐싱
- DB에서 유사 케이스 찾아 재사용

### 3. A/B 테스트
- 사용자 그룹별로 1차만 vs 1차+2차 제공
- 만족도 비교

### 4. 다국어 지원
- 2차 프롬프트에 언어 파라미터 추가
- 영어, 일본어 등 다국어 요약

## 참고 사항

1. **DB 마이그레이션**: 기존 DB에 `refined_output` 컬럼 추가 필요
2. **하위 호환성**: `refined_output`은 nullable이므로 기존 레코드도 정상 작동
3. **임베딩**: 변경 없음 (기존 `llm_output` 사용)
4. **TXT 파일**: 1차 + 2차 모두 포함되므로 파일 크기 증가
