# 사용자 프로필 기반 프롬프트 통합 가이드

## 📋 개요

`weekly_plan_system.py`의 룰 기반 분기 로직을 `prompt_generator_rag.py`에 통합하여, 사용자의 체형/운동 장소/스포츠 선호에 따라 맞춤형 전략을 프롬프트에 포함합니다.

---

## 🏗 구조

### 1. 파일 구성

```
src/llm/llm_prompt_test_sk/
├── weekly_plan_system.py          # 독립 시스템 (이 파이프라인과 별개)
├── user_profile_rules.py          # 룰 정의 (BODY_TYPE1/2, WORKOUT_PLACE, SPORT) (NEW)
├── user_profile_strategy.py       # 전략 텍스트 생성 유틸리티 (NEW)
├── sample_data.py                  # 샘플 데이터 (workout_place, preferred_sport 추가)
├── prompt_generator_rag.py        # 프롬프트 생성 (user_profile 파라미터 추가)
├── test_user_profile_prompt.py    # 테스트 스크립트 (NEW)
└── USER_PROFILE_INTEGRATION.md    # 이 문서 (NEW)
```

**중요:** `weekly_plan_system.py`는 이 파이프라인과 독립적으로 운영됩니다. 룰은 `user_profile_rules.py`에서 관리합니다.

---

## 🔧 주요 변경사항

### 1. sample_data.py

**추가된 필드:**
```python
SAMPLE_USER = {
    ...
    "workout_place": "홈트",     # "헬스장", "홈트", "아웃도어", "스포츠"
    "preferred_sport": None      # "축구", "농구", "테니스", ... (스포츠일 때만)
}

# 다양한 프로필 샘플
SAMPLE_PROFILES = {
    "홈트_마른비만": {...},
    "헬스장_표준": {...},
    "스포츠_축구": {...},
    "아웃도어_비만": {...}
}
```

### 2. user_profile_strategy.py (NEW)

**핵심 함수:**
```python
def build_strategy_text_from_dict(user_data: Dict[str, Any]) -> str:
    """
    딕셔너리 형태의 사용자 데이터 → 전략 텍스트 생성

    Input:
        {
            "body_type1": "마른비만형",
            "body_type2": "상체비만형",
            "workout_place": "홈트",
            "preferred_sport": None
        }

    Output:
        [전체 체형 전략]
        - 목표: 체지방 줄이면서 근육 늘리기 동시에
        - 식단: 단백질 많이, 밥은 현미/고구마 같은 좋은 탄수화물로
        ...
    """
```

**사용 예시:**
```python
from sample_data import SAMPLE_USER
from user_profile_strategy import build_strategy_text_from_dict

strategy = build_strategy_text_from_dict(SAMPLE_USER)
print(strategy)
```

### 3. prompt_generator_rag.py

**변경된 함수 시그니처:**
```python
# BEFORE
def create_weekly_plan_summary_prompt_with_rag(
    goal_input: GoalPlanInput,
    measurements: InBodyMeasurements,
    rag_context: str = ""
) -> Tuple[str, str]:

# AFTER
def create_weekly_plan_summary_prompt_with_rag(
    goal_input: GoalPlanInput,
    measurements: InBodyMeasurements,
    rag_context: str = "",
    user_profile: Optional[Dict[str, Any]] = None  # 추가!
) -> Tuple[str, str]:
```

**동작 방식:**
```python
# user_profile이 제공되면 전략 텍스트 자동 생성
if user_profile:
    strategy_text = build_strategy_text_from_dict(user_profile)
    # 프롬프트에 전략 텍스트 삽입
else:
    # 기존 방식대로 동작 (하위 호환)
```

---

## 🧪 테스트

### 1. 전략 텍스트 생성 테스트

```bash
cd src/llm/llm_prompt_test_sk
python user_profile_strategy.py
```

**결과:**
```
📋 SAMPLE_USER 전략 텍스트
============================================================

[전체 체형 전략]
- 목표: 체지방 줄이면서 근육 늘리기 동시에
- 식단: 단백질 많이, 밥은 현미/고구마 같은 좋은 탄수화물로
- 운동: 근력운동이 메인, 유산소는 보조로만
...
```

### 2. 프롬프트 생성 테스트

```bash
python test_user_profile_prompt.py
```

**결과:**
```
🧪 사용자 프로필 기반 프롬프트 생성 테스트
================================================================================

📋 프로필: 홈트_마른비만
체형: 마른비만형 / 상체비만형
장소: 홈트

🎯 Prompt 1: 주간 목표 요약
[User Prompt - 전략 섹션만 발췌]

[전체 체형 전략]
- 목표: 체지방 줄이면서 근육 늘리기 동시에
- 식단: 단백질 많이, 밥은 현미/고구마 같은 좋은 탄수화물로
...
```

---

## 🔌 실제 사용 예시

### 케이스 1: 샘플 데이터로 테스트

```python
from sample_data import SAMPLE_USER, SAMPLE_MEASUREMENTS, SAMPLE_GOAL
from schemas_inbody import InBodyData
from schemas import GoalPlanInput
from prompt_generator_rag import create_weekly_plan_summary_prompt_with_rag

# 데이터 변환
measurements = InBodyData(**SAMPLE_MEASUREMENTS)
goal_input = GoalPlanInput(**SAMPLE_GOAL)

# 프롬프트 생성 (프로필 포함)
system_prompt, user_prompt = create_weekly_plan_summary_prompt_with_rag(
    goal_input=goal_input,
    measurements=measurements,
    rag_context="",
    user_profile=SAMPLE_USER  # 전략 자동 생성
)

# LLM 호출
# result = llm_client.generate(system_prompt, user_prompt)
```

### 케이스 2: 다양한 프로필 테스트

```python
from sample_data import SAMPLE_PROFILES

# 헬스장 이용자
profile_gym = SAMPLE_PROFILES["헬스장_표준"]
system_prompt, user_prompt = create_weekly_plan_summary_prompt_with_rag(
    goal_input=goal_input,
    measurements=measurements,
    user_profile=profile_gym
)

# 스포츠 (축구) 이용자
profile_soccer = SAMPLE_PROFILES["스포츠_축구"]
system_prompt, user_prompt = create_weekly_plan_summary_prompt_with_rag(
    goal_input=goal_input,
    measurements=measurements,
    user_profile=profile_soccer
)
```

### 케이스 3: DB 연동 시 (향후)

```python
# DB에서 사용자 프로필 가져오기
user_profile = {
    "body_type1": user.body_type1,           # DB에서
    "body_type2": user.body_type2,           # DB에서
    "workout_place": user.workout_place,      # DB에서
    "preferred_sport": user.preferred_sport   # DB에서
}

# 프롬프트 생성
system_prompt, user_prompt = create_weekly_plan_summary_prompt_with_rag(
    goal_input=goal_input,
    measurements=measurements,
    user_profile=user_profile  # DB 데이터 사용
)
```

---

## 📊 분기 처리 구조

### 입력 → 룰 매칭 → 전략 생성

```
user_profile = {
    "body_type1": "마른비만형",
    "body_type2": "상체비만형",
    "workout_place": "홈트",
    "preferred_sport": None
}
    ↓
BODY_TYPE1_RULES["마른비만형"]  →  목표, 식단, 운동, 주의사항
BODY_TYPE2_RULES["상체비만형"]  →  포커스, 루틴 조정
WORKOUT_PLACE_RULES["홈트"]     →  환경, 스타일, 제약사항
    ↓
[전체 체형 전략]
- 목표: 체지방 줄이면서 근육 늘리기 동시에
- 식단: 단백질 많이, 밥은 현미/고구마 같은 좋은 탄수화물로
- 운동: 근력운동이 메인, 유산소는 보조로만
- ⚠️ 주의: 유산소만 하면 더 마르기만 해요. 근력이 우선이에요
- 💬 코치: 체중계 숫자보다 거울을 믿으세요. 근육이 붙으면 달라져요.

[상하체 밸런스]
- 포커스: 상체 체지방 감소 + 하체 근력 강화
- 루틴 조정: 전신 유산소로 상체 빼고, 하체 근력 집중
- 💬 코치: 하체 키우면 상체가 상대적으로 날씬해 보여요.

[운동 장소: 홈트]
- 환경: 장비가 제한적이라 맨몸 루틴이 핵심입니다.
- 스타일: 스쿼트/푸쉬업/런지/플랭크 위주로 구성하세요.
- 주의: 강도는 세트 수로 올리면 됩니다.
- 💬 코치: 집에서도 충분히 됩니다. 꾸준함이 장비를 이겨요.
    ↓
프롬프트에 삽입됨
```

---

## ✅ 하위 호환성

**프로필 없이도 동작:**
```python
# user_profile=None (기본값)
system_prompt, user_prompt = create_weekly_plan_summary_prompt_with_rag(
    goal_input=goal_input,
    measurements=measurements,
    rag_context=""
    # user_profile 생략 → 전략 텍스트 없음 (기존 방식)
)
```

---

## 🚀 다음 단계

### 1. 프롬프트 검증 완료 후
- 실제 LLM 호출 (OpenAI / Ollama)
- 응답 품질 확인

### 2. DB 연동 준비
```python
# 추후 Pydantic 모델로 검증
from pydantic import BaseModel

class UserProfile(BaseModel):
    body_type1: str
    body_type2: str
    workout_place: str
    preferred_sport: Optional[str] = None

# SQLAlchemy로 DB에서 가져오기
user_profile_dict = UserProfile.from_orm(user).dict()
```

### 3. API 엔드포인트 통합
```python
@router.post("/weekly-plan")
async def create_weekly_plan(
    user_id: int,
    goal_data: GoalPlanInput,
    db: Session = Depends(get_db)
):
    # DB에서 user profile 가져오기
    user = db.query(User).filter(User.id == user_id).first()
    user_profile = {
        "body_type1": user.body_type1,
        "body_type2": user.body_type2,
        "workout_place": user.workout_place,
        "preferred_sport": user.preferred_sport
    }

    # 프롬프트 생성
    system_prompt, user_prompt = create_weekly_plan_summary_prompt_with_rag(
        goal_input=goal_data,
        measurements=user.latest_inbody,
        user_profile=user_profile
    )

    # LLM 호출
    result = llm_service.generate(system_prompt, user_prompt)
    return result
```

---

## 📝 체크리스트

- [x] `weekly_plan_system.py` 룰 확인
- [x] `user_profile_strategy.py` 생성
- [x] `sample_data.py`에 프로필 필드 추가
- [x] `prompt_generator_rag.py` 수정
- [x] `test_user_profile_prompt.py` 생성
- [ ] 로컬 테스트 실행
- [ ] 프롬프트 검증
- [ ] LLM 응답 품질 확인
- [ ] DB 스키마 확인 (workout_place, preferred_sport 컬럼 존재?)
- [ ] API 연동

---

**작성일:** 2026-02-03
**버전:** 1.0
