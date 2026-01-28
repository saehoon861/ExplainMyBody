# UV 팀 프로젝트 가이드

## ✅ 해결 완료!

더 이상 경고 메시지가 나타나지 않습니다:
```bash
# ❌ 이전 (경고 발생)
warning: `VIRTUAL_ENV=/home/user/projects/ExplainMyBody/.venv` does not match the project environment path `.venv` and will be ignored

# ✅ 현재 (경고 없음)
uv run python main_workflow.py --list-users
```

---

## 📁 최종 프로젝트 구조

```
ExplainMyBody/                    # ← 팀 프로젝트 루트
├── .venv/                        # ← 단일 가상환경 (팀 전체 공유)
├── pyproject.toml                # ← 최상단에 하나만!
├── .gitignore                    # .venv 포함
├── llm/
│   ├── database.py
│   ├── workflow.py
│   ├── main_workflow.py
│   └── requirements.txt          # (선택사항, pyproject.toml과 동기화)
└── README.md
```

---

## 🚀 팀원 온보딩 (프로젝트 시작)

### 1. 프로젝트 클론
```bash
git clone <repository-url>
cd ExplainMyBody
```

### 2. uv 설치 (한 번만)
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
# 또는
pip install uv
```

### 3. 의존성 설치 (자동으로 .venv 생성)
```bash
uv sync
```

끝! ✨

---

## 💻 일상적인 사용법

### 명령어 실행

#### 방법 1: uv run 사용 (권장)
```bash
# 어느 디렉토리에서든 작동!
cd ExplainMyBody/llm
uv run python main_workflow.py --list-users

cd ExplainMyBody
uv run python llm/main_workflow.py --list-users
```

#### 방법 2: 가상환경 직접 활성화
```bash
cd ExplainMyBody
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate  # Windows

cd llm
python main_workflow.py --list-users
```

---

## 📦 의존성 관리

### 패키지 추가
```bash
# pyproject.toml에 추가 (권장)
uv add requests pandas
# 또는 수동으로 pyproject.toml 수정 후
uv sync

# 개발 의존성 추가
uv add --dev pytest black ruff
```

### 패키지 제거
```bash
uv remove requests
```

### 의존성 동기화 (다른 팀원이 패키지 추가했을 때)
```bash
git pull
uv sync  # pyproject.toml 기반으로 재동기화
```

---

## 🔒 버전 고정 (uv.lock)

uv는 자동으로 `uv.lock` 파일을 생성합니다:

```bash
ExplainMyBody/
├── pyproject.toml      # 의존성 범위 정의 (>=2.0.0)
└── uv.lock             # 정확한 버전 고정 (2.4.1)
```

### Git에 커밋할 파일
```bash
# .gitignore
.venv/          # ← 가상환경은 커밋 X
__pycache__/
*.pyc

# Git에 커밋하는 파일
pyproject.toml  # ✅ 커밋
uv.lock         # ✅ 커밋 (팀원 간 동일한 환경 보장)
```

---

## 🧪 다양한 사용 사례

### 1. 테스트 실행
```bash
# uv run으로 실행
uv run pytest llm/tests/

# 또는 의존성 추가 후
uv add --dev pytest
uv run pytest
```

### 2. 코드 포맷팅
```bash
uv add --dev black ruff
uv run black llm/
uv run ruff check llm/
```

### 3. 타입 체크
```bash
uv add --dev mypy
uv run mypy llm/
```

### 4. Jupyter Notebook
```bash
uv add jupyter
uv run jupyter notebook
```

---

## 👥 팀원 간 협업 워크플로우

### 시나리오 1: 새 패키지 추가
```bash
# 팀원 A
uv add sqlalchemy alembic
git add pyproject.toml uv.lock
git commit -m "Add SQLAlchemy and Alembic"
git push

# 팀원 B
git pull
uv sync  # ← 자동으로 동일한 버전 설치!
```

### 시나리오 2: 프로젝트 처음 시작
```bash
# 팀원 A (프로젝트 생성자)
uv init
uv add anthropic openai psycopg2-binary
git add .
git commit -m "Initial project setup"
git push

# 팀원 B, C, D (새로 합류)
git clone <repo>
cd ExplainMyBody
uv sync  # ← 한 줄로 환경 구성 완료!
```

### 시나리오 3: Python 버전 변경
```bash
# pyproject.toml 수정
requires-python = ">=3.12"

# 재동기화
uv sync
```

---

## ⚡ uv의 장점

### vs pip/venv
| 기능 | pip + venv | uv |
|------|-----------|-----|
| **속도** | 느림 | 10-100배 빠름 |
| **의존성 해결** | 느림 | 초고속 |
| **Lock 파일** | 수동 (pip freeze) | 자동 (uv.lock) |
| **설치** | Python 필요 | Rust로 작성, 독립 실행 |
| **크로스 플랫폼** | ⚠️ 수동 관리 | ✅ 자동 |

### vs poetry
| 기능 | poetry | uv |
|------|--------|-----|
| **속도** | 보통 | 10배 빠름 |
| **pyproject.toml** | ✅ | ✅ |
| **Lock 파일** | poetry.lock | uv.lock |
| **러닝 커브** | 중간 | 낮음 |

---

## 🐛 문제 해결

### Q: uv sync 시 에러 발생
```bash
# 캐시 삭제 후 재시도
uv cache clean
uv sync
```

### Q: 가상환경 위치 확인
```bash
uv run which python
# 출력: /home/user/projects/ExplainMyBody/.venv/bin/python
```

### Q: 특정 Python 버전 사용
```bash
# pyproject.toml에 명시
requires-python = ">=3.11,<3.13"

# 또는 명시적으로 지정
uv venv --python 3.11
```

### Q: 가상환경 재생성
```bash
rm -rf .venv
uv sync
```

---

## 📚 주요 명령어 치트시트

```bash
# 초기 설정
uv init                    # 새 프로젝트 초기화
uv sync                    # 의존성 설치/동기화

# 패키지 관리
uv add <package>           # 패키지 추가
uv add --dev <package>     # 개발 의존성 추가
uv remove <package>        # 패키지 제거
uv pip list                # 설치된 패키지 목록

# 실행
uv run <command>           # 가상환경에서 명령 실행
uv run python script.py    # Python 스크립트 실행

# 가상환경
uv venv                    # 가상환경 생성
source .venv/bin/activate  # 가상환경 활성화 (Linux/Mac)

# 유틸리티
uv cache clean             # 캐시 삭제
uv lock                    # Lock 파일만 업데이트
uv pip freeze              # 의존성 출력 (pip freeze 호환)
```

---

## 🎯 Best Practices

### 1. pyproject.toml은 최상단에 하나만
```
✅ Good:
ExplainMyBody/
├── pyproject.toml
└── llm/

❌ Bad:
ExplainMyBody/
├── pyproject.toml
└── llm/
    └── pyproject.toml  # ← 서브 프로젝트는 workspace 사용
```

### 2. .gitignore 설정
```gitignore
# Python
.venv/
__pycache__/
*.pyc
*.pyo
*.egg-info/

# uv
# uv.lock은 커밋 O (팀원 간 동일 버전)
```

### 3. CI/CD에서 uv 사용
```yaml
# .github/workflows/test.yml
- name: Install uv
  run: curl -LsSf https://astral.sh/uv/install.sh | sh

- name: Install dependencies
  run: uv sync

- name: Run tests
  run: uv run pytest
```

---

## 📖 추가 리소스

- [uv 공식 문서](https://docs.astral.sh/uv/)
- [pyproject.toml 스펙](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/)
- [uv GitHub](https://github.com/astral-sh/uv)

---

## ✨ 결론

**uv는 팀 프로젝트에 완벽합니다!**

- ✅ 빠른 속도
- ✅ 자동 의존성 관리
- ✅ 팀원 간 동일한 환경 보장
- ✅ 간단한 사용법

**지금 바로 사용하세요:**
```bash
uv sync
uv run python llm/main_workflow.py --list-users
```
