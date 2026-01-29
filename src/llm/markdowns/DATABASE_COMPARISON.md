# Database 구현 비교: psycopg2 vs SQLAlchemy

## 📁 파일 구조

```
llm/
├── database.py                    # 현재 (psycopg2)
├── database_sqlalchemy.py         # 새로운 (SQLAlchemy)
├── db_models.py                   # SQLAlchemy ORM 모델
├── main_workflow.py               # psycopg2 사용
├── main_workflow_sqlalchemy.py    # SQLAlchemy 사용
├── test_db_comparison.py          # 비교 테스트 스크립트
├── SQLALCHEMY_MIGRATION_GUIDE.md  # 상세 가이드
└── DATABASE_COMPARISON.md         # 이 파일
```

---

## 🚀 빠른 시작

### 1. SQLAlchemy 설치
```bash
uv pip install sqlalchemy alembic
```

### 2. 비교 테스트 실행
```bash
python test_db_comparison.py
```

### 3. SQLAlchemy 버전 실행
```bash
python main_workflow_sqlalchemy.py \
  --username "홍길동" \
  --email "hong@example.com" \
  --profile-id 1
```

---

## 💡 주요 차이점

### 코드 레벨

#### psycopg2 (현재)
```python
# database.py
def create_user(self, username: str, email: str) -> int:
    cursor.execute(
        "INSERT INTO users (username, email) VALUES (%s, %s) RETURNING id",
        (username, email)
    )
    return cursor.fetchone()[0]
```

#### SQLAlchemy
```python
# database_sqlalchemy.py
def create_user(self, username: str, email: str) -> int:
    with self.get_session() as session:
        user = User(username=username, email=email)
        session.add(user)
        session.flush()
        return user.id
```

**결과: 동일한 인터페이스, 다른 내부 구현**

---

## ✅ SQLAlchemy 이점

### 1. 타입 안전성
```python
# db_models.py
class User(Base):
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255), unique=True)

# IDE가 자동완성 제공!
user.id        # ✅
user.username  # ✅
user.emial     # ❌ IDE가 오타 감지!
```

### 2. Relationship 관리
```python
# ORM 방식
with db.get_session() as session:
    user = session.get(User, 1)

    # Relationship으로 자동 JOIN
    for record in user.health_records:
        print(record.measurements)

    for report in user.analysis_reports:
        print(report.llm_output)
```

### 3. Migration 관리 (Alembic)
```bash
# 스키마 변경 추적
alembic revision --autogenerate -m "Add phone to users"
alembic upgrade head

# 롤백 가능
alembic downgrade -1
```

### 4. 복잡한 쿼리 빌더
```python
from sqlalchemy import select, and_

# Type-safe 쿼리
stmt = (
    select(HealthRecord)
    .where(
        and_(
            HealthRecord.user_id == 1,
            HealthRecord.source == "inbody_ocr"
        )
    )
    .order_by(HealthRecord.measured_at.desc())
    .limit(10)
)
```

---

## ⚠️ SQLAlchemy 단점

### 1. JSONB 쿼리 복잡도

#### psycopg2 (간단)
```python
cursor.execute(
    "SELECT * FROM health_records WHERE measurements->>'stage2' = %s",
    ("근육형",)
)
```

#### SQLAlchemy (복잡)
```python
stmt = select(HealthRecord).where(
    HealthRecord.measurements["stage2"].astext == "근육형"
)
```

### 2. 러닝 커브
- ORM 개념 이해 필요
- SQLAlchemy 문법 학습 필요
- Session 관리 주의 필요

### 3. 성능 오버헤드
- ORM 레이어 추가로 약간의 성능 저하 (보통 10-20% 정도)
- 대부분의 경우 무시할 수준

---

## 📊 성능 비교

```bash
# test_db_comparison.py 실행 결과 예시

[1] 연결 테스트
✅ psycopg2 연결 성공 (0.015s)
✅ SQLAlchemy 연결 성공 (0.052s)  # 첫 연결 시 ORM 초기화

[2] 사용자 생성 테스트
✅ psycopg2: User ID 1 생성 (0.0034s)
✅ SQLAlchemy: User ID 2 생성 (0.0041s)  # 거의 차이 없음

[3] 건강 기록 저장 테스트
✅ psycopg2: Record ID 1 저장 (0.0038s)
✅ SQLAlchemy: Record ID 2 저장 (0.0045s)

[4] JSONB 검색 테스트
✅ psycopg2: 1개 검색 (0.0029s)
✅ SQLAlchemy: 1개 검색 (0.0033s)
```

**결론: 실사용에서는 성능 차이 미미**

---

## 🎯 언제 SQLAlchemy를 사용해야 할까?

### ✅ SQLAlchemy 추천
- 팀이 2명 이상
- 스키마 변경이 빈번함
- 복잡한 JOIN 쿼리 많음
- 타입 안전성 중요
- 다른 DB로 전환 가능성 있음

### ✅ psycopg2 추천 (현재)
- 혼자 개발
- 테이블 구조 단순 (4개)
- JSONB 중심 설계
- 빠른 프로토타이핑

---

## 🔄 마이그레이션 방법

### 옵션 1: 완전 교체 (권장 X)
```python
# database.py 삭제
# database_sqlalchemy.py를 database.py로 이름 변경
```

### 옵션 2: 점진적 도입 (권장 ✅)

#### Step 1: 새 파일로 테스트
```bash
python main_workflow_sqlalchemy.py --username "테스트" --email "test@example.com" --profile-id 1
```

#### Step 2: 문제없으면 main_workflow.py import만 변경
```python
# main_workflow.py
# from database import Database
from database_sqlalchemy import DatabaseSQLAlchemy as Database
```

#### Step 3: 다른 파일도 순차 변경
```python
# workflow.py
from database_sqlalchemy import DatabaseSQLAlchemy as Database
```

---

## 📝 인터페이스 호환성

**모든 메서드가 동일한 인터페이스 제공!**

| 메서드 | psycopg2 | SQLAlchemy | 호환성 |
|--------|----------|------------|--------|
| `create_user()` | ✅ | ✅ | 100% |
| `get_user_by_email()` | ✅ | ✅ | 100% |
| `get_user_by_id()` | ✅ | ✅ | 100% |
| `save_health_record()` | ✅ | ✅ | 100% |
| `get_health_record()` | ✅ | ✅ | 100% |
| `get_user_health_records()` | ✅ | ✅ | 100% |
| `search_health_records_by_measurement()` | ✅ | ✅ | 100% |
| `save_analysis_report()` | ✅ | ✅ | 100% |
| `get_analysis_report()` | ✅ | ✅ | 100% |
| `create_user_goal()` | ✅ | ✅ | 100% |
| `get_active_user_goals()` | ✅ | ✅ | 100% |
| `test_connection()` | ✅ | ✅ | 100% |
| `get_user_statistics()` | ✅ | ✅ | 100% |

**기존 코드를 전혀 수정하지 않아도 작동합니다!**

---

## 🎓 학습 자료

### SQLAlchemy 공식 문서
- [SQLAlchemy 2.0 Tutorial](https://docs.sqlalchemy.org/en/20/tutorial/)
- [ORM Quick Start](https://docs.sqlalchemy.org/en/20/orm/quickstart.html)

### Alembic Migration
- [Alembic Tutorial](https://alembic.sqlalchemy.org/en/latest/tutorial.html)

### 프로젝트 내 문서
- `SQLALCHEMY_MIGRATION_GUIDE.md` - 상세 가이드
- `DATABASE_COMPARISON.md` - 이 파일

---

## 💬 추천 사항

### 현재 프로젝트 (혼자 개발, 프로토타입)
**👉 psycopg2 유지 권장**

이유:
- 현재 구조가 JSONB 중심
- 쿼리가 단순함
- 빠른 개발 속도

### 향후 확장 시
**👉 SQLAlchemy 도입 고려**

타이밍:
- 팀원 추가 시
- 스키마 변경 빈번해질 때
- 복잡한 통계 쿼리 필요 시

---

## ✨ 결론

1. **두 구현 모두 준비됨** - 언제든 전환 가능
2. **인터페이스 동일** - 기존 코드 수정 불필요
3. **성능 차이 미미** - 실사용에서는 무시 가능
4. **선택은 자유** - 필요에 따라 선택

**지금은 psycopg2로 충분하지만, 확장 시 SQLAlchemy로 쉽게 전환 가능합니다!**
