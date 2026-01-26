# InBody OCR Library Integration Guide

이 문서는 메인 파이프라인 개발자가 OCR 모듈을 프로젝트에 통합하는 방법을 설명합니다.

## 📦 설치 (Requirements)
이 모듈은 PaddleOCR 및 관련 라이브러리에 의존합니다.
```bash
# OCR 폴더에서 실행
uv sync
```

## 🚀 빠른 시작 (Usage)
`inbody_matcher.py`에서 `analyze_inbody` 함수를 임포트하여 사용합니다.

```python
from inbody_matcher import analyze_inbody

try:
    # 이미기 경로를 전달하면 Pydantic 모델 객체(InBodyResult)를 반환합니다.
    result = analyze_inbody("path/to/inbody_image.jpg")
    
    # 데이터 접근 예시
    print(f"체중: {result.체중관리.체중}kg")
    print(f"골격근량: {result.체중관리.골격근량}kg")
    
    # 딕셔너리로 변환이 필요한 경우
    data_dict = result.model_dump()
    
except Exception as e:
    print(f"분석 실패: {e}")
```

## 📊 데이터 구조 (Schema)
`models.py`에 정의된 `InBodyResult` 객체는 다음과 같은 계층 구조를 가집니다.

- `기본정보`: 신장, 연령, 성별
- `체성분`: 체수분, 단백질, 무기질, 체지방
- `체중관리`: 체중, 골격근량, 체지방량, 적정체중, 체중조절, 지방조절, 근육조절
- `비만분석`: BMI, 체지방률, 복부지방률, 내장지방레벨, 비만도
- `기타`: 제지방량, 기초대사량, 권장섭취열량
- `부위별근육분석`: 왼쪽팔, 오른쪽팔, 복부, 왼쪽하체, 오른쪽하체
- `부위별체지방분석`: 왼쪽팔, 오른쪽팔, 복부, 왼쪽하체, 오른쪽하체

## ⚠️ 예외 처리 (Exceptions)
`inbody_matcher.py`에서 정의된 다음 예외들을 처리할 수 있습니다.
- `ImageReadError`: 파일을 읽을 수 없거나 이미지가 손상됨
- `OCRError`: 일반적인 분석 오류
