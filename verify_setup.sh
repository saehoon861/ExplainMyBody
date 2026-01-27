#!/bin/bash
# UV 환경 검증 스크립트 (최상위 디렉토리용)

set -e

echo "🔍 UV 환경 검증 시작..."
echo ""

# 1. uv 설치 확인
echo "1️⃣  uv 설치 확인..."
if command -v uv &> /dev/null; then
    echo "✅ uv 설치됨: $(uv --version)"
else
    echo "❌ uv가 설치되어 있지 않습니다."
    echo "   설치: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi
echo ""

# 2. Python 버전 확인
echo "2️⃣  Python 버전 확인..."
if [ -f ".python-version" ]; then
    REQUIRED_VERSION=$(cat .python-version)
    echo "✅ .python-version 파일 존재: Python $REQUIRED_VERSION"
else
    echo "⚠️  .python-version 파일이 없습니다."
fi
echo ""

# 3. 가상환경 확인
echo "3️⃣  가상환경 확인..."
if [ -d ".venv" ]; then
    echo "✅ .venv 디렉토리 존재"
    if [ -n "$VIRTUAL_ENV" ]; then
        echo "✅ 가상환경 활성화됨: $VIRTUAL_ENV"
        PYTHON_VERSION=$(python --version 2>&1)
        echo "   Python 버전: $PYTHON_VERSION"
    else
        echo "⚠️  가상환경이 활성화되지 않았습니다."
        echo "   실행: source .venv/bin/activate"
    fi
else
    echo "❌ .venv 디렉토리가 없습니다."
    echo "   생성: uv venv --python 3.11"
    exit 1
fi
echo ""

# 4. pyproject.toml 확인
echo "4️⃣  pyproject.toml 확인..."
if [ -f "pyproject.toml" ]; then
    echo "✅ pyproject.toml 존재"
else
    echo "❌ pyproject.toml이 없습니다."
    exit 1
fi
echo ""

# 5. 패키지 설치 확인 (가상환경이 활성화된 경우만)
if [ -n "$VIRTUAL_ENV" ]; then
    echo "5️⃣  주요 패키지 설치 확인..."
    
    PACKAGES=("fastapi" "uvicorn" "sqlalchemy" "pydantic" "paddleocr")
    ALL_INSTALLED=true
    
    for pkg in "${PACKAGES[@]}"; do
        if python -c "import $pkg" 2>/dev/null; then
            echo "✅ $pkg 설치됨"
        else
            echo "❌ $pkg 미설치"
            ALL_INSTALLED=false
        fi
    done
    
    if [ "$ALL_INSTALLED" = false ]; then
        echo ""
        echo "⚠️  일부 패키지가 설치되지 않았습니다."
        echo "   설치: uv sync --group dev"
    fi
else
    echo "5️⃣  패키지 확인 건너뜀 (가상환경 비활성화)"
fi
echo ""

# 6. 환경 변수 파일 확인
echo "6️⃣ 환경 변수 파일 확인..."
if [ -f ".env" ]; then
    echo "✅ .env 파일 존재"
elif [ -f ".env.example" ]; then
    echo "⚠️  .env 파일이 없습니다. .env.example을 복사하세요."
    echo "   실행: cp .env.example .env"
else
    echo "❌ .env.example 파일도 없습니다."
fi
echo ""

# 최종 결과
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✨ 검증 완료!"
echo ""
echo "📝 다음 단계:"
if [ ! -d ".venv" ]; then
    echo "   1. uv venv --python 3.11"
fi
if [ -z "$VIRTUAL_ENV" ]; then
    echo "   2. source .venv/bin/activate"
fi
if [ "$ALL_INSTALLED" = false ] || [ -z "$VIRTUAL_ENV" ]; then
    echo "   3. uv pip sync --extra dev"
fi
if [ ! -f "backend/.env" ]; then
    echo "   4. cp backend/.env.example backend/.env"
fi
echo "   5. cd backend && uvicorn main:app --reload"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
