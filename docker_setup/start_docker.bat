@echo off
REM Docker Desktop으로 PostgreSQL + Neo4j 시작 스크립트 (Windows)

echo ==========================================
echo   ExplainMyBody - Docker 환경 시작
echo ==========================================
echo.

REM 1. Docker 실행 확인
echo 🔍 1단계: Docker 실행 확인...
docker info >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker가 실행되지 않았습니다.
    echo    Docker Desktop을 실행하고 다시 시도하세요.
    pause
    exit /b 1
)
echo ✅ Docker 실행 중
echo.

REM 2. docker-compose 파일 확인
echo 🔍 2단계: docker-compose.yml 확인...
if not exist "docker-compose.yml" (
    echo ❌ docker-compose.yml 파일을 찾을 수 없습니다.
    pause
    exit /b 1
)
echo ✅ docker-compose.yml 존재
echo.

REM 3. 컨테이너 시작
echo 🚀 3단계: 컨테이너 시작 중...
docker-compose up -d
if errorlevel 1 (
    echo ❌ 컨테이너 시작 실패
    pause
    exit /b 1
)
echo.

REM 4. 컨테이너 상태 확인
echo 🔍 4단계: 컨테이너 상태 확인...
timeout /t 3 /nobreak >nul
docker-compose ps
echo.

REM 5. PostgreSQL 연결 대기
echo ⏳ 5단계: PostgreSQL 연결 대기...
timeout /t 5 /nobreak >nul
echo ✅ PostgreSQL 준비 중...
echo.

REM 6. Neo4j 연결 대기
echo ⏳ 6단계: Neo4j 연결 대기...
timeout /t 10 /nobreak >nul
echo ✅ Neo4j 준비 중...
echo.

REM 7. 완료 메시지
echo ==========================================
echo   ✅ Docker 환경 시작 완료!
echo ==========================================
echo.
echo 📊 접속 정보:
echo.
echo   PostgreSQL (pgvector):
echo     - Host: localhost:5432
echo     - User: postgres
echo     - Password: postgres
echo     - Database: explainmybody
echo.
echo   Neo4j:
echo     - 브라우저: http://localhost:7474
echo     - Bolt: bolt://localhost:7687
echo     - User: neo4j
echo     - Password: password
echo.
echo 📚 다음 단계:
echo.
echo   1. Neo4j Browser 열기:
echo      start http://localhost:7474
echo.
echo   2. Graph RAG 데이터 Import:
echo      python backend/utils/scripts/import_graph_rag.py --neo4j
echo.
echo   3. Graph RAG 파이프라인 실행:
echo      python src/llm/pipeline_weekly_plan_rag/main.py --user-id 1
echo.
echo ==========================================
echo.

REM Neo4j Browser 자동으로 열기 (옵션)
set /p OPEN_BROWSER="Neo4j Browser를 열까요? (y/n): "
if /i "%OPEN_BROWSER%"=="y" (
    start http://localhost:7474
)

pause
