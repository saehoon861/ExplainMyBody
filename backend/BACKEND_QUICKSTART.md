# ExplainMyBody Backend Quickstart

이 문서는 백엔드 서버 개발을 위한 가상환경 설정, 패키지 설치 및 실행 방법을 안내합니다.

## 개발 환경

- **Python**: 3.11
- **OS**: Ubuntu 22.04 (Linux)
- **패키지 관리자**: uv (backend 디렉토리에서 관리)
- **데이터베이스**: PostgreSQL

## 설치 및 실행

> **중요**: uv 가상환경은 **backend 디렉토리(`/home/user/ExplainMyBody/backend/`)** 에서 생성하고 관리합니다.

### 0. uv 설치 (처음 한 번만)
```bash
# uv가 설치되어 있지 않은 경우
curl -LsSf https://astral.sh/uv/install.sh | sh
# 또는
pip install uv
```

### 1. 가상환경 생성 및 활성화 (backend 디렉토리에서)
```bash
# backend 디렉토리로 이동
cd /home/user/ExplainMyBody/backend

# uv로 Python 3.11 가상환경 생성
uv venv --python 3.11

# 가상환경 활성화
source .venv/bin/activate
```

### 2. 패키지 설치 (backend 디렉토리에서)
```bash
# backend 디렉토리에서 실행
cd /home/user/ExplainMyBody/backend

# pyproject.toml 기반으로 모든 의존성 설치
uv sync

# 개발 도구 포함 설치
uv sync --group dev
```

### 3. 환경 변수 설정
```bash
cd backend
cp .env.example .env
# .env 파일을 열어서 데이터베이스 연결 정보 등을 수정
```

### 4. 데이터베이스 준비
PostgreSQL이 설치되어 있어야 합니다.
```bash
# PostgreSQL에서 데이터베이스 생성
createdb explainmybody
```

| 동작	| 명령어	| 설명
| :--- | :--- | :--- |
| 동작 |	sudo service postgresql start	|DB 서버를 가동합니다. (백엔드 실행 전 필수)
| 동작 |	sudo service postgresql stop	|DB 서버를 종료합니다. (작업 종료 후)
| 동작 |	sudo service postgresql status 또는 pg_isready	|현재 DB가 켜져 있는지 확인합니다.
| 동작 |	sudo service postgresql restart	|설정을 바꿨을 때 껐다 켜는 용도입니다.

### 5. 서버 실행
```bash
# backend 디렉토리에서 실행
cd backend

# 개발 모드로 실행 (자동 재시작)
uv run uvicorn main:app --reload
```

서버가 실행되면 http://localhost:8000 에서 접근 가능합니다.

## 패키지 추가 방법

```bash
# backend 디렉토리로 이동
cd /home/user/ExplainMyBody/backend

# 방법 1: 단일 패키지 추가 (자동으로 pyproject.toml 업데이트)
uv add <package-name>

# 개발 전용 패키지 추가
uv add --group dev <package-name>

# 방법 2: 여러 패키지 한 번에 추가 (추천)
# pyproject.toml 파일을 열어서 dependencies 리스트에 직접 추가
nano pyproject.toml  # 또는 code, vim 등

# 예시: LLM 패키지 여러 개 추가
# dependencies = [
#     ...
#     "openai>=1.0,<2.0",
#     "anthropic>=0.18,<1.0",
#     "langchain>=0.1,<1.0",
# ]

# 추가 후 동기화
uv sync

# 선택적 의존성 그룹 사용 (pyproject.toml에 정의)
# [dependency-groups]
# llm = ["openai>=1.0", "anthropic>=0.18"]

# 특정 그룹만 설치
uv sync --group llm
```

---
[README.md로 돌아가기](./README.md)
