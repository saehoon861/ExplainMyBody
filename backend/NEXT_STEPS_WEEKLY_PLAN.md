# WeeklyPlan Router 추가 후 가이드

## ✅ 완료된 작업

1. **WeeklyPlan Router 생성** (`backend/routers/llm/weekly_plans.py`)
   - 6개 CRUD 엔드포인트 구현
   - Repository 직접 호출 (Service 레이어 없음)

2. **Router 등록**
   - `routers/llm/__init__.py`에 export 추가
   - `main.py`에 `/api/weekly-plans` 경로로 등록

3. **Import 검증**
   - 모든 imports 성공 확인

---

## 📋 생성된 엔드포인트

| Method | Path | 설명 |
|--------|------|------|
| POST | `/api/weekly-plans/` | 주간 계획 생성 |
| GET | `/api/weekly-plans/{plan_id}` | 특정 계획 조회 |
| GET | `/api/weekly-plans/user/{user_id}` | 사용자별 목록 조회 |
| GET | `/api/weekly-plans/user/{user_id}/week/{week_number}` | 특정 주차 조회 |
| PATCH | `/api/weekly-plans/{plan_id}` | 계획 수정 |
| DELETE | `/api/weekly-plans/{plan_id}` | 계획 삭제 |

---

## ⚠️ 주의사항 및 다음 단계

### 1. 현재 Router의 제한사항

**현재 상태**:
```python
# Router에서 Repository 직접 호출
new_plan = WeeklyPlanRepository.create(db, user_id, plan_data)
```

**문제점**:
- ❌ LLM 호출 없음 (주간 계획이 수동으로만 생성됨)
- ❌ 분석 리포트와 연계 없음
- ❌ 사용자 목표와 연계 없음

**해결 방법** (팀장님께 전달):
Router와 Repository 사이에 Service 레이어를 추가해야 합니다.

---

### 2. Service 레이어 추가 시 구조

```python
# 현재 (Router → Repository)
@router.post("/")
def create_weekly_plan(user_id, plan_data, db):
    new_plan = WeeklyPlanRepository.create(db, user_id, plan_data)  # ❌ 직접 호출
    return new_plan

# 변경 후 (Router → Service → Repository)
@router.post("/")
async def create_weekly_plan(user_id, plan_data, db):
    new_plan = await WeeklyPlanService.generate_plan(  # ✅ Service 호출
        db, user_id, plan_data
    )
    return new_plan
```

---

### 3. 팀장님께 전달할 내용

#### Service 레이어 역할

**WeeklyPlanService** 생성 필요:
```python
# backend/services/llm/weekly_plan_service.py

class WeeklyPlanService:
    async def generate_plan(
        db: Session,
        user_id: int,
        record_id: int,
        user_goal: dict
    ) -> WeeklyPlanResponse:
        """
        주간 계획 생성 프로세스:
        
        1. 데이터 조회
           - HealthRecord 조회
           - AnalysisReport 조회 (LLM1 결과)
           - UserDetail 조회 (목표, 선호도)
        
        2. LLM 호출
           - src/llm/pipeline_weekly_plan/planner.py 로직 활용
           - 프롬프트 생성 및 LLM API 호출
        
        3. 결과 저장
           - WeeklyPlanRepository.create() 호출
        """
```

#### 통합 필요 파일
- `src/llm/pipeline_weekly_plan/planner.py` → Service로 이동
- `src/llm/shared/llm_client.py` → Service에서 사용

---

### 4. 프론트엔드 연동 주의사항

#### 현재 API 호출 방법
```javascript
// 주간 계획 생성 (현재는 수동)
POST /api/weekly-plans/
{
  "week_number": 1,
  "start_date": "2024-01-01",
  "end_date": "2024-01-07",
  "plan_data": {
    "meals": [...],
    "exercises": [...]
  },
  "model_version": "manual"
}
```

#### Service 추가 후 변경될 API
```javascript
// LLM이 자동 생성
POST /api/weekly-plans/generate
{
  "record_id": 123,          // 건강 기록 ID
  "user_goal_type": "체중감량",
  "user_goal_description": "3개월 내 5kg 감량"
}

// 응답
{
  "id": 1,
  "week_number": 1,
  "plan_data": {
    "meals": [...],          // LLM이 생성한 식단
    "exercises": [...],      // LLM이 생성한 운동
    "tips": [...]            // LLM이 생성한 팁
  },
  "model_version": "gpt-4"
}
```

**프론트엔드 수정 필요**:
- 새 엔드포인트 추가 또는 기존 엔드포인트 변경
- LLM 생성 진행 상태 표시 (로딩 인디케이터)

---

### 5. 변수명/메서드명 일관성 체크리스트

#### ✅ 모두 일치 확인됨

| 레이어 | 이름 | 상태 |
|--------|------|------|
| **Model** | `WeeklyPlan` | ✅ |
| **Table** | `weekly_plans` | ✅ |
| **Repository** | `WeeklyPlanRepository` | ✅ |
| **Schema** | `WeeklyPlanCreate/Response/Update` | ✅ |
| **Router** | `weekly_plans_router` | ✅ |
| **Endpoint** | `/api/weekly-plans/` | ✅ |

**일관된 명명 규칙**:
- Model/Repository/Schema: PascalCase
- Table/File: snake_case
- Router variable: snake_case + _router suffix
- Endpoint: kebab-case

---

### 6. 즉시 확인해야 할 사항

#### DB 마이그레이션 실행 확인
```bash
# 아직 실행하지 않았다면
cd /home/user/ExplainMyBody/backend
psql -U postgres -d explainmybody -h localhost -f migrations/002_add_pgvector_and_embeddings.sql
```

**확인 방법**:
```sql
-- PostgreSQL에서 확인
\dt weekly_plans
-- 테이블이 존재하면 OK
```

#### 서버 재시작
```bash
# 서버가 실행 중이면 재시작 (변경사항 반영)
# Ctrl+C로 중단 후
uv run uvicorn main:app --reload
```

#### API 문서 확인
서버 시작 후 http://localhost:8000/docs 접속
- "Weekly Plans" 섹션 확인
- 6개 엔드포인트 모두 표시되는지 확인

---

### 7. 테스트 방법

#### 수동 테스트 (Swagger UI)
1. http://localhost:8000/docs 접속
2. "Weekly Plans" > "POST /api/weekly-plans/" 클릭
3. Try it out 클릭
4. Request body 입력:
```json
{
  "week_number": 1,
  "start_date": "2024-01-01",
  "end_date": "2024-01-07",
  "plan_data": {
    "test": "data"
  },
  "model_version": "mock"
}
```
5. Execute 클릭
6. 201 응답 확인

#### curl로 테스트
```bash
curl -X POST "http://localhost:8000/api/weekly-plans/?user_id=1" \
  -H "Content-Type: application/json" \
  -d '{
    "week_number": 1,
    "start_date": "2024-01-01",
    "end_date": "2024-01-07",
    "plan_data": {"test": "data"},
    "model_version": "mock"
  }'
```

---

### 8. 다음 작업 순서 (팀장님과 협의)

1. **Service 레이어 설계 회의**
   - LLM1/LLM2 통합 방식 논의
   - API 설계 (generate vs create)
   - 에러 핸들링 전략

2. **Service 레이어 구현**
   - `services/llm/weekly_plan_service.py` 생성
   - `src/llm/pipeline_weekly_plan/` 로직 이동
   - LLM client 통합

3. **Router 수정**
   - Service 호출로 변경
   - async/await 적용

4. **프론트엔드 연동**
   - API 스펙 공유
   - 테스트

---

## 📝 요약

### 현재 상태
- ✅ Router 추가 완료 (CRUD만 가능)
- ✅ Repository 연결 완료
- ✅ DB 스키마 준비 완료

### 부족한 부분
- ❌ LLM 연동 (Service 레이어 필요)
- ❌ 자동 계획 생성 (Service 레이어 필요)

### 다음 단계
1. 팀장님과 Service 레이어 설계 논의
2. `src/llm/` 코드를 Service로 통합
3. Router를 Service 호출로 변경
4. 프론트엔드와 API 스펙 조율
