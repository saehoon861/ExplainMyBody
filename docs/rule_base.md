# Rule-based Body Analysis 개발 문서

## 📋 프로젝트 개요

### 프로젝트 목적
인바디(InBody) 체성분 데이터를 기반으로 사용자의 체형을 **규칙 기반(Rule-based)** 방식으로 분석하는 시스템입니다. 머신러닝이나 AI 모델 없이 순수하게 의학적/생리학적 기준과 임계값을 사용하여 체형을 분류합니다.

### 주요 기능
- **3단계 체형 분류 시스템**
  - Stage 1: BMI + 체지방률 기반 1차 체형 분류
  - Stage 2: 근육량 보정을 통한 2차 체형 분류
  - Stage 3: 상하체 밸런스 분석
- **부위별 근육/체지방 분석** (왼팔, 오른팔, 몸통, 왼다리, 오른다리)
- **유연한 데이터 입력** (딕셔너리 또는 객체 형태 모두 지원)

---

## 🏗️ 시스템 아키텍처

### 전체 구조
```
Rule-based_BodyAnalysis/
├── body_analysis/        # 체성분 분석 패키지
│   ├── __init__.py       # 패키지 초기화
│   ├── models.py         # 데이터 구조 정의 (BodyCompositionData)
│   ├── constants.py      # 상수 및 임계값 정의
│   ├── metrics.py        # 기초 지표(BMI/체지방/근육) 계산
│   ├── stages.py         # Stage 1~3 체형 분석 로직
│   ├── segmental.py      # 부위별 분석 및 정규화
│   └── pipeline.py       # 통합 분석 파이프라인 (Facade)
├── main_test.py          # 메인 실행 파일
└── utils_test.py         # 결과 출력 유틸리티
```

### 디자인 패턴
- **Strategy Pattern**: 각 분류 로직을 독립적인 클래스로 분리
- **Facade Pattern**: 복잡한 분석 과정을 단일 인터페이스로 통합
- **Builder Pattern**: BodyCompositionData 클래스의 메서드 체이닝

---

## 📥 Input 데이터 형식

### 1. 딕셔너리 형태 (권장)
```python
input_data = {
    # 기본 정보
    "sex": "male",           # 성별
    "age": 25,               # 나이
    "height_cm": 175,        # 키 (cm)
    "weight_kg": 70,         # 체중 (kg)
    
    # 체성분 정보
    "bmi": 23.1,             # BMI 지수
    "fat_rate": 15.2,        # 체지방률 (%)
    "smm": 25.4,             # 골격근량 (kg)
    
    # 부위별 근육량 (kg)
    "muscle_seg": {
        "왼팔": 2.1,
        "오른팔": 2.2,
        "몸통": 10.3,
        "왼다리": 12.4,
        "오른다리": 12.5
    },
    
    # 부위별 체지방량 (kg) - 선택사항
    "fat_seg": {
        "왼팔": 1.1,
        "오른팔": 1.2,
        "몸통": 4.3,
        "왼다리": 6.4,
        "오른다리": 6.5
    }
}
```

### 2. BodyCompositionData 객체 형태
```python
from body_analysis.models import BodyCompositionData

data = BodyCompositionData()
data.set_basic_info("남성", 25, 175, 70)
data.set_composition(23.1, 15.2, 25.4)
data.set_segmental_data(muscle_seg={...}, fat_seg={...})
```

> **Note**: 딕셔너리로 입력해도 내부적으로 자동으로 `BodyCompositionData` 객체로 변환됩니다.

---

## 📤 Output 데이터 형식

### 분석 결과 구조
```python
analysis_result = {
    # Stage 1 + 2 결과 (근육 보정 완료된 최종 체형)
    "stage2": "비만형",
    # Stage 3 결과 (상하체 밸런스 분석 결과)
    "stage3": "표준형"
}
```

---

## ⚙️ 시스템 메커니즘

```
[Step 0] 입력 데이터 변환 (딕셔너리/객체 → BodyCompositionData)
    ↓
[Step 1] 신체 정보 분류 (BMI, 체지방률, 근육지표 산출)
    ↓
[Step 2] 체형 분류 및 보정 (Stage 1 & 2 통합 분석)
    ↓
[Step 3] 데이터 정규화 및 균형 분석 (Stage 3 분석)
    ↓
[Step 4] 최종 결과 반환 (stage2, stage3 결과 요약)
```

### 2. 핵심 모듈 설명

#### 📄 `models.py`
**역할**: 데이터 구조 정의
- `BodyCompositionData`: 체성분 데이터를 담는 클래스 (JSON/Dict 자동 변환 지원)

#### 📄 `constants.py`
**역할**: 분석 기준값 및 상수 정의
- `BMIThreshold`, `BodyPartLevel` 등 각종 임계값 관리

#### 📄 `metrics.py`
**역할**: 기초 신체 지표 계산 및 등급 분류
- `BMIClassifier`, `BodyFatClassifier`, `MuscleClassifier` 포함
- BMI 지수, 체지방률, 골격근량 비율을 기준표에 따라 분류

#### 📄 `stages.py`
**역할**: 상위 레벨의 체형 분석 비즈니스 로직 (Core Logic)
- **Stage 1**: BMI & 체지방률 기반 기초 분류
- **Stage 2**: 근육량 기반 체형 보정 (예: BMI가 높더라도 근육량이 많으면 비만형에서 제외)
- **Stage 3**: 상하체 및 좌우 밸런스 분석

#### 📄 `segmental.py`
**역할**: 부위별 상세 분석 및 데이터 처리
- `DataNormalizer`: 원시 데이터를 분석 가능한 표준 등급으로 정규화
- 부위별(왼팔, 오른팔, 몸통, 왼다리, 오른다리) 근육/체지방 분석 지원

#### 📄 `pipeline.py`
**역할**: 전체 분석 흐름 통합 및 오케스트레이션 (Facade)
- `BodyCompositionAnalyzer`: 모든 서브 시스템을 제어하여 `analyze_full_pipeline` 실행
- 입력 변환, 단계별 분석 호출, 예외 처리 및 결과 요약 담당

---

## 🛠️ 개발 작업 내역 (2026-01-20)

### 1. 코드 리팩토링 및 모듈화
**이전 상태**: 
- 단일 파일(`BodyAnalysis_Rule.py`)에 모든 로직이 한 줄로 작성됨
- 함수 기반 구조로 재사용성 낮음
- 예외 처리 부족

**작업 내용**:
- ✅ 전체 코드를 **3개의 모듈로 분리** (`constants.py`, `classifiers.py`, `integration.py`)
- ✅ **모든 로직을 클래스화** (Strategy Pattern 적용)
- ✅ 각 분류 전략을 독립적인 클래스로 구현
- ✅ Facade Pattern으로 복잡한 분석 과정 추상화

### 2. 예외 처리 강화
**문제점**:
- NaN 값 발생 시 프로그램 크래시
- 잘못된 데이터 입력 시 처리 불가
- 디버깅 어려움

**해결 방안**:
- ✅ 모든 분류 메서드에 `try-except` 블록 추가
- ✅ `math.isfinite()` 검사로 NaN/Inf 값 필터링
- ✅ 예외 발생 시 기본값("알 수 없음", 0.0) 반환
- ✅ 디버깅용 에러 로그 출력 추가
- ✅ 안전한 0으로 나누기 방지

### 3. 데이터 타입 유연성 개선
**문제점**:
- 딕셔너리와 객체 형태 데이터 혼용 시 오류
- `BodyCompositionData` 클래스 정의는 있으나 활용 안 됨

**해결 방안**:
- ✅ **`BodyCompositionData.from_dict()` 메서드 구현**
  - 딕셔너리 → 객체 자동 변환
  - 누락된 필드 안전하게 처리
- ✅ `integration.py`에서 입력 데이터 자동 변환
- ✅ `_get_value()` 헬퍼로 딕셔너리/객체 통합 접근
- ✅ 사용자는 원하는 형태로 데이터 입력 가능

### 4. Import 오류 수정
**문제점**:
- 파일명 대소문자 불일치 (`Constants.py` vs `constants.py`)
- 누락된 import 문
- 순환 참조 문제

**해결 방안**:
- ✅ 모든 import 문을 소문자 파일명으로 통일
- ✅ `import constants as Constants` 별칭 사용
- ✅ 필요한 모든 클래스 명시적 import
- ✅ `BodyPartLevel.NORMAL` → `Constants.BodyPartLevel.NORMAL` 수정

### 5. 코드 품질 개선
- ✅ 모든 클래스/메서드에 docstring 추가
- ✅ 타입 힌트 및 주석 보강
- ✅ 매직 넘버 제거 (상수로 정의)
- ✅ 일관된 네이밍 컨벤션 적용
- ✅ 메서드 체이닝 지원 (Builder Pattern)

---

## 🛠️ 개발 작업 내역 (2026-01-21)

### 1. 패키지 구조화 (Refactoring)
**이전 상태**: 
- 3개의 개별 파일(`constants`, `classifiers`, `integration`)에 로직이 분산됨
- 단순 파일 분리로 인한 모듈 간 의존성 혼재

**작업 내용**:
- ✅ **`body_analysis` 패키지 생성**: 파이썬 표준 패키지 구조 도입
- ✅ **모듈 세분화 및 역할 정립**:
  - `models.py`: 데이터 구조체 정의 (`BodyCompositionData`)
  - `constants.py`: 분석 상수 정의
  - `metrics.py`: BMI, 체지방 등 기초 지표 계산
  - `segmental.py`: 부위별 분석 및 정규화
  - `stages.py`: Stage 1~3 핵심 비즈니스 로직
  - `pipeline.py`: 통합 실행 Facade 클래스
- ✅ **코드 정리**: 기존 플랫 파일 삭제 및 패키지 import 구조로 변경

---

## 🛠️ 개발 작업 내역 (2026-01-22)

### 1. 분석 결과 출력 최적화
**작업 내용**:
- ✅ **Return 값 구조 변경**: 분석 파이프라인의 최종 반환 값을 핵심 체형 분석 결과로 간소화
- ✅ **필드 정리**: 최종 API 응답에는 `stage2`(최종 체형)와 `stage3`(상하체 밸런스)만 포함하도록 수정
- **변경 후 포맷**:
```json
{
    "stage2": "비만형",  # Stage 1 + 2 결과 (근육 보정 완료된 최종 체형)
    "stage3": "표준형"   # Stage 3 결과 (상하체 밸런스 분석 결과)
}
```

### 2. 파이프라인 로직 동기화
- ✅ `pipeline.py`의 `analyze_full_pipeline` 함수 내부의 Step 구분을 주석과 일치시켜 가독성 향상
- ✅ `DataNormalizer`를 통한 부위별 체지방 정규화 로직 안전성 강화 (None 체크 추가)

---

## 🧪 테스트 및 검증

### 테스트 케이스
```python
# main_test.py 실행
from body_analysis import BodyCompositionAnalyzer

analyzer = BodyCompositionAnalyzer(margin=0.10)
result = analyzer.analyze_full_pipeline(user_data)
```

### 검증 항목
- [x] 딕셔너리 입력 정상 작동
- [x] BodyCompositionData 객체 입력 정상 작동
- [x] 자동 변환 기능 동작
- [x] 예외 처리 정상 작동 (NaN, None, 잘못된 값)
- [x] 모든 Stage 분석 결과 출력
- [x] 부위별 분석 정상 작동

---

## 📊 분류 기준 요약

### BMI 분류
| BMI 범위 | 분류 |
|---------|------|
| < 18.5 | 저체중 |
| 18.5 ~ 23.0 | 정상 |
| 23.0 ~ 24.9 | 과체중 |
| 24.9 ~ 29.9 | 비만1단계 |
| 29.9 ~ 34.9 | 비만2단계 |
| ≥ 34.9 | 고도비만 |

### 체지방률 분류
| 체지방률 | 분류 |
|---------|------|
| < 10% | 표준미만 |
| 10% ~ 20% | 표준 |
| 20% ~ 24% | 과체중 |
| ≥ 24% | 비만 |

### 근육량/체중 비율
| 비율 | 근육 레벨 |
|------|----------|
| ≥ 0.55 | 근육 매우 많음 |
| ≥ 0.50 | 근육 많음 |
| ≥ 0.45 | 근육 충분 |
| ≥ 0.40 | 근육 보통 |
| < 0.40 | 근육 적음 |

---

## 🚀 사용 방법

상세한 설치 방법 및 실행 가이드는 실제 코드가 위치한 실험 디렉토리의 README를 참고하세요.

### 👉 [사용 가이드 및 Quick Start 바로가기](../experiments/Rule-based_BodyAnalysis/readme.md)

위 링크를 통해 다음 내용을 확인할 수 있습니다:
1. 테스트 코드 실행 방법 (`main_test.py`)
2. 프로젝트 적용 예시 코드
3. 주요 파일 구조 설명

---

## 📝 참고 사항

### 개발 환경
- Python 3.13
- 외부 라이브러리 의존성 없음 (순수 Python)

### 주의사항
- 모든 수치는 의학적 기준을 참고했으나, **전문적인 의료 진단을 대체할 수 없습니다**
- 임계값은 한국인 기준으로 설정되어 있습니다
- 부위별 분석은 기본 마진 10%를 사용합니다

### 기여자
- 개발자: [Your Name]
- 프로젝트: ExplainMyBody
- 날짜: 2026-01-22

---

## 📚 관련 문서
- [BodyAnalysis_Rule.py](../experiments/Rule-based_BodyAnalysis/BodyAnalysis_Rule.py) - 원본 코드
- [body_analysis package](../experiments/Rule-based_BodyAnalysis/body_analysis/) - 패키지 폴더
- [models.py](../experiments/Rule-based_BodyAnalysis/body_analysis/models.py)
- [pipeline.py](../experiments/Rule-based_BodyAnalysis/body_analysis/pipeline.py)

---

**Last Updated**: 2026-01-22  
**Version**: 1.2.0  
**Status**: ✅ Production Ready
