# ExplainMyBody - OCR Engine (Backend)

이 디렉토리는 InBody 결과지 이미지를 분석하여 구조화된 데이터를 추출하는 **OCR 엔진 및 백엔드 API**를 포함하고 있습니다.

## 🛠 OCR 시스템 상세 (How it Works)

`InBodyMatcher`는 PaddleOCR과 OpenCV를 결합하여 높은 인식률을 자랑하는 InBody 전용 OCR 파이프라인을 제공합니다.

### 1. 이미지 규격화 (Image Rectification)
- **4점 원근 변환(Perspective Transform)**: 문서의 네 꼭짓점을 검출하여 비스듬하게 찍힌 결과지 이미지를 정면으로 펼쳐줍니다.
- **미세 기울기 보정(Deskewing)**: Hough Transform을 사용하여 이미지의 수평을 0.1도 단위로 정밀하게 맞춥니다.

### 2. 적응형 이미지 전처리
- **CLAHE (Contrast Limited Adaptive Histogram Equalization)**: 명암 대비를 국부적으로 개선하여 흐릿한 글자를 선명하게 만듭니다.
- **이진화 및 노이즈 제거**: Adaptive Thresholding을 통해 배경 노이즈를 제거하고 OCR 인식 효율을 극대화합니다.

### 3. 데이터 매칭 로직 (Structured Extraction)
- **Fuzzy Matching**: `rapidfuzz` 라이브러리를 사용하여 '골격근량', '체지방량' 등 키워드의 오타나 부분 인식을 지능적으로 보정합니다.
- **공간 기반 데이터 매핑**: 
    - 인식된 키워드의 좌표(Bounding Box)를 확보합니다.
    - 해당 좌표를 기준으로 우측 또는 하단의 특정 픽셀 범위 내에 존재하는 숫자 노드를 검색합니다.
    - 가장 관련성 높은 숫자를 해당 지표의 값으로 확정합니다.

---

## 💻 환경 설정 및 설치 (Setup Guide)

백엔드 엔진 구동을 위해 다음 설정을 완료해야 합니다.

### 요구 사항
- **Python**: 3.11.x
- **System Packages**: `libgl1-mesa-glx`, `libgomp1`

### 설치 및 실행

1.  **의존성 설치**:
    ```bash
    uv sync
    ```

2.  **시스템 패키지 설치 (Linux)**:
    ```bash
    sudo apt-get install -y libgl1-mesa-glx libgomp1
    ```

3.  **API 서버 실행**:
    ```bash
    uv run uvicorn app:app --host 0.0.0.0 --port 8000 --reload
    ```

---

## 📂 주요 파일 안내

- `inbody_matcher.py`: OCR 엔진의 핵심 로직 (전처리, 원근 변환, 매칭)
- `app.py`: FastAPI 기반의 이미지 업로드 및 분석 결과 제공 API
- `pyproject.toml`: `uv` 기반의 패키지 의존성 정의
