# PostgreSQL 설정 가이드

## PostgreSQL + pgvector 설치 및 설정

### 1. PostgreSQL 설치

#### Ubuntu/Debian
```bash
# PostgreSQL 설치
sudo apt update
sudo apt install postgresql postgresql-contrib

# 서비스 시작
sudo systemctl start postgresql
sudo systemctl enable postgresql

# 상태 확인
sudo systemctl status postgresql
```

#### macOS (Homebrew)
```bash
# PostgreSQL 설치
brew install postgresql@15

# 서비스 시작
brew services start postgresql@15
```

#### Docker 사용
```bash
# PostgreSQL + pgvector 도커 이미지 실행
docker run -d \
  --name explainmybody-postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_DB=explainmybody \
  -p 5432:5432 \
  pgvector/pgvector:pg16

# 로그 확인
docker logs explainmybody-postgres

# 접속 테스트
docker exec -it explainmybody-postgres psql -U postgres -d explainmybody
```

---

### 2. 데이터베이스 생성

```bash
# PostgreSQL 사용자로 전환
sudo -u postgres psql

# 데이터베이스 생성
CREATE DATABASE explainmybody;

# 사용자 생성 (선택사항)
CREATE USER explainmybody_user WITH PASSWORD 'your_password';

# 권한 부여
GRANT ALL PRIVILEGES ON DATABASE explainmybody TO explainmybody_user;

# 종료
\q
```

---

### 3. pgvector Extension 설치

#### 수동 설치 (Ubuntu/Debian)
```bash
# 의존성 설치
sudo apt install -y postgresql-server-dev-all git build-essential

# pgvector 다운로드 및 빌드
cd /tmp
git clone --branch v0.5.1 https://github.com/pgvector/pgvector.git
cd pgvector
make
sudo make install
```

#### macOS (Homebrew)
```bash
brew install pgvector
```

#### Docker를 사용하는 경우
Docker 이미지 `pgvector/pgvector`를 사용하면 이미 설치되어 있습니다.

#### Extension 활성화
```sql
-- psql로 데이터베이스 접속 후
\c explainmybody

-- pgvector extension 생성
CREATE EXTENSION IF NOT EXISTS vector;

-- 확인
\dx
```

---

### 4. 연결 문자열 설정

`.env` 파일에 PostgreSQL 연결 정보 설정:

```bash
# .env
DATABASE_URL=postgresql://username:password@host:port/database

# 예시 (로컬)
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/explainmybody

# 예시 (Docker)
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/explainmybody

# 예시 (원격 서버)
DATABASE_URL=postgresql://explainmybody_user:your_password@192.168.1.100:5432/explainmybody

# 예시 (Supabase, Neon 등 클라우드)
DATABASE_URL=postgresql://user:password@host.region.cloud.provider.com:5432/database?sslmode=require
```

---

### 5. 연결 테스트

#### Python 스크립트로 테스트
```bash
cd /home/user/projects/ExplainMyBody/llm

python3 << EOF
from database import Database

db = Database()
if db.test_connection():
    print("✅ PostgreSQL 연결 성공!")
else:
    print("❌ PostgreSQL 연결 실패")
EOF
```

#### psql로 직접 테스트
```bash
# 로컬
psql -U postgres -d explainmybody -c "SELECT version();"

# 원격
psql -U username -h hostname -d explainmybody -c "SELECT version();"

# 연결 문자열로 테스트
psql "postgresql://postgres:postgres@localhost:5432/explainmybody" -c "SELECT 1;"
```

---

### 6. 테이블 생성 확인

프로그램을 실행하면 자동으로 테이블이 생성됩니다:

```bash
python main_workflow.py --list-users
```

수동으로 확인:
```sql
-- psql 접속
psql -U postgres -d explainmybody

-- 테이블 목록 확인
\dt

-- 테이블 구조 확인
\d users
\d health_records
\d analysis_reports
\d user_goals

-- pgvector extension 확인
\dx vector
```

---

### 7. pgvector 사용 예시 (향후 활용)

#### Vector 컬럼 추가 예시
```sql
-- 리포트에 embedding 컬럼 추가 (나중에 사용)
ALTER TABLE analysis_reports
ADD COLUMN embedding vector(1536);

-- 인덱스 생성 (유사도 검색 최적화)
CREATE INDEX ON analysis_reports
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
```

#### Python에서 Vector 저장/검색 예시
```python
from database import Database

db = Database()

# Vector 저장 (OpenAI embedding 예시)
embedding = [0.1, 0.2, 0.3, ...]  # 1536차원

with db.get_connection() as conn:
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE analysis_reports SET embedding = %s WHERE id = %s",
        (embedding, report_id)
    )

# 유사도 검색 (코사인 유사도)
with db.get_connection() as conn:
    cursor = conn.cursor()
    cursor.execute(
        """SELECT id, llm_output,
           1 - (embedding <=> %s) as similarity
           FROM analysis_reports
           WHERE user_id = %s
           ORDER BY embedding <=> %s
           LIMIT 5""",
        (query_embedding, user_id, query_embedding)
    )
    similar_reports = cursor.fetchall()
```

---

## 주요 기능

### PostgreSQL 장점
- ✅ **JSONB 지원**: 유연한 측정 데이터 저장 및 빠른 검색
- ✅ **pgvector 지원**: 임베딩 벡터 저장 및 유사도 검색
- ✅ **확장성**: 대용량 데이터 처리
- ✅ **트랜잭션**: ACID 보장
- ✅ **인덱싱**: GIN, BTREE, IVFFlat 등 다양한 인덱스

### JSONB 활용 예시
```sql
-- 특정 체형을 가진 사용자 검색
SELECT * FROM health_records
WHERE measurements->>'stage2_근육보정체형' = '근육형';

-- BMI 범위 검색
SELECT * FROM health_records
WHERE (measurements->>'BMI')::float BETWEEN 20 AND 25;

-- 부위별 근육 등급 검색
SELECT * FROM health_records
WHERE measurements->'근육_부위별등급'->>'왼팔' = '표준이상';
```

---

## 문제 해결

### 1. 연결 거부 오류
```
psycopg2.OperationalError: could not connect to server
```

**해결:**
```bash
# PostgreSQL 서비스 상태 확인
sudo systemctl status postgresql

# 서비스 시작
sudo systemctl start postgresql

# Docker의 경우
docker start explainmybody-postgres
```

### 2. 인증 실패
```
psycopg2.OperationalError: FATAL: password authentication failed
```

**해결:**
- `.env` 파일의 DATABASE_URL 확인
- 사용자 비밀번호 재설정:
```sql
ALTER USER postgres WITH PASSWORD 'new_password';
```

### 3. 데이터베이스가 없음
```
psycopg2.OperationalError: FATAL: database "explainmybody" does not exist
```

**해결:**
```bash
# 데이터베이스 생성
sudo -u postgres createdb explainmybody

# 또는 psql로
psql -U postgres -c "CREATE DATABASE explainmybody;"
```

### 4. pgvector extension 설치 실패
```
ERROR: could not open extension control file
```

**해결:**
- Ubuntu: `sudo apt install postgresql-15-pgvector`
- 수동 빌드: 위의 "3. pgvector Extension 설치" 참고
- Docker 사용 권장

---

## Docker Compose 예시

프로젝트 루트에 `docker-compose.yml` 생성:

```yaml
version: '3.8'

services:
  postgres:
    image: pgvector/pgvector:pg16
    container_name: explainmybody-postgres
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: explainmybody
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

volumes:
  postgres_data:
```

실행:
```bash
docker-compose up -d

# 로그 확인
docker-compose logs -f postgres

# 중지
docker-compose down
```

---

## 백업 및 복구

### 백업
```bash
# 전체 데이터베이스 백업
pg_dump -U postgres explainmybody > backup_$(date +%Y%m%d).sql

# Docker의 경우
docker exec explainmybody-postgres pg_dump -U postgres explainmybody > backup.sql
```

### 복구
```bash
# 복구
psql -U postgres explainmybody < backup_20260123.sql

# Docker의 경우
docker exec -i explainmybody-postgres psql -U postgres explainmybody < backup.sql
```

---

## 참고 자료

- [PostgreSQL 공식 문서](https://www.postgresql.org/docs/)
- [pgvector GitHub](https://github.com/pgvector/pgvector)
- [psycopg2 문서](https://www.psycopg.org/docs/)
- [JSONB 사용법](https://www.postgresql.org/docs/current/datatype-json.html)
