# Schemas - Pydantic 스키마

## 📁 파일 구조 (팀 담당 기준)

```
schemas/
├── common.py       # 공통 스키마 (User, HealthRecord)
├── llm.py          # LLM 팀 전담 (AnalysisReport, UserGoal, LLM 입출력)
├── inbody.py       # OCR 팀 전담 (InBody 데이터 검증)
└── body_type.py    # OCR 팀 전담 (체형 분석)
```

## 🎯 설계 원칙

**팀 담당 기준 분리로 Merge Conflict 최소화**
- 각 팀원이 서로 다른 파일을 작업하여 동시 작업 시 충돌 방지
- 도메인 응집도를 유지하면서 협업 효율성 극대화

## 📦 파일별 상세

### `common.py` - 공통 스키마
**담당**: 양 팀 공통 사용  
**내용**:
- **User**: UserCreate, UserLogin, UserResponse
- **HealthRecord**: HealthRecordCreate, HealthRecordUpdate, HealthRecordResponse

**특징**: 안정적이며 변경 빈도가 낮음

---

### `llm.py` - LLM 팀 전담
**담당**: LLM 팀원  
**내용**:
- **AnalysisReport**: AnalysisReportCreate, AnalysisReportResponse
- **UserGoal**: UserGoalCreate, UserGoalUpdate, UserGoalResponse
- **LLM 상태 분석 (LLM1)**: StatusAnalysisInput, StatusAnalysisResponse
- **LLM 주간 계획 (LLM2)**: GoalPlanInput, GoalPlanResponse, GoalPlanRequest

**특징**: LLM 관련 모든 입출력 스키마 통합 관리

---

### `inbody.py` - OCR 팀 전담
**담당**: OCR 팀원  
**내용**:
- **InBodyData**: OCR 추출 데이터 전체 검증 모델
- 중첩된 Pydantic 모델 (BasicInfo, BodyComposition, WeightManagement 등)
- 복잡한 필드 검증 로직 및 null 값 체크

**특징**: 7500 bytes의 복잡한 검증 로직 포함

---

### `body_type.py` - OCR 팀 전담
**담당**: OCR 팀원  
**내용**:
- **BodyTypeAnalysisInput**: InBodyData에서 체형 분석 필요 필드 추출
- **BodyTypeAnalysisOutput**: 체형 분석 결과 (stage2, stage3)
- InBodyData → BodyTypeAnalysisInput 변환 로직

**특징**: InBody 데이터와 강하게 결합된 도메인 로직

---

## 🤝 협업 가이드

### Merge Conflict 방지
- **OCR 팀원**: `inbody.py`, `body_type.py` 작업
- **LLM 팀원**: `llm.py` 작업
- **공통 수정 필요 시**: `common.py` (사전 협의 필요)

### Import 방법
```python
# 공통 스키마
from schemas.common import UserCreate, HealthRecordCreate

# LLM 팀 스키마
from schemas.llm import AnalysisReportCreate, StatusAnalysisInput

# OCR 팀 스키마
from schemas.inbody import InBodyData
from schemas.body_type import BodyTypeAnalysisInput
```

### 스키마 vs 모델
- **스키마 (Pydantic)**: API 입출력 검증, 데이터 변환
- **모델 (SQLAlchemy)**: 데이터베이스 테이블 매핑
- 스키마는 모델과 독립적으로 설계 가능 (느슨한 결합)