# DB 데이터 확인 가이드

연결 정보: `localhost:5433`, DB `explainmybody`, 유저 `sgkim`

---

## Docker에서 접속

postgres가 docker 컨테이너로 돌리고 있으면 아래 순서대로 실행합니다.

**1단계: 컨테이너 이름 확인**

```bash
docker ps
```

출력에서 `postgres` 이미지를 사용하는 컨테이너의 `NAMES` 열 값을 메모합니다. 아래 2단계에서 `<컨테이너명>` 자리에 넣습니다.

**2단계: 컨테이너 안에서 psql 실행**

```bash
docker exec -it <컨테이너명> psql -U sgkim -d explainmybody
```

접속 후 아래 "테이블별 확인 쿼리" 섹션의 SQL을 그대로 붙여넣어 실행하면 됩니다.

**한 줄로 쿼리 실행하는 경우** (psql 인터렉티브 모드 없이):

```bash
docker exec <컨테이너명> psql -U sgkim -d explainmybody -c "SELECT id, username, email FROM users;"
```

`-c` 뒤의 SQL만 바꾸면 아래 모든 쿼리를 같은 방식으로 실행할 수 있습니다.

---

## psql로 직접 접속 (컨테이너 밖에서)

```bash
PGPASSWORD=1234 psql -h localhost -p 5433 -U sgkim -d explainmybody
```

---

## 테이블별 확인 쿼리

순서대로 실행하면 아이디 생성 → 분석 리포트까지 어디까지 저장되었는지 확인됩니다.

### 1. 사용자 생성 확인

```sql
SELECT id, username, email, created_at FROM users;
```

### 2. 사용자 목표/상세정보 확인

```sql
SELECT id, user_id, goal_type, goal_description, is_active, started_at FROM user_details;
```

### 3. 건강 기록 (InBody 측정 데이터) 확인

```sql
-- 기본 정보
SELECT id, user_id, source, measured_at FROM health_records;

-- measurements JSONB 내용 확인
SELECT id, measurements FROM health_records;
```

### 4. 분석 리포트 확인 (LLM 출력)

```sql
-- 기본 정보 (embedding 제외)
SELECT id, user_id, record_id, model_version, analysis_type, generated_at FROM inbody_analysis_reports;

-- LLM 출력 텍스트
SELECT id, llm_output FROM inbody_analysis_reports;

-- 임베딩 저장 여부 (벡터 값 자체는 길어서 길이만 확인)
SELECT id, array_length(embedding_1536::float[], 1) AS dim_1536, array_length(embedding_1024::float[], 1) AS dim_1024 FROM inbody_analysis_reports;
```

### 5. 주간 계획 확인

```sql
SELECT id, user_id, week_number, start_date, end_date, model_version, created_at FROM weekly_plans;

-- plan_data JSONB 내용
SELECT id, plan_data FROM weekly_plans;
```

---

## 전체를 한 번에 확인하는 경우

```sql
-- 사용자 기준 전체 연결 상황 한눈에 보기
SELECT
  u.id          AS user_id,
  u.username,
  ud.goal_type,
  ud.is_active  AS goal_active,
  hr.id         AS health_record_id,
  hr.source,
  hr.measured_at,
  iar.id        AS analysis_report_id,
  iar.model_version,
  iar.analysis_type,
  iar.generated_at,
  wp.id         AS weekly_plan_id,
  wp.week_number
FROM users u
LEFT JOIN user_details ud       ON u.id = ud.user_id
LEFT JOIN health_records hr     ON u.id = hr.user_id
LEFT JOIN inbody_analysis_reports iar ON hr.id = iar.record_id
LEFT JOIN weekly_plans wp       ON u.id = wp.user_id;
```

---

## pgAdmin으로 볼 경우

테이블명과 컬럼 이름은 위와 동일합니다. `measurements`와 `plan_data`는 JSONB 타입이므로 pgAdmin에서 클릭하면 JSON 구조로 펼쳐집니다. `embedding_1536`은 벡터 타입이어서 원본 값 확인보다는 위의 `array_length` 쿼리로 저장 여부만 확인하는 것이 좋습니다.
