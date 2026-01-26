FROM python:3.11-slim

# 시스템 의존성 설치 (OpenCV, PaddleOCR 필요 라이브러리)
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# uv 설치 (고속 패키지 관리자)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# 작업 디렉토리 설정
WORKDIR /app

# 의존성 파일 복사 및 설치
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-cache

# 소스 코드 및 관련 파일 복사
COPY . .

# 환경 변수 설정 (PaddleOCR 관련)
ENV FLAGS_use_mkldnn=0
ENV FLAGS_enable_pir_api=0
ENV FLAGS_enable_executor_v2=0
ENV DISABLE_MODEL_SOURCE_CHECK=True

# 실행 명령 (스크립트 실행)
ENTRYPOINT ["uv", "run", "python", "ocr_update_2.py"]

