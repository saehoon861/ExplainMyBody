# Docker Desktop으로 PostgreSQL + Neo4j 실행하기

## 사전 준비

1. **Docker Desktop 설치 확인**
   - Windows: Docker Desktop for Windows
   - macOS: Docker Desktop for Mac
   - Docker Desktop이 실행 중인지 확인

2. **프로젝트 루트로 이동**
   ```bash
   cd /home/user/projects/ExplainMyBody
   ```

## 방법 1: docker-compose 사용 (권장) ⭐

### 1-1. 컨테이너 시작

```bash
# PostgreSQL + Neo4j 동시 실행
docker-compose up -d

# 로그 확인
docker-compose logs -f
```

**출력 예시**:
```
Creating explainmybody-postgres ... done
Creating explainmybody-neo4j     ... done
```

### 1-2. 실행 확인

```bash
# 컨테이너 상태 확인
docker-compose ps

# 개별 로그 확인
docker-compose logs postgres
docker-compose logs neo4j
```

**예상 출력**:
```
NAME                      STATUS      PORTS
explainmybody-postgres    Up          0.0.0.0:5432->5432/tcp
explainmybody-neo4j       Up          0.0.0.0:7474->7474/tcp, 0.0.0.0:7687->7687/tcp
```

### 1-3. Neo4j 브라우저 접속

브라우저에서 열기:
```
http://localhost:7474
```

**로그인 정보**:
- Username: `neo4j`
- Password: `password`

**첫 로그인 시**: 비밀번호 변경 요구됨 (그대로 `password` 사용 가능)

### 1-4. 컨테이너 중지/시작/삭제

```bash
# 중지
docker-compose stop

# 시작
docker-compose start

# 중지 + 삭제 (데이터는 유지됨)
docker-compose down

# 중지 + 삭제 + 볼륨 삭제 (데이터 완전 삭제)
docker-compose down -v
```

## 방법 2: Docker Desktop UI 사용

### 2-1. Docker Desktop 앱 열기

Windows/Mac에서 Docker Desktop 앱 실행

### 2-2. Images 탭에서 이미지 다운로드

1. **Images** 탭 클릭
2. 검색창에 `neo4j` 입력
3. `neo4j:5.15-community` 선택 후 **Pull** 클릭

### 2-3. Containers 탭에서 실행

1. **Containers** 탭 클릭
2. **Run** 버튼 클릭 (또는 Images → neo4j → Run)
3. **Optional settings** 펼치기
4. 다음 설정 입력:

**Container name**:
```
explainmybody-neo4j
```

**Ports** (Port mapping):
```
7474:7474
7687:7687
```

**Environment variables** (환경변수):
```
NEO4J_AUTH=neo4j/password
```

**Volumes** (볼륨):
```
neo4j_data → /data
neo4j_logs → /logs
```

5. **Run** 클릭

### 2-4. 실행 확인

Docker Desktop → **Containers** 탭에서 `explainmybody-neo4j`가 **Running** 상태인지 확인

## 방법 3: Docker CLI 직접 사용

### 3-1. Neo4j 컨테이너 실행

```bash
docker run -d \
  --name explainmybody-neo4j \
  -p 7474:7474 \
  -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  -v neo4j_data:/data \
  -v neo4j_logs:/logs \
  neo4j:5.15-community
```

### 3-2. 실행 확인

```bash
# 컨테이너 목록 확인
docker ps

# 로그 확인
docker logs explainmybody-neo4j

# 로그 실시간 추적
docker logs -f explainmybody-neo4j
```

### 3-3. 컨테이너 관리

```bash
# 중지
docker stop explainmybody-neo4j

# 시작
docker start explainmybody-neo4j

# 재시작
docker restart explainmybody-neo4j

# 삭제
docker rm explainmybody-neo4j

# 삭제 (실행 중이어도)
docker rm -f explainmybody-neo4j
```

## Neo4j 접속 방법

### 1. 브라우저 UI (Neo4j Browser)

```
http://localhost:7474
```

- **Username**: `neo4j`
- **Password**: `password`

**첫 실행 시 테스트 쿼리**:
```cypher
// 노드 수 확인
MATCH (n) RETURN count(n);

// 관계 수 확인
MATCH ()-[r]->() RETURN count(r);

// 샘플 데이터 조회
MATCH (p:Paper) RETURN p LIMIT 5;
```

### 2. Python 코드에서 접속

`.env` 파일:
```bash
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
```

Python 테스트:
```python
from neo4j import GraphDatabase

driver = GraphDatabase.driver(
    "bolt://localhost:7687",
    auth=("neo4j", "password")
)

# 연결 테스트
driver.verify_connectivity()
print("✅ Neo4j 연결 성공!")

driver.close()
```

## 데이터 Import

Neo4j가 실행되면 Graph RAG 데이터를 로드하세요:

```bash
# PostgreSQL + Neo4j에 데이터 로드
python backend/utils/scripts/import_graph_rag.py --neo4j

# PostgreSQL만 (Neo4j 스킵)
python backend/utils/scripts/import_graph_rag.py
```

**예상 출력**:
```
============================================================
  Graph RAG Data Import Script
============================================================

📂 JSON 파일 로드 중: src/llm/ragdb_collect/outputs/graph_rag_2577papers_20260130_130411.json
  ✓ Nodes: 2,149개
  ✓ Edges: 9,176개

🔧 pgvector extension 확인 중...
  ✓ pgvector extension 활성화 완료

📥 PostgreSQL에 2,149개 논문 삽입 중...
  ✅ 논문 삽입 완료: 2,149개 성공, 0개 스킵

📥 PostgreSQL에 9,176개 관계 삽입 중...
  ✅ 관계 삽입 완료: 9,176개 성공, 0개 스킵

🔷 Neo4j에 그래프 데이터 로드 중...
  ✅ Neo4j 연결 성공: bolt://localhost:7687
  ✓ Paper 노드: 2,149/2,149
  ✓ 관계: 9,176/9,176
  ✅ Neo4j 로드 완료

============================================================
  ✅ Graph RAG 데이터 Import 완료!
============================================================
```

## Docker Desktop에서 확인하기

### Containers 탭

- `explainmybody-postgres`: PostgreSQL (pgvector)
- `explainmybody-neo4j`: Neo4j Graph DB

각 컨테이너를 클릭하면:
- **Logs**: 실시간 로그 확인
- **Inspect**: 상세 정보
- **Stats**: CPU/메모리 사용량
- **Terminal**: 컨테이너 내부 접속

### Volumes 탭

생성된 볼륨 확인:
- `postgres_data`: PostgreSQL 데이터
- `neo4j_data`: Neo4j 데이터
- `neo4j_logs`: Neo4j 로그

## 문제 해결

### 포트 충돌

**에러**: `port is already allocated`

**해결**:
```bash
# 사용 중인 포트 확인 (Windows)
netstat -ano | findstr :7474
netstat -ano | findstr :7687

# 사용 중인 포트 확인 (Mac/Linux)
lsof -i :7474
lsof -i :7687

# 다른 포트 사용 (docker-compose.yml 수정)
ports:
  - "17474:7474"  # 외부 포트 변경
  - "17687:7687"
```

### 메모리 부족

**증상**: Neo4j가 느리거나 크래시

**해결**: `docker-compose.yml`에서 메모리 설정 조정
```yaml
environment:
  NEO4J_server_memory_heap_max__size: 1G  # 2G → 1G로 감소
  NEO4J_server_memory_pagecache_size: 512m  # 1G → 512m로 감소
```

### 연결 실패

**에러**: `Unable to connect to localhost:7687`

**해결**:
```bash
# 1. Neo4j 로그 확인
docker logs explainmybody-neo4j

# 2. Neo4j가 완전히 시작될 때까지 대기 (30초~1분)
docker logs -f explainmybody-neo4j
# "Started." 메시지 확인

# 3. 컨테이너 재시작
docker restart explainmybody-neo4j
```

### 비밀번호 변경

Neo4j Browser에서 Cypher로 변경:
```cypher
ALTER CURRENT USER SET PASSWORD FROM 'password' TO 'new_password';
```

또는 환경변수 변경:
```yaml
# docker-compose.yml
environment:
  NEO4J_AUTH: neo4j/new_password
```

## 완전 초기화

모든 데이터를 삭제하고 처음부터:

```bash
# 1. 컨테이너 중지 및 삭제
docker-compose down -v

# 2. 볼륨 삭제 확인
docker volume ls
docker volume rm explainmybody_neo4j_data
docker volume rm explainmybody_postgres_data

# 3. 재시작
docker-compose up -d

# 4. 데이터 재로드
python backend/utils/scripts/import_graph_rag.py --neo4j
```

## 유용한 명령어 모음

```bash
# === Docker Compose ===
# 시작 (백그라운드)
docker-compose up -d

# 중지
docker-compose stop

# 재시작
docker-compose restart

# 로그 확인 (실시간)
docker-compose logs -f

# 특정 서비스만 재시작
docker-compose restart neo4j

# === Docker CLI ===
# 모든 컨테이너 확인
docker ps -a

# Neo4j 컨테이너 접속
docker exec -it explainmybody-neo4j bash

# Neo4j Cypher Shell 접속
docker exec -it explainmybody-neo4j cypher-shell -u neo4j -p password

# === Neo4j 상태 확인 ===
# HTTP 엔드포인트 확인
curl http://localhost:7474

# Bolt 연결 확인
docker exec explainmybody-neo4j cypher-shell -u neo4j -p password "MATCH (n) RETURN count(n);"
```

## Windows 사용자 주의사항

### WSL2 사용 시

Docker Desktop이 WSL2를 사용하는 경우:

1. **파일 경로**: WSL2 내부 경로 사용
   ```bash
   cd /home/user/projects/ExplainMyBody
   ```

2. **포트 접속**: `localhost` 또는 `127.0.0.1` 사용 가능
   ```
   http://localhost:7474
   ```

3. **볼륨 위치**: WSL2 파일시스템에 저장됨
   ```
   \\wsl$\docker-desktop-data\data\docker\volumes
   ```

## 다음 단계

1. ✅ Neo4j 실행 확인
   ```bash
   curl http://localhost:7474
   ```

2. ✅ 데이터 Import
   ```bash
   python backend/utils/scripts/import_graph_rag.py --neo4j
   ```

3. ✅ Neo4j Browser에서 데이터 확인
   ```
   http://localhost:7474
   ```

   Cypher 쿼리:
   ```cypher
   // 논문 수 확인
   MATCH (p:Paper) RETURN count(p);

   // 개념 수 확인
   MATCH (c:Concept) RETURN count(c);

   // 샘플 관계 확인
   MATCH (p:Paper)-[r]->(c:Concept)
   RETURN p.title, type(r), c.id
   LIMIT 10;
   ```

4. ✅ Graph RAG 파이프라인 실행
   ```bash
   python src/llm/pipeline_weekly_plan_rag/main.py --user-id 1
   ```
