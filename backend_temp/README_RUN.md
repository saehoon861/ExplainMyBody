# 백엔드 및 데이터베이스 실행 가이드 (backend_temp)

현재 사용 중인 `backend_temp` 환경에서의 데이터베이스 및 서버 실행 방법입니다.

## 1. 데이터베이스 서버 (SQLite)
현재 프로젝트는 **SQLite**를 사용하고 있습니다. 
- **별도의 서버 설치 불필요**: SQLite는 파일 기반 데이터베이스(`explainmybody.db`)이므로, MySQL이나 PostgreSQL처럼 별도의 DB 서버 프로그램을 실행할 필요가 없습니다.
- **자동 관리**: 백엔드 서버(`app.py`)가 실행될 때 자동으로 해당 파일을 읽고 쓰며 관리합니다.

## 2. 백엔드 서버 실행 방법
터미널에서 아래 명령어를 입력하여 서버를 실행합니다.

```bash
# 위치 이동 (이미 해당 폴더인 경우 생략 가능)
cd /home/roh/myworkspace/ExplainMyBody/backend_temp

# 서버 실행 (uv 사용 시)
uv run uvicorn app:app --port 5000 --reload
```

- **--port 5000**: 프론트엔드와 약속된 5000번 포트로 서버를 엽니다.
- **--reload**: 코드를 수정하면 서버가 자동으로 재시작됩니다.

## 3. 데이터 확인 방법 (디버그)
서버가 실행 중일 때 브라우저에서 아래 주소에 접속하면 DB에 저장된 데이터를 직접 확인할 수 있습니다.
- **가입 유저 목록 확인**: `http://localhost:5000/api/debug/users`

---
> [!NOTE]
> 만약 나중에 실제 서비스용인 `postgresql`로 전환하게 되면, 그때는 별도의 DB 서버(PostgreSQL)를 실행해야 합니다. 지금은 이 명령어로 충분합니다!
