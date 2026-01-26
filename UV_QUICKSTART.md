# ExplainMyBody - UV 빠른 시작 가이드

## 🚀 빠른 시작 (Quick Start)

### 1단계: uv 설치 확인
```bash
# uv 버전 확인
uv --version

# 설치되어 있지 않다면
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2단계: 프로젝트 설정
```bash
cd /home/user/ExplainMyBody

# Python 3.11 가상환경 생성 (최상위 디렉토리에서)
uv venv --python 3.11

# 가상환경 활성화
source .venv/bin/activate

# 모든 의존성 설치 (pyproject.toml 기반)
uv sync

# 개발 도구 포함 설치
uv sync --group dev
```

### 3단계: 환경 설정
```bash
# 백엔드 환경 변수 파일 생성
cd backend
cp .env.example .env

# .env 파일 편집 (데이터베이스 정보 등)
nano .env  # 또는 vim, code 등
```

### 4단계: 데이터베이스 설정
```bash
# PostgreSQL 데이터베이스 생성
createdb explainmybody

# (선택) 마이그레이션 실행
# cd backend
# alembic upgrade head
```

### 5단계: 백엔드 서버 실행
```bash
cd backend

# 개발 서버 실행 (자동 재시작)
uvicorn main:app --reload

# 또는
python main.py
```

## 📦 패키지 관리

### 새 패키지 추가
```bash
# 방법 1: uv add 명령어로 자동 추가 및 설치
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
```

### 선택적 의존성 그룹 사용
```bash
# pyproject.toml에 그룹 정의 (예시)
# [dependency-groups]
# llm = ["openai>=1.0", "anthropic>=0.18"]
# ocr-extra = ["easyocr>=1.7", "pytesseract>=0.3"]

# 특정 그룹만 설치
uv sync --group llm

# 여러 그룹 동시 설치
uv sync --group dev --group llm
```

### 패키지 업데이트
```bash
# 특정 패키지 업데이트
uv add --upgrade <package-name>

# 모든 패키지 최신 버전으로 동기화
uv sync --upgrade
```

### 설치된 패키지 확인
```bash
uv pip list

# 또는 uv tree로 의존성 트리 확인
uv tree
```

## 🔧 유용한 명령어

### 가상환경 재생성
```bash
cd /home/user/ExplainMyBody

# 기존 가상환경 삭제
rm -rf .venv

# 새로 생성
uv venv --python 3.11
source .venv/bin/activate
uv sync --group dev
```

### 의존성 동기화
```bash
# pyproject.toml 기준으로 정확히 동기화
uv sync --group dev

# 캐시 무시하고 강제 재설치
uv sync --group dev --reinstall
```

### 패키지 제거
```bash
# pyproject.toml에서 패키지 제거 후
uv sync

# 또는 uv remove 명령어 사용
uv remove <package-name>
```

## ⚡ uv의 장점

- **빠른 속도**: pip보다 10-100배 빠른 패키지 설치
- **Python 버전 관리**: 자동으로 Python 3.11 다운로드 및 설정
- **의존성 해결**: 더 정확하고 빠른 의존성 충돌 해결
- **디스크 공간 절약**: 패키지 캐싱으로 중복 다운로드 방지

## 🐛 문제 해결

### uv를 찾을 수 없는 경우
```bash
# PATH에 uv 추가
export PATH="$HOME/.cargo/bin:$PATH"

# 또는 쉘 설정 파일에 추가
echo 'export PATH="$HOME/.cargo/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### Python 3.11을 찾을 수 없는 경우
```bash
# uv가 자동으로 Python 3.11 설치
uv python install 3.11

# 또는 시스템에 설치
sudo apt update
sudo apt install python3.11 python3.11-venv python3.11-dev
```

### 패키지 설치 오류
```bash
# 캐시 삭제 후 재설치
uv cache clean
uv sync --group dev --reinstall
```

## 📂 프로젝트 구조

```
ExplainMyBody/
├── .venv/              # uv 가상환경 (여기에 생성됨!)
├── .python-version     # Python 3.11 지정
├── pyproject.toml      # 프로젝트 의존성 관리
├── backend/            # FastAPI 백엔드
│   ├── main.py
│   ├── .env           # 백엔드 환경 변수
│   └── ...
├── frontend/           # 프론트엔드 (추후)
├── OCR/                # OCR 관련 코드
└── rule_based_bodytype/ # 체형 분류 코드
```

## 📚 추가 정보

- uv 공식 문서: https://github.com/astral-sh/uv
- FastAPI 문서: https://fastapi.tiangolo.com/
- 백엔드 README: [backend/README.md](./backend/README.md)
