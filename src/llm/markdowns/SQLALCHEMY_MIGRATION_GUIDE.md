# SQLAlchemy 마이그레이션 가이드

## 설치

```bash
pip install sqlalchemy alembic
# 또는
uv pip install sqlalchemy alembic
```

---

## 1. 코드 비교: psycopg2 vs SQLAlchemy

### 사용자 생성

#### 현재 (psycopg2)
```python
from database import Database

db = Database()
user_id = db.create_user("홍길동", "hong@example.com")
```

#### SQLAlchemy
```python
from database_sqlalchemy import DatabaseSQLAlchemy

db = DatabaseSQLAlchemy()
user_id = db.create_user("홍길동", "hong@example.com")
```

**결과: 인터페이스 동일!** ✅

---

### 건강 기록 저장

#### 현재 (psycopg2)
```python
measurements = {
    "성별": "남자",
    "나이": 30,
    "체중": 70.0,
    # ...
}

record_id = db.save_health_record(
    user_id=1,
    measurements=measurements,
    source="inbody_ocr"
)
```

#### SQLAlchemy
```python
# 완전히 동일!
record_id = db.save_health_record(
    user_id=1,
    measurements=measurements,
    source="inbody_ocr"
)
```

**결과: 인터페이스 동일!** ✅

---

### JSONB 검색

#### 현재 (psycopg2)
```python
records = db.search_health_records_by_measurement(
    user_id=1,
    key="stage2_근육보정체형",
    value="근육형"
)
```

#### SQLAlchemy
```python
# 완전히 동일!
records = db.search_health_records_by_measurement(
    user_id=1,
    key="stage2_근육보정체형",
    value="근육형"
)
```

**결과: 인터페이스 동일!** ✅

---

## 2. SQLAlchemy만의 추가 기능

### Relationship 활용

```python
from database_sqlalchemy import DatabaseSQLAlchemy

db = DatabaseSQLAlchemy()

# ORM 방식으로 사용자와 모든 건강 기록 가져오기
with db.get_session() as session:
    user = session.get(User, 1)

    # Relationship을 통한 자동 JOIN
    print(f"사용자: {user.username}")
    print(f"건강 기록 수: {len(user.health_records)}")

    for record in user.health_records:
        print(f"  - Record {record.id}: {record.source}")
        print(f"    측정일: {record.measured_at}")
        print(f"    체형: {record.measurements.get('stage2_근육보정체형')}")
```

### 복잡한 쿼리 빌더

```python
from sqlalchemy import select, and_, or_
from db_models import HealthRecord

with db.get_session() as session:
    # 복잡한 조건 쿼리
    stmt = (
        select(HealthRecord)
        .where(
            and_(
                HealthRecord.user_id == 1,
                HealthRecord.source == "inbody_ocr",
                HealthRecord.measurements["BMI"].astext.cast(Float) > 25.0
            )
        )
        .order_by(HealthRecord.measured_at.desc())
        .limit(10)
    )

    records = session.scalars(stmt).all()
```

### Type-safe 쿼리

```python
# IDE 자동완성 지원!
with db.get_session() as session:
    user = session.get(User, 1)

    user.username  # ✅ IDE가 자동완성
    user.emial     # ❌ IDE가 오타 감지!
```

---

## 3. 기존 코드 마이그레이션

### 옵션 A: database.py 완전 교체 (권장 X)

```python
# database.py를 삭제하고 database_sqlalchemy.py를 사용
# 위험: 기존 코드 전체 영향
```

### 옵션 B: 점진적 마이그레이션 (권장 ✅)

#### 단계 1: main_workflow.py만 변경

```python
# main_workflow.py
# from database import Database
from database_sqlalchemy import DatabaseSQLAlchemy as Database

# 나머지 코드는 그대로!
db = Database(args.db_url)
```

#### 단계 2: 테스트

```bash
python main_workflow.py --username "테스트" --email "test@example.com" --profile-id 1
```

#### 단계 3: 문제없으면 다른 파일도 변경

```python
# workflow.py, run_my_inbody.py 등
from database_sqlalchemy import DatabaseSQLAlchemy as Database
```

---

## 4. Alembic으로 Migration 관리 (선택사항)

### 초기 설정

```bash
cd /home/user/projects/ExplainMyBody/llm
alembic init alembic
```

### alembic.ini 수정

```ini
# alembic.ini
sqlalchemy.url = postgresql://sgkim:1234@localhost:5433/explainmybody
```

### env.py 수정

```python
# alembic/env.py
from db_models import Base

target_metadata = Base.metadata
```

### 첫 마이그레이션 생성

```bash
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head
```

### 스키마 변경 시

```python
# db_models.py에서 모델 수정
class User(Base):
    # 새 컬럼 추가
    phone: Mapped[Optional[str]] = mapped_column(String(20))
```

```bash
# 마이그레이션 생성 및 적용
alembic revision --autogenerate -m "Add phone to users"
alembic upgrade head
```

---

## 5. 성능 비교

### psycopg2 (현재)
```python
# 10명의 사용자와 각각의 건강 기록 조회
for user_id in range(1, 11):
    user = db.get_user_by_id(user_id)
    records = db.get_user_health_records(user_id)
    # 20개의 쿼리 (N+1 문제)
```

### SQLAlchemy (최적화)
```python
# Eager loading으로 한 번에 가져오기
with db.get_session() as session:
    stmt = (
        select(User)
        .options(joinedload(User.health_records))
        .where(User.id.in_(range(1, 11)))
    )
    users = session.scalars(stmt).unique().all()
    # 2개의 쿼리 (JOIN 사용)
```

---

## 6. 장단점 정리

### psycopg2 (현재)

**장점:**
- ✅ 단순하고 직관적
- ✅ JSONB 쿼리가 간단
- ✅ PostgreSQL 특화 기능 쉽게 사용

**단점:**
- ❌ SQL 문자열 직접 작성 (오타 위험)
- ❌ IDE 자동완성 없음
- ❌ Migration 관리 수동

### SQLAlchemy

**장점:**
- ✅ 타입 안정성 + IDE 자동완성
- ✅ Relationship 자동 관리
- ✅ 복잡한 쿼리 빌더
- ✅ Alembic으로 Migration 자동화
- ✅ 다른 DB로 전환 쉬움

**단점:**
- ❌ 러닝 커브
- ❌ JSONB 쿼리가 더 복잡
- ❌ 약간의 성능 오버헤드

---

## 7. 추천 사항

### 현재 프로젝트 규모에서는?

**psycopg2 유지 권장** (현재 상태)
- 테이블 4개, 쿼리 단순
- JSONB 중심 설계
- 팀 규모 작음

### SQLAlchemy 도입이 유리한 경우

1. **팀이 확장되는 경우**
   - 여러 개발자가 작업
   - 코드 리뷰 필요

2. **복잡한 쿼리 증가**
   - JOIN이 많아짐
   - 통계 쿼리 복잡해짐

3. **Migration 관리 필요**
   - 스키마 변경 빈번
   - 버전 관리 필요

4. **다른 DB 전환 가능성**
   - PostgreSQL → MySQL 등

---

## 8. 실전 테스트

### 두 가지 모두 테스트해보기

```bash
# psycopg2 버전 테스트
python main_workflow.py --username "테스트1" --email "test1@example.com" --profile-id 1

# SQLAlchemy 버전 테스트 (main_workflow.py import만 변경)
python main_workflow.py --username "테스트2" --email "test2@example.com" --profile-id 2
```

### 성능 비교

```python
import time

# psycopg2
start = time.time()
db = Database()
user_id = db.create_user("test", "test@example.com")
print(f"psycopg2: {time.time() - start:.3f}s")

# SQLAlchemy
start = time.time()
db = DatabaseSQLAlchemy()
user_id = db.create_user("test2", "test2@example.com")
print(f"SQLAlchemy: {time.time() - start:.3f}s")
```

---

## 9. 결론

### 즉시 적용하기
```python
# main_workflow.py 첫 줄만 변경
from database_sqlalchemy import DatabaseSQLAlchemy as Database

# 나머지 코드는 모두 동일하게 작동!
```

### 점진적 도입
1. Week 1: database_sqlalchemy.py 테스트
2. Week 2: main_workflow.py 전환
3. Week 3: workflow.py 전환
4. Week 4: Alembic migration 도입

### 장기 계획
- 프로젝트가 커지면 SQLAlchemy + Alembic 도입
- 현재는 psycopg2로 충분
- 언제든 전환 가능하도록 인터페이스 설계함
