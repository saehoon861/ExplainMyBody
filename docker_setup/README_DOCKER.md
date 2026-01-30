# Docker Desktop 빠른 시작 가이드

PostgreSQL (pgvector) + Neo4j를 Docker Desktop으로 한 번에 실행하기

## 🚀 빠른 시작 (30초)

### Windows

```bash
# 1. Docker Desktop 실행 (백그라운드)

# 2. 이 스크립트 더블클릭 또는 실행
start_docker.bat

# 또는 CMD에서
.\start_docker.bat
```

### Mac / Linux / WSL

```bash
# 1. Docker Desktop 실행 (백그라운드)

# 2. 스크립트 실행
./start_docker.sh

# 또는
bash start_docker.sh
```

### 직접 실행 (모든 OS)

```bash
# Docker Desktop 실행 후
docker-compose up -d
```

## ✅ 실행 확인

### 1. Docker Desktop에서 확인

Docker Desktop 앱 열기 → **Containers** 탭

다음 컨테이너가 **Running** 상태여야 함:
- ✅ `explainmybody-postgres` (PostgreSQL)
- ✅ `explainmybody-neo4j` (Neo4j)

### 2. 브라우저에서 확인

```
http://localhost:7474
```

Neo4j Browser가 열리면 성공!

**로그인**:
- Username: `neo4j`
- Password: `password`

### 3. 명령어로 확인

```bash
# 컨테이너 상태
docker-compose ps

# PostgreSQL 연결 테스트
docker exec explainmybody-postgres pg_isready -U postgres

# Neo4j 연결 테스트
curl http://localhost:7474
```

## 📊 접속 정보

### PostgreSQL (pgvector)

```
Host: localhost
Port: 5432
User: postgres
Password: postgres
Database: explainmybody
```

**Python 연결**:
```python
DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/explainmybody"
```

### Neo4j

```
HTTP UI: http://localhost:7474
Bolt: bolt://localhost:7687
User: neo4j
Password: password
```

**Python 연결**:
```python
from neo4j import GraphDatabase

driver = GraphDatabase.driver(
    "bolt://localhost:7687",
    auth=("neo4j", "password")
)
```

## 📚 다음 단계

### 1. Neo4j Browser 열기

```
http://localhost:7474
```

첫 로그인 시 비밀번호 변경 요구 → 그대로 `password` 사용 가능

### 2. Graph RAG 데이터 Import

```bash
# PostgreSQL + Neo4j에 2,149개 논문 + 9,176개 관계 로드
python backend/utils/scripts/import_graph_rag.py --neo4j

# 또는 PostgreSQL만 (Neo4j 스킵)
python backend/utils/scripts/import_graph_rag.py
```

**예상 시간**: 약 2-5분

### 3. Neo4j에서 데이터 확인

Neo4j Browser (http://localhost:7474)에서 Cypher 쿼리 실행:

```cypher
// 논문 수 확인
MATCH (p:Paper) RETURN count(p);

// 개념 수 확인
MATCH (c:Concept) RETURN count(c);

// 관계 수 확인
MATCH ()-[r]->() RETURN count(r);

// 샘플 데이터 조회
MATCH (p:Paper)-[r:MENTIONS]->(c:Concept)
RETURN p.title, c.id, r.confidence
LIMIT 10;
```

### 4. Graph RAG 파이프라인 실행

```bash
python src/llm/pipeline_weekly_plan_rag/main.py --user-id 1
```

## 🛠️ 관리 명령어

### 시작/중지/재시작

```bash
# 시작
docker-compose start

# 중지
docker-compose stop

# 재시작
docker-compose restart

# 중지 + 삭제 (데이터는 유지)
docker-compose down

# 중지 + 삭제 + 데이터 삭제
docker-compose down -v
```

### 로그 확인

```bash
# 전체 로그 (실시간)
docker-compose logs -f

# PostgreSQL 로그만
docker-compose logs -f postgres

# Neo4j 로그만
docker-compose logs -f neo4j

# 최근 100줄만
docker-compose logs --tail=100
```

### 컨테이너 접속

```bash
# PostgreSQL 접속
docker exec -it explainmybody-postgres psql -U postgres -d explainmybody

# Neo4j Cypher Shell 접속
docker exec -it explainmybody-neo4j cypher-shell -u neo4j -p password

# Bash 접속
docker exec -it explainmybody-neo4j bash
```

## 🐛 문제 해결

### 포트 충돌

**증상**: `port is already allocated`

**원인**: 다른 프로세스가 포트 사용 중

**해결**:

**Windows**:
```cmd
netstat -ano | findstr :5432
netstat -ano | findstr :7474
netstat -ano | findstr :7687

# 해당 PID 프로세스 종료
taskkill /PID [PID번호] /F
```

**Mac/Linux**:
```bash
lsof -i :5432
lsof -i :7474
lsof -i :7687

# 해당 프로세스 종료
kill [PID]
```

**또는 포트 변경** (`docker-compose.yml`):
```yaml
ports:
  - "15432:5432"  # PostgreSQL
  - "17474:7474"  # Neo4j HTTP
  - "17687:7687"  # Neo4j Bolt
```

### 연결 실패

**증상**: `Connection refused`

**해결**:

1. **컨테이너 상태 확인**
   ```bash
   docker-compose ps
   ```
   → 모두 `Up` 상태여야 함

2. **로그 확인**
   ```bash
   docker-compose logs
   ```
   → 에러 메시지 확인

3. **재시작**
   ```bash
   docker-compose restart
   ```

4. **완전 재시작**
   ```bash
   docker-compose down
   docker-compose up -d
   ```

### Neo4j가 느림

**원인**: 메모리 부족

**해결**: `docker-compose.yml`에서 메모리 설정 조정

```yaml
neo4j:
  environment:
    NEO4J_server_memory_heap_max__size: 1G    # 2G → 1G
    NEO4J_server_memory_pagecache_size: 512m  # 1G → 512m
```

그 후 재시작:
```bash
docker-compose down
docker-compose up -d
```

### 데이터 완전 초기화

```bash
# 1. 모든 컨테이너 및 볼륨 삭제
docker-compose down -v

# 2. 이미지까지 삭제 (선택)
docker rmi ankane/pgvector:latest neo4j:5.15-community

# 3. 재시작
docker-compose up -d

# 4. 데이터 재로드
python backend/utils/scripts/import_graph_rag.py --neo4j
```

## 📖 자세한 가이드

더 자세한 내용은 다음 문서 참고:

- **DOCKER_SETUP.md**: Docker Desktop 상세 가이드
- **backend/utils/scripts/README.md**: 데이터 Import 가이드
- **src/llm/pipeline_weekly_plan_rag/README.md**: Graph RAG 파이프라인 가이드
- **GRAPH_RAG_INTEGRATION.md**: 전체 통합 가이드

## 💡 팁

### Docker Desktop 리소스 설정

Docker Desktop → **Settings** → **Resources**

권장 설정:
- **CPUs**: 4개 이상
- **Memory**: 8GB 이상 (Neo4j 사용 시)
- **Disk**: 20GB 이상

### 자동 시작 설정

Docker Desktop → **Settings** → **General**
- ✅ Start Docker Desktop when you log in

### 컨테이너 자동 재시작

`docker-compose.yml`에 이미 설정됨:
```yaml
restart: unless-stopped
```

→ Docker Desktop 재시작 시 자동으로 컨테이너도 재시작됨

## ⚡ 성능 최적화

### PostgreSQL

```yaml
# docker-compose.yml에 추가 (선택)
environment:
  POSTGRES_SHARED_BUFFERS: 256MB
  POSTGRES_EFFECTIVE_CACHE_SIZE: 1GB
```

### Neo4j

```yaml
# docker-compose.yml에 추가 (선택)
environment:
  NEO4J_dbms_memory_transaction_total_max: 512m
  NEO4J_dbms_memory_transaction_max: 256m
```

## 🔐 보안 설정 (프로덕션)

개발 환경에서는 기본 비밀번호 사용 가능하지만, 프로덕션에서는 변경 필수:

```yaml
# docker-compose.yml
environment:
  # PostgreSQL
  POSTGRES_PASSWORD: your_strong_password

  # Neo4j
  NEO4J_AUTH: neo4j/your_strong_password
```

## 📦 백업 & 복원

### PostgreSQL

**백업**:
```bash
docker exec explainmybody-postgres pg_dump -U postgres explainmybody > backup.sql
```

**복원**:
```bash
cat backup.sql | docker exec -i explainmybody-postgres psql -U postgres -d explainmybody
```

### Neo4j

**백업**:
```bash
docker exec explainmybody-neo4j neo4j-admin database dump neo4j --to-path=/backups
docker cp explainmybody-neo4j:/backups ./neo4j_backup
```

**복원**:
```bash
docker-compose stop neo4j
docker exec explainmybody-neo4j neo4j-admin database load neo4j --from-path=/backups
docker-compose start neo4j
```

## 🎉 완료!

이제 Graph RAG 시스템을 사용할 준비가 되었습니다!

```bash
# 주간 계획 생성 (Graph RAG 자동 적용)
python src/llm/pipeline_weekly_plan_rag/main.py --user-id 1
```
